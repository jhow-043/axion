# MASTER — Plano de Estabilização da Plataforma

> **Documento-raiz** da fase de estabilização. Coordena subplanos, issues, branches e PRs.
> Nenhuma funcionalidade nova enquanto esta fase estiver ativa.

## Status global

| Fase | Status | Descrição |
|------|--------|-----------|
| Fase 0 — Bootstrap | ✅ Concluída | Estrutura docs/estabilizacao/ criada |
| Fase A — Diagnóstico | 🔄 Em andamento | Auditoria spec-a-spec, sem alterar código |
| Fase B — Priorização / Issues | ⏳ Aguardando | Revisão do diagnóstico → gerar Issues no GitHub |
| Fase C — Correção controlada | ⏳ Aguardando | 1 issue por vez: branch → fix → teste → PR |

---

## Índice de subplanos

| # | Subplano | Specs | Status Diagnóstico |
|---|----------|-------|-------------------|
| 01 | [auth-permissoes](subplanos/01-auth-permissoes.md) | P03, P04 | ⏳ Pendente |
| 02 | [multiempresa](subplanos/02-multiempresa.md) | P01 | ⏳ Pendente |
| 03 | [administracao](subplanos/03-administracao.md) | P18, P19 | ⏳ Pendente |
| 04 | [usuarios](subplanos/04-usuarios.md) | P04 | ⏳ Pendente |
| 05 | [setores-locais](subplanos/05-setores-locais.md) | P06 | ⏳ Pendente |
| 06 | [equipamentos](subplanos/06-equipamentos.md) | P08 | ⏳ Pendente |
| 07 | [chamados](subplanos/07-chamados.md) | P09, P10, P11, P14 | ⏳ Pendente |
| 08 | [sla-encerramento](subplanos/08-sla-encerramento.md) | P12, P13 | ⏳ Pendente |
| 09 | [dashboards](subplanos/09-dashboards.md) | P15, P16 | ⏳ Pendente |
| 10 | [navegacao](subplanos/10-navegacao.md) | P02 | ⏳ Pendente |
| 11 | [visual](subplanos/11-visual.md) | — | ⏳ Pendente |

---

## Problemas catalogados (resumo global)

> Preenchido progressivamente durante a Fase A. Ver subplanos para detalhes.

| EST-ID | Módulo | Classificação | Descrição resumida | Issue GH# |
|--------|--------|--------------|-------------------|-----------|
| EST-FE-001 | SLA / Frontend | Bloqueador | `npm run build` falha: dependencia `date-fns` ausente em `SlaIndicator` | - |
| EST-FE-002 | Dashboards / Frontend | Bloqueador | `npm run build` falha: `data` possivelmente indefinido em `KanbanBoard` | #27 |
| EST-FE-003 | Frontend / Tooling | Alto | `npm run lint` falha: ESLint 9 exige `eslint.config.*`, mas o projeto nao possui flat config | #35 |
| EST-DEV-001 | Dev scripts | Alto | `start.ps1` imprime erros de PowerShell ao mostrar PIDs de Celery/Vite | #30 |
| EST-FE-004 | Navegacao / Frontend | Medio | React Router emite warning `No HydrateFallback element provided` no console | #32 |
| EST-AUTH-001 | Auth / Frontend | Medio | Console mostra repetidos 401 em refresh/login; confirmar se e fluxo esperado ou bug | #33 |
| EST-BE-001 | Backend / Tooling | Alto | `uv run ruff check .` falha com 59 ocorrencias em migrations, reports, dashboards e testes | #36 |
| EST-BE-002 | Backend / Ambiente | Medio | `uv run pytest` falha quando `DEBUG=release`; suite passa ao executar com `DEBUG=false` | #37 |
| — | — | — | *A preencher na Fase A* | — |

**Totais por classificação:**
- Bloqueador: 0
- Alto: 0
- Médio: 0
- Baixo: 0

Contagem atual da Fase A:
- Bloqueador: 2
- Alto: 3
- Medio: 3
- Baixo: 0

## Ultima varredura automatizada

Data: 2026-06-08

| Comando | Resultado |
|---------|-----------|
| `npm run build` | Falhou: EST-FE-001, EST-FE-002 |
| `npm run test` | Passou: 8 arquivos, 35 testes |
| `npm run lint` | Falhou: EST-FE-003 |
| `uv sync --extra dev` | Passou |
| `uv run pytest tests/administration -q` com `DEBUG=false` | 33 testes passaram; falha apenas no gate de cobertura por execucao parcial |
| `uv run pytest -q` com `DEBUG=false` | Passou: 690 testes, cobertura 93,78% |
| `uv run ruff check .` | Falhou: EST-BE-001 |

## Correcoes concluidas

| EST-ID | Status | Validacao |
|--------|--------|-----------|
| EST-FE-001 | Mergeado | PR #26 |
| EST-FE-002 | Mergeado | Issue #27; PR #28; `npm run build`; `npm run test` |
| EST-DEV-001 | Mergeado | Issue #30; PR #31; validado pelo usuario via `start.ps1` |

## Novos achados manuais

Data: 2026-06-08

| EST-ID | Evidencia | Status |
|--------|-----------|--------|
| EST-DEV-001 | `.\start.ps1` mostra `PID : O termo 'PID' nao e reconhecido` nas linhas de Celery/Vite | Catalogado |
| EST-FE-004 | Console do navegador mostra `No HydrateFallback element provided` | Issue #32 aberta |
| EST-AUTH-001 | Console mostra 401 em `/auth/refresh` e `/auth/login`; requer reproducao com `.\start.ps1 -Seed` e credenciais seed | Issue #33 aberta |

## Issues de tooling e ambiente

| EST-ID | Issue | Reproducao |
|--------|-------|------------|
| EST-FE-003 | #35 | `cd frontend && npm run lint` |
| EST-BE-001 | #36 | `cd backend && uv run ruff check .` |
| EST-BE-002 | #37 | `DEBUG=release` herdado do ambiente e `cd backend && uv run pytest -q` |

---

## Artefatos de suporte

- [Inventário de Specs](inventario-specs.md) — status real de P00–P19
- [Inventário de Módulos](inventario-modulos.md) — backend + frontend
- [Rastreabilidade](rastreabilidade.md) — spec ↔ EST-ID ↔ GH# ↔ branch/PR

---

## Critério de conclusão por spec

Uma spec só é marcada como concluída quando, na **interface**:
- O fluxo principal funciona (criar · listar · ver · editar · desativar/reativar · usar em módulo dependente).
- Dados persistem e aparecem corretamente nas listagens.
- O registro pode ser usado nos módulos dependentes.
- Permissões corretas; sem 401/403/500 no fluxo esperado.
- Sem erros visíveis no console do navegador.
- Comportamento coerente com o modelo multiempresa.

---

## Regras da fase

- Sem novas funcionalidades ou specs de produto.
- Sem expandir escopo além do que está especificado.
- Sem refatoração grande sem necessidade.
- Sem mudança de arquitetura sem justificar.
- Backend "salvando dados" **não** conta como validação suficiente.

---

## Ambiente

```
./start.ps1 -Seed   # sobe toda a stack
./stop.ps1          # para tudo

Credenciais seed:
  SaaS Admin: admin@plataforma.local / admin123  → /plataforma
  Admin demo: admin@demo.com / admin123           → app normal

URLs:
  Frontend  : http://localhost:5173
  API       : http://localhost:8000
  Docs API  : http://localhost:8000/docs
  MailHog   : http://localhost:8025
  MinIO     : http://localhost:9001
```

---

*Última atualização: 2026-06-08 | Branch: docs/link-console-error-issues*
