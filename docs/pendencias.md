# Pendências

## Banco de dados (escopo desta branch)

| # | Pendência | Prioridade |
|---|---|---|
| 1 | Criar uma rota na API para registrar multa usando `services.registrar_multa` (hoje o `MultaViewSet` grava direto, sem finalizar o aluguel nem liberar o carro) | alta |
| 2 | Comando de *seed* (`python manage.py popular_banco`) com carros/clientes de exemplo para a apresentação. A pasta `locadora/management/commands/` já existe e está vazia | média |
| 3 | Adicionar as novas variáveis (`DB_ENGINE`, `POSTGRES_*`, `DJANGO_ALLOWED_HOSTS`) no `.env.example` | baixa |
| 4 | Configurar backup automático no servidor de produção | quando houver servidor |

## Encontrado em outras partes do código (avisar o time)

| # | Arquivo | Problema | Situação |
|---|---|---|---|
| 1 | `serializers.py` (`MultaSerializer`) | Usava `descricao` em vez de `motivo` | ✅ corrigido nesta branch |
| 2 | `services.py` (`registrar_multa`) | Usava `descricao` e não preenchia `dias_atrasos` | ✅ corrigido nesta branch |
| 3 | `services.py` (`devolver_carro`) | Não travava o aluguel (devolução dupla simultânea) | ✅ corrigido nesta branch |
| 4 | `serializers.py` (`CarroSerializer`) | Faltava o campo `marca` (obrigatório no banco). Criar carro pela API dava erro 500 | ✅ resolvido: `marca` foi removida do modelo (migração `0002_remove_carro_marca`, marca + modelo juntos em `modelo`) |
| 5 | `views.py` (`MultaViewSet`) | O `funcionario` vem do corpo da requisição; deveria ser o usuário logado | pendente |
| 6 | `views.py` (`AluguelViewSet.perform_destroy`) | Não trata `RegraDeNegocio` do `excluir_aluguel`. Excluir aluguel com multa dá 500; deveria dar 409 com `raise Conflito(str(erro))`, como nas outras ações | pendente |
| 7 | `config/settings.py` | Depois do HTTPS: `SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` | quando houver HTTPS |
| 8 | Testes da API | Nenhuma view tinha teste (usar `APIClient` do DRF: 401/403/404/409) | ✅ resolvido: `test_alugueis.py`, `test_permissoes.py`, `test_relacionamentos.py` |
