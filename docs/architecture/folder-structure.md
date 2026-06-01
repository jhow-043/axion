# Estrutura de Pastas

## Backend

```
backend/
├── pyproject.toml                    # dependências, scripts, ruff config
├── .env.example                      # variáveis de ambiente documentadas
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/                     # migrations (nunca editar manualmente)
├── CLAUDE.md                         # contexto backend para Claude Code
└── app/
    ├── main.py                       # cria FastAPI app, monta routers, WebSocket
    ├── core/
    │   ├── config.py                 # pydantic-settings (sem hardcode de segredos)
    │   ├── exceptions.py             # hierarquia de exceções + handler global
    │   ├── pagination.py             # esquema de paginação reutilizável
    │   ├── deps.py                   # dependências FastAPI comuns (sessão, paginação)
    │   ├── permissions.py            # catálogo de códigos de permissão (fonte única)
    │   └── security.py              # JWT utils, Argon2 hashing
    ├── db/
    │   ├── engine.py                 # AsyncEngine
    │   ├── session.py                # AsyncSession factory
    │   └── base.py                   # DeclarativeBase
    ├── shared/
    │   ├── tenant_context.py         # ContextVar de tenant
    │   ├── base_repository.py        # BaseRepository com filtro automático de tenant
    │   ├── tenant_mixin.py           # TenantMixin (coluna tenant_id + índice)
    │   └── event_bus.py              # barramento interno de eventos (para P10/P14)
    └── modules/
        ├── auth/
        │   ├── router.py
        │   ├── schemas.py
        │   ├── service.py
        │   ├── repository.py
        │   └── tests/
        ├── users/
        │   ├── models.py
        │   ├── router.py
        │   ├── schemas.py
        │   ├── service.py
        │   ├── repository.py
        │   └── tests/
        ├── teams/
        ├── catalog/                  # prioridades, status, categorias, motivos pendência
        ├── locations/                # setores + locais prediais
        ├── equipments/
        ├── tickets/                  # núcleo + state machine/workflow
        │   ├── models.py
        │   ├── schemas.py
        │   ├── repository.py
        │   ├── service.py
        │   ├── state_machine.py      # transições válidas/inválidas (invariante INV-03)
        │   ├── router.py
        │   └── tests/
        │       ├── test_unit.py
        │       ├── test_integration.py
        │       └── test_tenant_isolation.py
        ├── timeline/
        ├── attachments/              # MinIO
        ├── sla/
        │   ├── models.py
        │   ├── schemas.py
        │   ├── repository.py
        │   ├── service.py            # cálculo de prazos, pausa/retomada
        │   ├── router.py
        │   ├── tasks.py              # Celery tasks: alert_sweep, breach_sweep
        │   └── tests/
        ├── notifications/            # in-app + WebSocket + e-mail
        │   ├── models.py
        │   ├── schemas.py
        │   ├── repository.py
        │   ├── service.py            # notify(), resolução de destinatários
        │   ├── router.py
        │   ├── websocket.py          # ConnectionManager + Redis pub/sub
        │   ├── tasks.py              # Celery task: send_email
        │   └── tests/
        ├── dashboards/
        ├── reports/
        ├── audit/
        └── administration/
```

**Convenção por módulo:**

| Arquivo | Responsabilidade | O que NÃO deve ter |
|---------|-----------------|-------------------|
| `models.py` | ORM SQLAlchemy, herda TenantMixin | Lógica de negócio |
| `schemas.py` | Pydantic request/response | Acesso ao banco |
| `repository.py` | Queries (herda BaseRepository) | Lógica de negócio, HTTP |
| `service.py` | Regras de negócio, orquestra repositórios | AsyncSession direta, HTTP |
| `router.py` | Rotas HTTP, require_permission(), chama service | Lógica de negócio, ORM direto |

---

## Frontend

```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── CLAUDE.md                         # contexto frontend para Claude Code
└── src/
    ├── main.tsx                      # entry point
    ├── app/
    │   ├── App.tsx                   # providers (QueryClient, AuthProvider, Router)
    │   ├── router.tsx                # definição de rotas e guards
    │   └── providers/
    │       ├── AuthProvider.tsx      # contexto de autenticação
    │       └── QueryProvider.tsx     # TanStack Query client
    ├── shared/
    │   ├── components/               # componentes UI reutilizáveis (shadcn + custom)
    │   │   ├── ui/                   # componentes shadcn copiados
    │   │   ├── DataTable.tsx
    │   │   ├── PageHeader.tsx
    │   │   └── StatusBadge.tsx
    │   ├── hooks/
    │   │   ├── useAuth.ts
    │   │   ├── usePagination.ts
    │   │   └── useWebSocket.ts
    │   ├── api/
    │   │   └── client.ts             # axios/fetch client com interceptors JWT
    │   └── ws/
    │       └── notificationSocket.ts # WebSocket client singleton
    ├── config/
    │   ├── constants.ts
    │   └── env.ts                    # import.meta.env tipado
    ├── types/
    │   └── api.ts                    # tipos compartilhados que espelham contratos da API
    ├── utils/
    │   ├── dates.ts                  # formatação dd/mm/yyyy, UTC → local
    │   └── permissions.ts            # helpers RBAC frontend
    └── features/
        ├── auth/
        │   ├── api.ts
        │   ├── components/
        │   │   └── LoginForm.tsx
        │   └── types.ts
        ├── users/
        ├── teams/
        ├── equipments/
        ├── locations/
        ├── catalog/
        ├── tickets/
        │   ├── api.ts
        │   ├── types.ts
        │   ├── hooks/
        │   │   ├── useTickets.ts
        │   │   └── useTicketTransition.ts
        │   └── components/
        │       ├── TicketList.tsx
        │       ├── TicketForm.tsx
        │       ├── TicketDetail.tsx
        │       ├── TicketStatusBadge.tsx
        │       └── TicketActions.tsx
        ├── timeline/
        ├── notifications/
        │   ├── api.ts
        │   ├── types.ts
        │   └── components/
        │       ├── NotificationBell.tsx
        │       └── NotificationList.tsx
        ├── dashboards/
        ├── reports/
        └── administration/
```

**Convenção por feature:**

| Arquivo | Responsabilidade |
|---------|-----------------|
| `api.ts` | TanStack Query hooks (`useQuery`, `useMutation`) para os endpoints da feature |
| `types.ts` | Tipos TypeScript espelhando a API — sem `any` |
| `components/` | Componentes React da feature — sem lógica de fetch direto |
| `hooks/` | Hooks customizados compondo `api.ts` com lógica de UI |
