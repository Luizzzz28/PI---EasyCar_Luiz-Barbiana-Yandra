# 🚗 Dashboard e API da Locadora de Veículos

Projeto acadêmico de Desenvolvimento de Sistemas: um dashboard interativo para uma locadora de veículos, com os valores dos aluguéis e a tabela de taxas de atraso na entrega, mais uma API REST para cadastro de clientes.

Feito com **Django** e **Django REST Framework**.

## Funcionalidades

**Dashboard** (`/`)
- Cards com receita dos aluguéis, total de multas, total geral e quantidade de aluguéis/atrasados
- Filtro por categoria de veículo
- Gráfico de barras com a receita por categoria
- Tabela de aluguéis com valor, horas de atraso e multa
- Tabela de taxas de atraso por faixa e por categoria
- Simulador de multa
- Tema claro/escuro automático e layout responsivo
- Fotos locais de carros modernos e layout responsivo para celular

**Clientes** (`/clientes/`)
- Formulário autenticado para cadastrar nome, CPF e telefone
- Validação de CPF/telefone e normalização de dados com ou sem máscara
- Busca de clientes cadastrados

**Carros disponíveis** (`/carros/`)
- Catálogo demonstrativo de 20 modelos com foto local e diária de referência
- Atalho para registrar o aluguel de um modelo escolhido para um cliente cadastrado
- Créditos e licenças de cada imagem exibidos nos próprios cartões

**Aluguéis**
- Registro autenticado a partir do catálogo em `/alugueis/novo/`
- Seleção de cliente cadastrado, modelo e quantidade de diárias
- Valor da diária escolhido preservado no aluguel

**Taxas de atraso** (`/taxas-atraso/`)
- Tabela das faixas de atraso e dos valores de multa
- Calculadora de devolução por modelo de carro e horas de atraso
- Tabela de diária, taxa por hora e multa diária dos 20 modelos

**API REST** (`/api/`)
- CRUD de clientes (nome, CPF e telefone), categorias e aluguéis
- Consulta da tabela de taxas de atraso em `/api/taxas-atraso/`
- Validação de CPF (dígitos verificadores) e de telefone (DDD + número)
- Bloqueio de CPF duplicado
- Aceita CPF e telefone com ou sem máscara
- Busca de clientes por nome ou CPF
- Acesso protegido por login

## Tecnologias

- Python 3
- Django
- Django REST Framework
- SQLite (banco padrão de desenvolvimento) ou PostgreSQL em produção
- Gunicorn e WhiteNoise para hospedagem
- HTML, CSS e JavaScript puros no dashboard

## Estrutura do projeto

```
locadora_django/
├── manage.py
├── requirements.txt
├── locadora/                  # configurações do projeto
│   ├── settings.py
│   └── urls.py
└── core/                      # aplicação principal
    ├── models.py              # Categoria, Cliente, Aluguel
    ├── validators.py          # validação de CPF e telefone
    ├── serializers.py         # serializers da API
    ├── api.py                 # viewsets da API
    ├── views.py               # view do dashboard
    ├── urls.py                # rotas (dashboard e API)
    ├── admin.py
    ├── tests.py               # testes da API e do cadastro pela interface
    ├── catalogo.py            # modelos e diárias de referência
    ├── templates/
    │   └── core/
    │       ├── dashboard.html
    │       ├── clientes.html   # cadastro e consulta de clientes
    │       ├── carros.html     # catálogo de carros
    │       ├── novo_aluguel.html # registro de aluguéis
    │       └── taxas_atraso.html # tabela e calculadora de multas
    ├── static/
    │   └── core/
    │       ├── css/dashboard.css  # estilos editáveis
    │       ├── js/dashboard.js    # simulador
    │       ├── js/taxas_atraso.js # calculadora de multas
    │       └── img/
    │           ├── car-photo-main.jpg       # foto do banner
    │           ├── car-photo-fleet.jpg      # foto da frota
    │           └── cars/                    # fotos e créditos do catálogo
    └── management/commands/seed.py   # dados fictícios de exemplo
```

## Como rodar

Pré-requisito: Python 3.10 ou superior.

```bash
# 1. Criar e ativar o ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Criar o banco de dados
python manage.py migrate

# 4. Criar um usuário (necessário para usar a API)
python manage.py createsuperuser

# 5. (Opcional) Carregar dados fictícios de exemplo
python manage.py seed

# 6. Iniciar o servidor
python manage.py runserver
```

Endereços:

| O quê | URL |
|---|---|
| Dashboard | http://127.0.0.1:8000/ |
| Carros disponíveis | http://127.0.0.1:8000/carros/ |
| Registrar aluguel | http://127.0.0.1:8000/alugueis/novo/ |
| Clientes | http://127.0.0.1:8000/clientes/ |
| Tabela e calculadora de taxas | http://127.0.0.1:8000/taxas-atraso/ |
| API navegável | http://127.0.0.1:8000/api/ |
| Login da API | http://127.0.0.1:8000/api-auth/login/ |
| Admin | http://127.0.0.1:8000/admin/ |

No VS Code, escolha o interpretador da `.venv` (Ctrl+Shift+P > *Python: Select Interpreter*).

O visual do painel e do catálogo pode ser personalizado em `core/static/core/css/dashboard.css`. A estrutura fica em `core/templates/core/`, e os modelos e valores diários de referência podem ser alterados em `core/catalogo.py`. O catálogo é demonstrativo: disponibilidade e preço final devem ser confirmados com a locadora. As fotos do Unsplash e do Wikimedia Commons estão salvas localmente; os cartões do catálogo apontam para as páginas originais e informam seus autores e licenças.

