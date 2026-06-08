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
| — | — | — | *A preencher na Fase A* | — |

**Totais por classificação:**
- Bloqueador: 0
- Alto: 0
- Médio: 0
- Baixo: 0

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

*Última atualização: 2026-06-08 | Branch: feature/018-administracao*
