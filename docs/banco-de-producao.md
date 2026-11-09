# Banco de produção (PostgreSQL)

Em produção usamos **PostgreSQL 17**: aguenta muitos acessos simultâneos, tem
travamento por linha (`FOR UPDATE`), tipos de dados reais (`numeric`, `date`) e
ferramentas de backup.

## Como a aplicação escolhe o banco

Em `config/settings.py`:

```mermaid
flowchart TD
    A["settings.py lê DB_ENGINE"] --> B{"valor?"}
    B -->|"sqlite (padrão)"| C["django.db.backends.sqlite3<br/>arquivo SQLITE_PATH ou db.sqlite3"]
    B -->|postgres| D["django.db.backends.postgresql<br/>POSTGRES_DB / USER / PASSWORD / HOST / PORT"]
    B -->|outro| E["RuntimeError<br/>(falha logo ao iniciar)"]
```

No PostgreSQL também estão ligados:
- `CONN_MAX_AGE = 60`: reaproveita a conexão por até 60 s, em vez de abrir uma nova a cada requisição;
- `CONN_HEALTH_CHECKS = True`: antes de reaproveitar, confere se a conexão ainda está viva.

## Variáveis de ambiente

| Variável | Exemplo | Obrigatória em produção | Descrição |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | (string longa e aleatória) | **sim** | Chave de criptografia do Django. Sem ela e com `DEBUG=0`, a aplicação não sobe |
| `DJANGO_DEBUG` | `0` | sim | `1` só em desenvolvimento. O padrão é `0` (seguro) |
| `DJANGO_ALLOWED_HOSTS` | `api.easycar.com.br` | sim | Domínios aceitos, separados por vírgula |
| `DB_ENGINE` | `postgres` | sim | `sqlite` ou `postgres` |
| `POSTGRES_DB` | `easycar` | sim | Nome do banco |
| `POSTGRES_USER` | `easycar` | sim | Usuário do banco |
| `POSTGRES_PASSWORD` | (segredo) | **sim** | Senha do banco |
| `POSTGRES_HOST` | `db` / IP / host gerenciado | sim | Endereço do servidor |
| `POSTGRES_PORT` | `5432` | não | Porta (padrão 5432) |
| `SQLITE_PATH` | `db.sqlite3` | não | Só quando `DB_ENGINE=sqlite` |

