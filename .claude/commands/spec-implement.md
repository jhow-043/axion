# /spec-implement — Implementar uma spec completa

Executa a implementação de uma spec aprovada, respeitando fronteiras de módulo e a Constituição.

## Uso

```
/spec-implement P##
```

Exemplo: `/spec-implement P09`

## Pré-requisitos

1. Spec com `status: approved` no frontmatter.
2. Todas as specs listadas em `depends_on` com `status: done`.
3. `/spec-plan` executado e aprovado (plano disponível).

## O que o agente faz

### Fase 0 — Contexto obrigatório
Lê nesta ordem (sem pular):
1. `docs/constitution.md`
2. A spec alvo
3. Todos os ADRs do frontmatter `adrs:`
4. `docs/architecture/data-model.md`
5. `docs/architecture/folder-structure.md`
6. `docs/process/code-conventions.md`
7. Consulta `context7` para as libs usadas nesta spec

### Fase 1 — Branch
Cria a branch `feature/<id>-<slug>` a partir de `develop`.
Atualiza `status: in-progress` no frontmatter da spec.

### Fase 2 — Implementação (camada a camada)
Ordem obrigatória dentro do módulo backend:
1. `models.py` — entidades ORM com `TenantMixin`, índices corretos
2. Migration Alembic — `alembic revision --autogenerate`
3. `repository.py` — herda `BaseRepository`, scope de tenant automático
4. `schemas.py` — Pydantic v2 request/response
5. `service.py` — regras de negócio (sem acesso direto ao banco)
6. `router.py` — rotas com `require_permission()`, sem lógica de negócio
7. Montar router em `main.py`

Frontend (se previsto na spec):
1. `types.ts` — tipos espelhando contratos da API
2. `api.ts` — TanStack Query hooks
3. `components/` — componentes da feature
4. Registrar rotas no React Router

### Fase 3 — Testes
Escreve testes cobrindo **cada** Critério de Aceite (checkbox) da spec:
1. Testes unitários (regras de negócio puras)
2. Testes de integração (rotas + banco)
3. Testes de isolamento de tenant (obrigatórios)
4. Testes E2E via Playwright (se spec prevê telas)

### Fase 4 — Validação local
```bash
ruff check . && ruff format --check .
pytest -q
```
Todos os testes devem passar antes de qualquer commit.

### Fase 5 — Commit e PR
Commits granulares seguindo Conventional Commits.
Abre PR com:
- Título: `feat(<módulo>): <descrição> [P##]`
- Corpo: referência ao P##, critérios de aceite atendidos, ADRs aplicados
- Atualiza `status: in-review` no frontmatter da spec

## Fronteiras de módulo

O agente altera APENAS:
- `backend/app/modules/<módulo-da-spec>/`
- Arquivos de configuração central previstos na spec (ex.: `main.py` para montar router)
- `frontend/src/features/<feature-da-spec>/`

Não toca outros módulos sem que a spec preveja explicitamente.

## Contexto necessário

- `docs/constitution.md` (obrigatório)
- `docs/process/code-conventions.md`
- `docs/process/testing-strategy.md`