A calculadora de atraso usa as mesmas faixas de multa de `core/models.py`: até 1 hora não há cobrança; de 1 a 3 horas são cobrados 10% da diária por hora; acima de 3 horas, cobra-se 110% da diária por cada dia ou fração. O endpoint JSON autenticado permanece em `/api/taxas-atraso/`.

## Endpoints da API

| Recurso | Rota | Métodos |
|---|---|---|
| Clientes | `/api/clientes/` | GET, POST, PUT, PATCH, DELETE |
| Categorias | `/api/categorias/` | GET, POST, PUT, PATCH, DELETE |
| Aluguéis | `/api/alugueis/` | GET, POST, PUT, PATCH, DELETE |
| Tabela e calculadora de taxas | `/taxas-atraso/` | Página web |
| Dados das taxas (API JSON) | `/api/taxas-atraso/` | GET |

Buscar cliente por nome ou CPF: `/api/clientes/?search=maria`

Para cadastrar clientes pela API navegável, entre em `/api/clientes/` autenticado e use o formulário `POST` da página. A tabela de taxas retorna as faixas e os valores calculados para cada categoria.

Para personalizar o dashboard, edite `core/static/core/css/dashboard.css` (visual), `core/static/core/js/dashboard.js` (simulador) e `core/templates/core/dashboard.html` (estrutura da página).

A aba **Clientes** oferece cadastro e busca pela interface do navegador; o endpoint REST continua disponível em `/api/clientes/`. As fotos do banner foram baixadas do Unsplash para `core/static/core/img/`, evitando requisições de imagens externas durante o uso.

### Exemplo: cadastrar um cliente

```bash
curl -u USUARIO:SENHA -X POST http://127.0.0.1:8000/api/clientes/ \
  -H "Content-Type: application/json" \
  -d '{"nome": "Maria Silva", "cpf": "390.533.447-05", "telefone": "(61) 99999-1234"}'
```

Resposta (201 Created):

```json
{
  "id": 1,
  "nome": "Maria Silva",
  "cpf": "390.533.447-05",
  "telefone": "(61) 99999-1234",
  "criado_em": "2026-11-10T10:00:00-03:00"
}
```

### Regras de validação dos clientes

- **Nome:** precisa ter nome e sobrenome
- **CPF:** 11 dígitos, dígitos verificadores corretos, sem repetição de cadastro
- **Telefone:** DDD + número (10 ou 11 dígitos); se tiver 11, o número começa com 9
- Erros retornam status `400` com a mensagem do campo

## Regras de multa por atraso

| Atraso | Cobrança |
|---|---|
| Até 1 hora | Tolerância, sem multa |
| De 1h até 3h | 10% da diária por hora de atraso |
| Acima de 3h | 1 diária + 10%, por dia (ou fração) de atraso |

Essas regras são exemplos fictícios. Para ajustá-las, edite as constantes no topo de `core/models.py` e a propriedade `multa` de `Aluguel`. O simulador do dashboard repete a regra em JavaScript no final de `dashboard.html`, então altere nos dois lugares.

## Testes

```bash
python manage.py test
```

Os testes cobrem o cadastro de cliente com máscara, CPF inválido, CPF duplicado e exigência de login.

## Dados pessoais e segurança (LGPD)

CPF e telefone são dados pessoais. Neste projeto:

- A API exige autenticação
- O `.gitignore` exclui o `db.sqlite3`, para o banco não ir para o repositório
- O comando `seed` usa CPFs **fictícios** (válidos só matematicamente). Use-os em testes e apresentações

## Publicar em um servidor

O projeto está configurado para executar em um servidor WSGI, servir arquivos estáticos com WhiteNoise e usar PostgreSQL por `DATABASE_URL`. Não use o servidor `runserver` em produção.

Configure estas variáveis no provedor de hospedagem:

| Variável | Exemplo/uso |
|---|---|
| `DJANGO_SECRET_KEY` | Chave aleatória e privada; gere com `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | Domínios permitidos, separados por vírgula, sem `https://` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Origens HTTPS do site, separadas por vírgula |
| `DATABASE_URL` | URL de conexão PostgreSQL fornecida pelo provedor |
| `DJANGO_USE_X_FORWARDED_PROTO` | `True` se o proxy HTTPS do provedor encaminhar `X-Forwarded-Proto` |

Com as variáveis configuradas, execute durante a publicação:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Inicie o servidor de aplicação em Linux com:

```bash
gunicorn locadora.wsgi:application --bind 0.0.0.0:$PORT
```

O `PORT` deve ser fornecido pelo provedor. Antes de abrir o site ao público, confirme que HTTPS está ativo, que o banco persistente foi configurado e que o usuário administrador tem uma senha forte. A senha local de demonstração `admin/admin` não deve ser usada em produção. Para validar as configurações de segurança depois de definir as variáveis do servidor, execute `python manage.py check --deploy`.

O `check --deploy` pode recomendar HSTS para subdomínios e inclusão na lista de preload. Essas opções não são ativadas automaticamente: habilite-as somente depois de confirmar que todos os subdomínios também usam HTTPS e que deseja o comportamento permanente de preload.

## Melhorias futuras

- Autenticação por token (JWT)
- Registro de devolução do veículo com cálculo automático das horas de atraso

## Autor

Projeto desenvolvido para a disciplina de Desenvolvimento de Sistemas.
Autor: yandra ketlen aquino