Para gerar uma `DJANGO_SECRET_KEY`:
```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

> Nunca coloque senhas reais no Git. O `.env` está no `.gitignore`. No servidor,
> use as variáveis/segredos da hospedagem.

## Modelo de dados

```mermaid
erDiagram
    auth_user ||--o| locadora_perfilcliente : "tem perfil (1:1)"
    auth_user ||--o{ locadora_aluguel : "registra (funcionário)"
    auth_user ||--o{ locadora_multa : "registra (funcionário)"
    locadora_perfilcliente ||--o{ locadora_aluguel : "aluga"
    locadora_carro ||--o{ locadora_aluguel : "é alugado"
    locadora_aluguel ||--o{ locadora_multa : "gera"

    auth_user {
        bigint id PK
        varchar username UK
        varchar first_name
        varchar last_name
        varchar email
    }
    locadora_perfilcliente {
        bigint id PK
        int user_id FK,UK
        varchar_11 cnh UK
        varchar_20 telefone
        varchar_255 endereco
    }
    locadora_carro {
        bigint id PK
        varchar_50 marca
        varchar_100 modelo
        varchar_7 placa UK
        smallint ano
        varchar_12 status "disponivel / alugado / manutencao"
    }
    locadora_aluguel {
        bigint id PK
        bigint perfil_cliente_id FK
        bigint carro_id FK
        int funcionario_id FK
        date data_inicio
        date data_fim "CHECK >= data_inicio"
        numeric_10_2 valor "CHECK > 0"
        varchar_10 status "ativo / finalizado"
        date data_devolucao "nulo enquanto ativo"
    }
    locadora_multa {
        bigint id PK
        bigint aluguel_id FK
        int funcionario_id FK
        int dias_atrasos
        numeric_10_2 valor
        varchar_10 status "pendente / pago / abonado"
        date data_infracao
        date data_pagamento "nulo enquanto pendente"
        text motivo
    }
```

Relações:
- **1:1**: `auth_user` ↔ `locadora_perfilcliente` (um usuário cliente tem um perfil).
- **1:N**: funcionário → aluguéis; funcionário → multas; aluguel → multas.
- **N:N**: cliente ↔ carro, usando `locadora_aluguel` como tabela intermediária.

### Regras garantidas pelo próprio banco

| Regra | Onde |
|---|---|
| Placa única | `UNIQUE (placa)` em `locadora_carro` |
| CNH única | `UNIQUE (cnh)` em `locadora_perfilcliente` |
| Um perfil por usuário | `UNIQUE (user_id)` em `locadora_perfilcliente` |
| Fim do aluguel ≥ início | `CHECK aluguel_fim_depois_do_inicio` |
| Valor do aluguel > 0 | `CHECK aluguel_valor_positivo` |
| Chaves estrangeiras válidas | `FOREIGN KEY ... DEFERRABLE INITIALLY DEFERRED` |

> ⚠️ O `on_delete=PROTECT`/`CASCADE` dos models é aplicado pelo **Django em Python**,
> não pelo banco. Com SQL puro, um `DELETE` de um carro com aluguéis só falha no
> `COMMIT`. Por isso os repositórios têm `tem_alugueis()`/`tem_multas()`: o service
> deve consultar antes de excluir.

Para ver o SQL exato que cria as tabelas no PostgreSQL:
```bash
DB_ENGINE=postgres python manage.py sqlmigrate locadora 0001
```

## Ciclo de vida dos status

```mermaid
stateDiagram-v2
    direction LR
    state "Carro" as C {
        [*] --> disponivel
        disponivel --> alugado: registrar aluguel
        alugado --> disponivel: devolver / multar
        disponivel --> manutencao
        manutencao --> disponivel
    }
```

```mermaid
stateDiagram-v2
    direction LR
    state "Aluguel" as A {
        [*] --> ativo
        ativo --> finalizado: devolução (finalizar)
    }
    state "Multa" as M {
        [*] --> pendente
        pendente --> pago: registrar_pagamento
        pendente --> abonado: abonar
    }
```

Os `UPDATE` de mudança de status têm a condição do estado atual no `WHERE`
(ex.: `... WHERE id = %s AND status = 'ativo'`). Se duas pessoas tentarem
finalizar o mesmo aluguel ao mesmo tempo, só uma consegue (`rowcount = 1`) e a
outra recebe `0`.

## Concorrência: alugar o mesmo carro ao mesmo tempo

Sem trava, dois funcionários poderiam alugar o mesmo carro no mesmo instante. Com
`transaction.atomic()` + `buscar_por_id(..., bloquear=True)` (que gera `FOR UPDATE`):

```mermaid
sequenceDiagram
    participant F1 as Funcionário 1
    participant F2 as Funcionário 2
    participant PG as PostgreSQL
    F1->>PG: BEGIN
    F1->>PG: SELECT ... FROM locadora_carro WHERE id=7 FOR UPDATE
    PG-->>F1: status = disponivel (linha TRAVADA)
    F2->>PG: BEGIN
    F2->>PG: SELECT ... WHERE id=7 FOR UPDATE
    Note over F2,PG: F2 fica esperando a trava
    F1->>PG: INSERT locadora_aluguel ...
    F1->>PG: UPDATE locadora_carro SET status='alugado'
    F1->>PG: COMMIT (libera a trava)
    PG-->>F2: status = alugado
    F2->>F2: RegraDeNegocio → HTTP 409
    F2->>PG: ROLLBACK
```

Exemplo de service usando os repositórios:

```python
from django.db import transaction
from locadora.repositories import alugueis, carros


@transaction.atomic
def registrar_aluguel(perfil_id: int, carro_id: int, funcionario_id: int,
                      inicio: date, fim: date, valor: Decimal) -> AluguelLinha:
    carro = carros.buscar_por_id(carro_id, bloquear=True)
    if carro is None:
        raise RegraDeNegocio('Carro não encontrado.')
    if carro['status'] != 'disponivel':
        raise RegraDeNegocio(f"O carro {carro['placa']} não está disponível.")
    aluguel = alugueis.criar(perfil_id, carro_id, funcionario_id, inicio, fim, valor)
    carros.atualizar_status(carro_id, 'alugado')
    return aluguel
```

## Arquitetura de produção sugerida

```mermaid
flowchart LR
    U["Usuários"] -->|HTTPS| P["Proxy / HTTPS<br/>(da hospedagem ou nginx)"]
    P -->|HTTP :8000| A["Container da API<br/>gunicorn (3 workers)"]
    A -->|"5432 (rede privada)"| D[("PostgreSQL 17<br/>gerenciado ou container")]
    D --> B[("Backups diários")]
    CI["GitHub Actions"] -->|imagem| R["GHCR<br/>ghcr.io/.../easycar"]
    R -->|docker pull| A
```

- O PostgreSQL **não** deve ficar exposto na internet: só a API acessa.
- O HTTPS fica no proxy/hospedagem. Depois de ativado, ligue no `settings.py`:
  `SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` e
  `SECURE_SSL_REDIRECT` (o `manage.py check --deploy` lista o que falta).

## Backup e restauração

```bash
# Backup (formato compactado)
docker compose exec db pg_dump -U easycar -d easycar -Fc > backup_$(date +%F).dump

# Restaurar
docker compose exec -T db pg_restore -U easycar -d easycar --clean < backup_2026-11-09.dump
```

## Checklist de deploy

- [ ] `DJANGO_DEBUG=0`
- [ ] `DJANGO_SECRET_KEY` nova e secreta
- [ ] `DJANGO_ALLOWED_HOSTS` com o domínio real
- [ ] Senha forte em `POSTGRES_PASSWORD`
- [ ] Banco acessível só pela API (rede privada)
- [ ] HTTPS ativo + configurações `SECURE_*`
- [ ] Backup automático configurado
- [ ] `python manage.py check --deploy` sem avisos
- [ ] `python manage.py createsuperuser` para o primeiro admin
- [ ] Grupos `Funcionários` e `Clientes` criados no admin
