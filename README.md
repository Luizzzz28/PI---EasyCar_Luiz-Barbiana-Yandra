# PI - EasyCar (Luiz, Barbiana e Yandra)

API REST de uma locadora de carros: clientes, carros, aluguéis e multas, com acesso
por grupos (Funcionários e Clientes). Feita com Django + Django REST Framework.

## Banco de dados

- **SQLite** para desenvolvimento e testes automatizados
- **PostgreSQL 17** para produção (via Docker)
- Acesso a dados com o **ORM do Django** (`locadora/models.py`); regras de negócio com transação em `locadora/services.py`

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
cp .env.example .env               # Windows: Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver         # http://localhost:8000/api/  |  docs: /api/docs/
pytest                             # testes
docker compose up --build          # API + PostgreSQL, igual à produção
```

## Documentação

Toda a documentação está na pasta [`docs/`](docs/README.md):
Docker, banco de testes, banco de produção, CI/CD, padrões de código e pendências.

## Dashboard da locadora

O dashboard e a API acadêmica da locadora estão no projeto independente [`dashboard_locadora/`](./dashboard_locadora/). Ele foi adicionado em uma pasta própria para preservar a API existente deste repositório, que permanece na raiz.

Para executar no Windows:

```powershell
cd dashboard_locadora
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Endereços do dashboard:

- Painel: `http://127.0.0.1:8000/`
- Carros disponíveis: `http://127.0.0.1:8000/carros/`
- Cadastro de clientes: `http://127.0.0.1:8000/clientes/`
- Tabela e calculadora de atraso: `http://127.0.0.1:8000/taxas-atraso/`
- API REST do dashboard: `http://127.0.0.1:8000/api/`

Consulte [`dashboard_locadora/README.md`](./dashboard_locadora/README.md) para detalhes de endpoints, validações e funcionamento.

## Publicar no Render

Este repositório inclui um Blueprint em [`render.yaml`](./render.yaml) para publicar o dashboard em `dashboard_locadora/` sem substituir a API que fica na raiz. O Blueprint provisiona o serviço web e um PostgreSQL no Ohio, na mesma região, e aplica migrações no deploy.

1. Envie este repositório ao GitHub e acesse o [Render Dashboard](https://dashboard.render.com/).
2. Crie um Blueprint e conecte este repositório, selecionando `render.yaml`.
3. Revise e confirme o plano e a cobrança mostrados pelo Render. O Blueprint usa o plano pago `starter` para o serviço e `basic-1gb` para o PostgreSQL, pois os bancos gratuitos do Render expiram após 30 dias.
4. Após o primeiro deploy, crie um usuário administrador pelo Shell do serviço: `cd dashboard_locadora && python manage.py createsuperuser`.
5. O Render atribui um endereço `onrender.com` ao serviço e configura HTTPS. A aplicação aceita automaticamente esse hostname.

O domínio `onrender.com` é o endereço público atribuído pelo provedor, não um domínio próprio registrado. Para usar um domínio comprado por você, adicione-o em **Settings > Custom Domains** no Render, configure os registros DNS indicados pelo painel e adicione o hostname a `DJANGO_ALLOWED_HOSTS` e a origem `https://seu-dominio` a `DJANGO_CSRF_TRUSTED_ORIGINS`.

Nenhum serviço foi provisionado por este repositório; criar o Blueprint no Render requer uma conta e confirmação explícita dos custos.

## Créditos

Projeto Integrador desenvolvido por Luiz, Barbiana e Yandra.
Camada de banco de dados, Docker, CI/CD e documentação feitas com orientação e ajuda do
**Prof. Henry**, Tech Lead da **Brassol Distribuidora**.

As referências bibliográficas de tudo o que foi usado estão em [`docs/referencias.md`](docs/referencias.md).
