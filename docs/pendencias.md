# Pendências

## Banco de dados (escopo desta branch)

| # | Pendência | Prioridade |
|---|---|---|
| 1 | Ligar os `services.py` aos repositórios (hoje ainda usam o ORM) | alta |
| 2 | Testes dos services (carro indisponível, devolução dupla, multa em aluguel finalizado) | alta |
| 3 | Confirmar com o professor se o projeto deve ser **sem ORM**. A estrutura atual funciona dos dois jeitos: os `models.py` (ORM) continuam e as tabelas são as mesmas; os repositórios (SQL puro) já estão prontos e testados. **Se for sem ORM:** ligar services/views aos repositórios e trocar os `models.py` por migrations `RunSQL`. **Se ORM for permitido:** os repositórios podem ser usados só nas consultas mais complexas, ou removidos | alta, decidir com o professor/time |
| 4 | Comando de *seed* (`python manage.py popular_banco`) com carros/clientes de exemplo para apresentação. A pasta `locadora/management/commands/` já existe e está vazia | média |
| 5 | Índices para consultas frequentes (`locadora_carro(status)`, `locadora_aluguel(status)`) | baixa |
| 6 | Guardar dinheiro como inteiro em centavos, se quiserem evitar `numeric` no SQLite | baixa |
| 7 | Adicionar as novas variáveis (`DB_ENGINE`, `POSTGRES_*`, `DJANGO_ALLOWED_HOSTS`) no `.env.example` | baixa |
| 8 | Configurar backup automático no servidor de produção | quando houver servidor |

## Encontrado em outras partes do código (avisar o time)

Esses pontos não são da camada de banco, mas vão gerar **erro 500** quando usados:

| # | Arquivo | Problema |
|---|---|---|
| 1 | ~~`locadora/serializers.py` (`MultaSerializer`)~~ | ~~Usava `descricao` em vez de `motivo`~~ **corrigido nesta branch** (o CI acusou) |
| 2 | `locadora/services.py` (`registrar_multa`) | Também usa `descricao` e não preenche `dias_atrasos` (campo obrigatório) |
| 3 | `locadora/serializers.py` (`CarroSerializer`) | Falta o campo `marca` (obrigatório no banco). Criar carro pela API falha |
| 4 | `locadora/views.py` (`MultaViewSet`) | O `funcionario` vem do corpo da requisição; deveria ser o usuário logado |
| 5 | `locadora/services.py` (`devolver_carro`) | Não trava o aluguel. Com o repositório, `alugueis.finalizar()` já resolve isso |
| 6 | `README.md` | Vazio: apontar para `docs/` |
| 7 | `config/settings.py` | Depois do HTTPS: `SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` |
| 8 | Testes da API | Nenhuma view tem teste ainda |
