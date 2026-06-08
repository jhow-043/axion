# Rastreabilidade — Estabilização

> Matriz completa: **Spec ↔ Problema (EST-ID) ↔ Issue GitHub (GH#) ↔ Branch ↔ PR**

## Como ler

- **EST-ID**: `EST-<MÓDULO>-###` — identificador estável do problema, criado na Fase A.
- **GH#**: número da Issue no GitHub (`jhow-043/axion`), criada **após aprovação** na Fase B.
- **Branch**: `fix/EST-<MÓDULO>-###-<slug>` — criada na Fase C ao corrigir.
- **PR**: número do Pull Request, referencia `EST-ID`, `GH#` e a spec.

## Formato de linha

| EST-ID | Spec | Subplano | Classificação | Descrição | GH# | Branch | PR | Status |
|--------|------|----------|--------------|-----------|-----|--------|-----|--------|
| EST-AUTH-001 | P03 | 01 | Bloqueador | *descrição* | — | — | — | Catalogado |

---

## Problemas catalogados

> A preencher progressivamente durante a Fase A.

| EST-ID | Spec | Subplano | Classificação | Descrição | GH# | Branch | PR | Status |
|--------|------|----------|--------------|-----------|-----|--------|-----|--------|
| EST-FE-001 | P12 | 08 | Bloqueador | Build frontend falha por dependencia `date-fns` ausente em `SlaIndicator` | - | - | #26 | Mergeado |
| EST-FE-002 | P15 | 09 | Bloqueador | Build frontend falha por `data` possivelmente indefinido em `KanbanBoard` | #27 | fix/EST-FE-002-kanban-data-narrowing | #28 | Mergeado |
| EST-FE-003 | P02 | 10 | Alto | Lint frontend nao executa por falta de `eslint.config.*` compativel com ESLint 9 | - | - | - | Catalogado |
| EST-DEV-001 | DX | Geral | Alto | `start.ps1` imprime erros `PID : O termo 'PID' nao e reconhecido` ao iniciar Celery/Vite | - | - | - | Catalogado |
| EST-FE-004 | P02 | 10 | Medio | React Router emite warning `No HydrateFallback element provided` no console do navegador | - | - | - | Catalogado |
| EST-AUTH-001 | P03 | 01 | Medio | Console mostra varios 401 em `/auth/refresh` e `/auth/login` ao abrir/login; precisa separar fluxo esperado de bug real | - | - | - | Catalogado |
| EST-BE-001 | P00-P19 | Geral | Alto | `ruff check .` falha com 59 ocorrencias em codigo e testes | - | - | - | Catalogado |
| EST-BE-002 | P00 | Geral | Medio | `Settings.DEBUG` quebra testes quando ambiente externo define `DEBUG=release` | - | - | - | Catalogado |
| — | — | — | — | *Aguardando Fase A* | — | — | — | — |

---

## Labels GitHub (a criar antes da Fase B)

| Label | Cor | Descrição |
|-------|-----|-----------|
| `estabilizacao` | #e11d48 | Fase de estabilização |
| `bloqueador` | #dc2626 | Impede uso da plataforma |
| `prioridade-alta` | #f97316 | Funcionalidade importante quebrada |
| `prioridade-media` | #eab308 | Funcionalidade parcial ou incorreta |
| `prioridade-baixa` | #22c55e | Ajuste visual/texto/navegação |
| `modulo-auth` | #6366f1 | P03, P04 |
| `modulo-multiempresa` | #8b5cf6 | P01 |
| `modulo-chamados` | #3b82f6 | P09 |
| `modulo-sla` | #0ea5e9 | P12, P13 |
| `modulo-admin` | #14b8a6 | P18, P19 |

---

*Atualizado nas Fases A, B e C conforme o diagnóstico avança.*
