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

## Dashboard integrado

O dashboard e a API usam o mesmo projeto Django, os modelos de [`locadora/models.py`](./locadora/models.py) e o mesmo banco configurado em `config/settings.py`. As páginas reaproveitam os templates e arquivos estáticos em `dashboard_locadora/core/`, mas não usam mais o banco isolado daquela pasta.

- Painel da equipe: `/` (login de funcionário)
- Frota: `/carros/` (dados consultados no banco principal)
- Cadastro de veículo: `/carros/novo/` (funcionários; inclui chassi, placa, ano e diária)
- Clientes: `/clientes/` (funcionários; cria usuário e perfil com CNH, telefone e endereço)
- Novo aluguel: `/alugueis/novo/` (registra pela camada de serviços da API e atualiza o status do carro)
- Taxas: `/taxas-atraso/`
- API e documentação: `/api/` e `/api/docs/`
- Administração: `/admin/`

Para executar no Windows, na raiz deste repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Use um superusuário ou adicione um usuário ao grupo `Funcionários` para acessar o painel, cadastrar clientes e veículos e registrar aluguéis. Para cadastrar um cliente, o painel cria um usuário no grupo `Clientes` e seu perfil no mesmo banco.

O campo `chassi` é validado com 17 caracteres e é mostrado apenas para funcionários na API. Placa, ano, diária e status continuam compartilhados entre as páginas e os endpoints.

## Compartilhar a aplicação

O arquivo [`render.yaml`](./render.yaml) configura um serviço web e um PostgreSQL gratuitos no Render. **O banco gratuito expira após 30 dias e seus dados são apagados**; use-o apenas para demonstração/testes. Para manter dados por mais tempo, migre para um plano pago ou outro provedor PostgreSQL persistente e atualize a referência de `DATABASE_URL`.

1. Envie as alterações para o GitHub e conecte o repositório a um Blueprint no Render. Se usar a URL pública do repositório, novos commits não iniciam deploy automaticamente; conecte o GitHub nas configurações do Render ou use **Manual Deploy**.
2. O Blueprint cria o PostgreSQL, conecta sua URL interna à variável `DATABASE_URL` e gera `DJANGO_SECRET_KEY`.
3. As migrações são aplicadas ao iniciar o serviço.
4. Como o plano gratuito não oferece Shell, crie o primeiro superusuário no seu computador. Use a URL externa exibida em **Connect** no painel do banco (não a URL interna usada pelo serviço) e o `DJANGO_SECRET_KEY` exibido no serviço. No PowerShell, na raiz do projeto, defina `DATABASE_URL`, `DJANGO_SECRET_KEY`, `DB_ENGINE=postgres` e `DJANGO_DEBUG=false`, e execute `.\.venv\Scripts\python.exe manage.py createsuperuser`. Não salve esses valores no repositório.
5. Compartilhe o endereço `https://...onrender.com` com a equipe. O painel e clientes exigem login; a frota e as taxas podem ser consultadas publicamente.

O serviço web gratuito pode dormir quando não houver acesso e demorar para responder à primeira visita. Confira os limites e a política de retenção do Render antes de cadastrar dados reais.

## Créditos

Projeto Integrador desenvolvido por Luiz, Barbiana e Yandra.
Camada de banco de dados, Docker, CI/CD e documentação feitas com orientação e ajuda do
**Prof. Henry**, Tech Lead da **Brassol Distribuidora**.

As referências bibliográficas de tudo o que foi usado estão em [`docs/referencias.md`](docs/referencias.md).
