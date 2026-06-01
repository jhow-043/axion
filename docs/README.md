# Gestão de Manutenção Industrial e Predial — Índice

> Este é o índice de navegação. O conteúdo vive nos documentos linkados abaixo.
> Não adicione conteúdo substantivo aqui — use os documentos de destino.

---

## Para começar (leia nesta ordem)

1. [Visão do produto](product/vision.md) — problema, personas, objetivos
2. [Constituição](constitution.md) — **invariantes invioláveis e DoD global**
3. [AGENTS.md](../AGENTS.md) — guia para agentes de IA
4. [Fluxo SDD](process/spec-workflow.md) — como trabalhar neste projeto

---

## Produto

| Documento | Conteúdo |
|-----------|---------|
| [product/vision.md](product/vision.md) | Problema, personas, objetivos de negócio |
| [product/glossary.md](product/glossary.md) | Linguagem ubíqua do domínio |
| [product/requirements/functional.md](product/requirements/functional.md) | Catálogo RF-### |
| [product/requirements/non-functional.md](product/requirements/non-functional.md) | Catálogo RNF-### |

---

## Arquitetura

| Documento | Conteúdo |
|-----------|---------|
| [architecture/overview.md](architecture/overview.md) | Contexto, contêineres, fluxos (C4) |
| [architecture/stack.md](architecture/stack.md) | Stack tecnológica com versões e justificativas |
| [architecture/data-model.md](architecture/data-model.md) | ERD consolidado de todos os módulos |
| [architecture/folder-structure.md](architecture/folder-structure.md) | Estrutura de pastas backend e frontend |
| [architecture/decisions/](architecture/decisions/) | ADRs — decisões arquiteturais |

---

## Specs (P00–P18)

| ID | Spec | Complexidade | Prioridade | Status |
|----|------|-------------|-----------|--------|
| P00 | [Fundação Backend](specs/000-fundacao-plataforma.md) | Média | Crítica | approved |
| P01 | [Multi-Tenancy](specs/001-multi-tenancy.md) | Alta | Crítica | approved |
| P02 | [Fundação Frontend](specs/002-fundacao-frontend.md) | Média | Crítica | approved |
| P03 | [Autenticação](specs/003-autenticacao.md) | Média | Crítica | approved |
| P04 | [Usuários e Permissões](specs/004-usuarios-permissoes.md) | Média | Crítica | approved |
| P05 | [Equipes](specs/005-equipes.md) | Baixa | Alta | approved |
| P06 | [Setores e Locais](specs/006-setores-locais.md) | Baixa | Alta | approved |
| P07 | [Catálogos Configuráveis](specs/007-catalogos-configuraveis.md) | Média | Alta | approved |
| P08 | [Equipamentos](specs/008-equipamentos.md) | Baixa | Alta | approved |
| P09 | [Chamados: Núcleo & Workflow](specs/009-chamados-workflow.md) | Alta | Crítica | approved |
| P10 | [Timeline](specs/010-timeline.md) | Média | Alta | approved |
| P11 | [Anexos e Evidências](specs/011-anexos-evidencias.md) | Média | Alta | approved |
| P12 | [SLA](specs/012-sla.md) | Alta | Crítica | approved |
| P13 | [Encerramento e Validação](specs/013-encerramento-validacao.md) | Média | Alta | approved |
| P14 | [Notificações](specs/014-notificacoes.md) | Alta | Alta | approved |
| P15 | [Dashboards Operacionais](specs/015-dashboards-operacionais.md) | Média | Alta | approved |
| P16 | [Dashboard Gerencial & Relatórios](specs/016-dashboard-gerencial-relatorios.md) | Média | Média | approved |
| P17 | [Auditoria](specs/017-auditoria.md) | Média | Média | approved |
| P18 | [Administração](specs/018-administracao.md) | Média | Alta | approved |

### Roadmap em ondas

```
ONDA 0 — Fundação (sequencial, caminho crítico)
  P00 → P01 → P02 → P03 → P04

ONDA 1 — Cadastros (paralelos após P04)
  P05  P06  P07  P08

ONDA 2 — Núcleo de Chamados (após P05–P08)
  P09 → P10
       P11 (paralelo a P10)

ONDA 3 — Regras Avançadas (após P09)
  P12 → P13
  P14  (paralelo a P12/P13)

ONDA 4 — Visualização (após P09/P12)
  P15 → P16

ONDA 5 — Transversais (contínuo)
  P17  P18
```

### Mapa de dependências

```
P00 ──► P01 ──► P03 ──► P04 ──┬──► P05
   └──► P02 ──► (P03)         ├──► P06 ──► P08
                              ├──► P07 ──► P08
                              └──► P09 ◄── (P05,P06,P07,P08)
P09 ──► P10
P09 ──► P11
P09 ──► P12 ──► P13
P09 ──► P14   (P12,P13 ──► P14)
P09,P12 ──► P15 ──► P16
P00,P01,P04 ──► P17
(P04,P05,P06,P07,P12,P14) ──► P18
```

---

## Processo

| Documento | Conteúdo |
|-----------|---------|
| [process/spec-workflow.md](process/spec-workflow.md) | Fluxo SDD completo (requisito → merge) |
| [process/git-strategy.md](process/git-strategy.md) | Branches, commits, PRs, releases, rollback |
| [process/testing-strategy.md](process/testing-strategy.md) | Pirâmide de testes, fixtures, CI |
| [process/code-conventions.md](process/code-conventions.md) | Convenções Python, TypeScript e geração por IA |
| [process/environments.md](process/environments.md) | Dev, homologação, produção, deploy, backup |

---

## Rastreabilidade

| Documento | Conteúdo |
|-----------|---------|
| [traceability.md](traceability.md) | Matriz RF/RNF ↔ Spec ↔ ADR ↔ PR |
| [architecture/decisions/](architecture/decisions/) | ADR-0001 a ADR-0004 (e futuros) |
