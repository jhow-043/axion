# AGENTS.md — Guia de Agentes de IA

Arquivo canônico de orientação para qualquer agente de IA (Claude Code, Cursor, Copilot, etc.)
que trabalhe neste repositório. Leia este arquivo **antes** de qualquer implementação.

---

## 1. Visão geral do projeto

Sistema de **Gestão de Manutenção Industrial e Predial** — plataforma multi-tenant SaaS on-premise
para abertura, acompanhamento e encerramento de chamados de manutenção, com controle de SLA,
notificações em tempo real e dashboards operacionais e gerenciais.

- Domínio: `docs/product/vision.md`
- Glossário: `docs/product/glossary.md`
- Requisitos funcionais: `docs/product/requirements/functional.md`
- Requisitos não-funcionais: `docs/product/requirements/non-functional.md`

---

## 2. Stack tecnológica

Consulte `docs/architecture/stack.md` para a lista completa com versões.

Resumo:
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2.0 async + Pydantic v2 + Alembic + Celery + Redis
- **Frontend:** React + Vite + TypeScript + TanStack Query + React Router + Tailwind + shadcn/ui
- **Banco:** PostgreSQL 16
- **Arquivos:** MinIO (S3-compatível)
- **Auth:** JWT (access + refresh) + Argon2 + RBAC próprio
- **Deploy:** Docker Compose on-premise

---

## 3. Arquitetura e estrutura de pastas

- Visão geral (C4 contexto + contêineres): `docs/architecture/overview.md`
- Modelo de dados consolidado: `docs/architecture/data-model.md`
- Estrutura de pastas backend e frontend: `docs/architecture/folder-structure.md`
- Decisões arquiteturais (ADRs): `docs/architecture/decisions/`

---

## 4. Princípios inegociáveis (Constituição)

Leia `docs/constitution.md` antes de escrever qualquer linha de código.

Resumo rápido dos 5 invariantes que nunca podem ser violados:
1. Todo acesso a dados de domínio passa pelo `BaseRepository` — sem queries diretas de domínio.
2. Acesso cross-tenant retorna **404**, nunca 403.
3. A máquina de estados do chamado é invariante de código; catálogo ajusta apenas rótulo/ordem/flags.
4. Jobs Celery recebem `tenant_id` explicitamente — nunca assumem do ContextVar.
5. Segredos sempre em variáveis de ambiente; nunca valores padrão fixos no código.

---

## 5. Fluxo de desenvolvimento baseado em Specs (SDD)

Cada unidade de trabalho é uma **spec** em `docs/specs/`. Cada spec define:
- Escopo exato + fora do escopo
- Entidades do banco
- APIs e telas necessárias
- Regras de negócio
- Critérios de Aceite (checkboxes = Definition of Done)
- Estratégia de testes (unit / integração / E2E)

Fluxo completo: `docs/process/spec-workflow.md`

Regras para o agente:
- Receba **uma spec** por tarefa. Não cruze fronteiras de módulo além do que a spec prevê.
- Os **Critérios de Aceite** são o DoD — todos devem estar cobertos por testes.
- Respeite o mapa de dependências: só implemente P## quando suas dependências estiverem presentes.
- Crie a branch `feature/<id>-<slug>` conforme indicado na spec. Um PR por spec.

---

## 6. Comandos essenciais

### Backend (Python/FastAPI)
```bash
# Instalar dependências
uv sync  # ou: pip install -e ".[dev]"

# Rodar testes
pytest -q

# Lint e formatação
ruff check .
ruff format --check .

# Migrations
alembic upgrade head
alembic revision --autogenerate -m "descrição"

# Dev server
uvicorn app.main:app --reload
```

### Frontend (React/Vite)
```bash
# Instalar dependências
pnpm install  # ou: npm install

# Dev server
pnpm dev

# Build
pnpm build

# Lint
pnpm lint

# Testes
pnpm test
```

### Docker Compose (ambiente completo)
```bash
docker compose up -d          # sobe todos os serviços
docker compose logs -f api    # logs do backend
docker compose down -v        # derruba + remove volumes
```

---

## 7. Convenções de código

Consulte `docs/process/code-conventions.md` para convenções completas.

Resumo crítico:

### Backend — padrão de módulo
Cada módulo em `backend/app/modules/<nome>/` deve ter:
```
router.py      # rotas HTTP (sem lógica de negócio)
schemas.py     # Pydantic I/O (request/response)
models.py      # ORM SQLAlchemy (herda TenantMixin)
service.py     # regras de negócio (sem acesso direto ao banco)
repository.py  # queries (herda BaseRepository, tenant automático)
tests/         # testes do módulo
```

### Frontend — padrão de feature
Cada feature em `frontend/src/features/<nome>/` deve ter:
```
api.ts          # chamadas de API via TanStack Query
components/     # componentes da feature
hooks/          # hooks customizados
types.ts        # tipos locais da feature
```

### Comentários
Só para o **porquê** — nunca para o que o código faz.
Cite o ADR ou a regra de negócio relevante quando necessário.

---

## 8. Testes

Consulte `docs/process/testing-strategy.md` para a estratégia completa.

Regras mínimas:
- **Cobertura mínima de 90%** — CI rejeita PRs abaixo do limiar (`--cov-fail-under=90`).
- Todo critério de aceite da spec tem ≥1 teste correspondente.
- Testes de isolamento de tenant obrigatórios por módulo.
- Testes unitários para toda regra de negócio pura (state machine, cálculos de SLA, etc.).
- `pytest --cov=app --cov-fail-under=90` deve passar antes de qualquer PR.

---

## 9. Git e PRs

Consulte `docs/process/git-strategy.md` para a estratégia completa.

Resumo:
- Branches: `feature/<id>-<slug>`, `fix/...`, `hotfix/...`
- Commits: Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`)
- Um PR por spec — título referencia o plano (ex.: `feat(tickets): implementa P09`)
- CI obrigatório verde antes de merge

---

## 10. MCP — servidores disponíveis

Configurados em `.mcp.json`. Use-os ativamente:

| Servidor | Quando usar |
|----------|-------------|
| `context7` | Antes de usar qualquer API de FastAPI, SQLAlchemy, Pydantic, TanStack Query, shadcn. Elimina código obsoleto/alucinado. |
| `postgres` | Para introspectar o schema PG16 real, validar que migrations batem com `data-model.md`, checar índices. Read-only — schema só muda via migration Alembic. |
| `github` | Criar/atualizar PRs, linkar a P##, consultar status de CI. |
| `playwright` | Conduzir testes E2E descritos nos critérios de aceite das specs. |

---

## 11. Rastreabilidade

- Specs têm frontmatter `satisfies: [RF-###, RNF-###]` linkando aos requisitos.
- PRs citam `Spec: P##` e `Satisfaz: RF-###`.
- Matriz completa: `docs/traceability.md`

---

## 12. O que NÃO fazer

- Nunca escrever query de domínio fora do `BaseRepository`.
- Nunca retornar 403 para acesso cross-tenant (usar 404).
- Nunca hardcodar `tenant_id` em jobs Celery.
- Nunca commitar segredos ou credenciais.
- Nunca iniciar um P## antes de suas dependências estarem implementadas.
- Nunca cruzar fronteiras de módulo além do previsto na spec.
- Nunca misturar regra de negócio no `router.py`.
- Nunca criar documentos de planejamento ou análise como arquivos — use o contexto da conversa.
