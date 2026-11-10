# PI---EasyCar_Luiz-Barbiana-Yandra

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