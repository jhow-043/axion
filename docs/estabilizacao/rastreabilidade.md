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
