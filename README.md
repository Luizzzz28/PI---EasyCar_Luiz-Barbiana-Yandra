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

## Créditos

Projeto Integrador desenvolvido por Luiz, Barbiana e Yandra.
Camada de banco de dados, Docker, CI/CD e documentação com orientação do **Prof. Henry**.
