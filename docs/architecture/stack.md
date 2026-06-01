# Stack Tecnológica

## Backend

| Componente | Tecnologia | Versão | Justificativa |
|------------|-----------|--------|---------------|
| Runtime | Python | 3.12 | Suporte a async nativo, type hints modernos |
| Framework HTTP | FastAPI | 0.115+ | async-first, Pydantic integrado, OpenAPI automático |
| ORM | SQLAlchemy | 2.0 async | API declarativa modern, sessão async, 2.0 remove legados |
| Validação | Pydantic | v2 | Performance (Rust core), modo strict, serialização |
| Migrations | Alembic | 1.13+ | Padrão com SQLAlchemy, autogenerate confiável |
| Task queue | Celery | 5.x | Padrão Python para jobs assíncronos e schedulados |
| Scheduler | Celery Beat | 5.x | Agendamento periódico integrado ao Celery |
| Hashing | Argon2 (passlib) | — | Vencedor da Password Hashing Competition, seguro contra GPU |
| JWT | python-jose | — | RFC 7519, suporte a RS256/HS256 |
| Config | pydantic-settings | 2.x | Carregamento de env vars com validação Pydantic |
| Lint/Format | ruff | 0.4+ | Substituição de flake8+black+isort, extremamente rápido |
| Testes | pytest + pytest-asyncio | — | Padrão Python, suporte async nativo |
| HTTP testing | httpx | — | AsyncClient para testes FastAPI |
| Package manager | uv | — | Instalação ultrarrápida, lock file determinístico |

## Frontend

| Componente | Tecnologia | Versão | Justificativa |
|------------|-----------|--------|---------------|
| Framework | React | 18+ | Ecossistema amplo, concurrent mode |
| Bundler | Vite | 5+ | HMR instantâneo, build extremamente rápido |
| Linguagem | TypeScript | 5+ | Tipagem end-to-end com contratos da API |
| Server state | TanStack Query | v5 | Cache, refetch, optimistic updates, devtools |
| Roteamento | React Router | v6 | Data APIs, loaders, SPA padrão |
| UI base | shadcn/ui + Radix | — | Acessível, sem estilo imposto, copiado para o projeto |
| Estilos | Tailwind CSS | v3 | Utility-first, sem CSS global |
| Gráficos | Recharts | — | React-native, composável, bom para dashboards |
| Drag & drop | dnd-kit | — | Acessível, performático (usado se necessário) |
| Package manager | pnpm | — | Eficiente em disco, workspaces |

## Infraestrutura

| Componente | Tecnologia | Versão | Justificativa |
|------------|-----------|--------|---------------|
| Banco | PostgreSQL | 16 | Índices avançados, JSON nativo, UUID nativo |
| Cache/Broker | Redis | 7+ | Celery broker + pub/sub WebSocket multi-instância |
| Object storage | MinIO | — | S3-compatível, on-premise, sem vendor lock-in |
| Containerização | Docker Compose | — | Deploy simples on-premise, sem Kubernetes |
| Proxy reverso | Nginx | — | TLS, proxy para API e frontend estático |
| SMTP dev | Mailhog | — | Captura de e-mails em desenvolvimento sem envio real |

## Ferramentas de desenvolvimento

| Ferramenta | Uso |
|------------|-----|
| Claude Code | Implementação guiada por specs, slash commands SDD |
| Context7 MCP | Documentação atualizada das libs (FastAPI, SQLAlchemy, TanStack...) |
| Postgres MCP | Introspecção read-only do schema de desenvolvimento |
| Playwright MCP | Testes E2E automatizados das specs |
| GitHub MCP | Automação de PRs e CI |
