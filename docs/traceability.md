# Matriz de Rastreabilidade

> Relaciona requisitos funcionais e não-funcionais às specs que os implementam,
> ADRs que os afetam, branches/PRs e o status atual.
>
> Atualizar a coluna `PR` e `Status` após cada merge.
> As colunas `RF/RNF` e `Spec` são derivadas automaticamente dos frontmatters das specs.

---

## Como ler esta matriz

| Coluna | Conteúdo |
|--------|---------|
| RF/RNF | ID do requisito em `docs/product/requirements/` |
| Spec | Plano que realiza o requisito |
| ADR | Decisões arquiteturais que afetam este requisito |
| Branch/PR | Branch de implementação e número do PR (quando criado) |
| Status | `pending` → `in-progress` → `in-review` → `done` |

---

## Fundação e Infraestrutura

| RF/RNF | Descrição resumida | Spec | ADR | Branch/PR | Status |
|--------|-------------------|------|-----|-----------|--------|
| RF-001 | Healthcheck `/health` e `/ping` | P00 | — | feature/000 | done |
| RF-002 | Envelope de erro padronizado | P00 | — | feature/000 | done |
| RF-003 | Paginação com `page` e `page_size` | P00 | — | feature/000 | done |
| RF-004 | Config por variáveis de ambiente | P00 | — | feature/000 | done |
| RNF-OBS-001 | Logging estruturado JSON | P00 | — | feature/000 | done |
| RNF-MANUT-001 | ruff lint/format em todo PR | P00 | — | feature/000 | done |

## Multi-Tenancy

| RF/RNF | Descrição resumida | Spec | ADR | Branch/PR | Status |
|--------|-------------------|------|-----|-----------|--------|
| RF-010 | Isolamento completo entre tenants | P01 | ADR-0001 | feature/001 | done |
| RF-011 | BaseRepository aplica tenant automaticamente | P01 | ADR-0001 | feature/001 | done |
| RF-012 | Cross-tenant retorna 404 | P01 | ADR-0002 | feature/001 | done |
| RF-013 | tenant_id extraído do JWT via ContextVar | P01 | ADR-0004 | feature/001 | done |
| RNF-SEG-001 | Isolamento de dados entre tenants | P01 | ADR-0001 | feature/001 | done |

## Autenticação

| RF/RNF | Descrição resumida | Spec | ADR | Branch/PR | Status |
|--------|-------------------|------|-----|-----------|--------|
| RF-020 | Login JWT com access + refresh token | P03 | — | feature/003 / PR #4 | done |
| RF-021 | Rotação de refresh token | P03 | — | feature/003 / PR #4 | done |
| RF-022 | Logout invalida refresh token | P03 | — | feature/003 / PR #4 | done |
| RF-023 | Senha com Argon2 | P03 | — | feature/003 / PR #4 | done |
| RF-024 | Resposta genérica em login inválido | P03 | — | feature/003 / PR #4 | done |
| RF-025 | Token revogado invalida todos os tokens | P03 | — | feature/003 / PR #4 | done |
| RF-026 | `GET /auth/me` retorna dados e papéis | P03 | — | feature/003 / PR #4 | done |
| RNF-SEG-002 | Argon2 obrigatório | P03 | — | feature/003 / PR #4 | done |
| RNF-SEG-003 | JWT expiração curta + rotação | P03 | — | feature/003 / PR #4 | done |

## Usuários e RBAC

| RF/RNF | Descrição resumida | Spec | ADR | Branch/PR | Status |
|--------|-------------------|------|-----|-----------|--------|
| RF-030 | CRUD de usuários por tenant | P04 | ADR-0001 | feature/018 / PR #23 | in-review |
| RF-031 | RBAC com 4 papéis padrão | P04 | — | feature/018 / PR #23 | in-review |
| RF-032 | Papéis provisionados automaticamente | P04 | — | feature/018 / PR #23 | in-review |
| RF-033 | Permissões = união dos papéis | P04 | — | feature/018 / PR #23 | in-review |
| RF-034 | Admin único protegido | P04 | — | feature/018 / PR #23 | in-review |
| RF-035 | Usuário inativo não autentica | P04 | — | feature/018 / PR #23 | in-review |
| RF-036 | Email único por tenant | P04 | ADR-0002 | feature/018 / PR #23 | in-review |

## Cadastros (Onda 1)

| RF/RNF | Descrição resumida | Spec | ADR | Branch/PR | Status |
|--------|-------------------|------|-----|-----------|--------|
| RF-040 | CRUD de equipes | P05 | ADR-0001 | feature/018 / PR #23 | in-review |
| RF-041 | Chamados direcionados a equipes | P05, P09 | — | feature/018 / PR #23 | in-review |
| RF-042 | Técnicos membros de equipes | P05 | — | feature/018 / PR #23 | in-review |
| RF-050 | CRUD de setores | P06 | ADR-0001 | feature/018 / PR #23 | in-review |
| RF-051 | CRUD de locais prediais | P06 | ADR-0001 | feature/018 / PR #23 | in-review |
| RF-052 | Locais vinculáveis a chamados | P06, P09 | — | feature/018 / PR #23 | in-review |
| RF-060–064 | Catálogos configuráveis | P07 | ADR-0003 | feature/018 / PR #23 | in-review |
| RF-070–071 | Equipamentos e vinculação a chamados | P08 | ADR-0001 | feature/018 / PR #23 | in-review |

## Chamados e Workflow

| RF/RNF | Descrição resumida | Spec | ADR | Branch/PR | Status |
|--------|-------------------|------|-----|-----------|--------|
| RF-080 | Chamado industrial exige equipamento | P09 | ADR-0003 | feature/018 / PR #23 | in-review |
| RF-081 | Chamado predial exige local | P09 | ADR-0003 | feature/018 / PR #23 | in-review |
| RF-082 | Status inicial `new` | P09 | ADR-0003 | feature/018 / PR #23 | in-review |
| RF-083 | Assumir = responsável + `in_progress` | P09 | ADR-0003 | feature/018 / PR #23 | in-review |
| RF-084 | Pendente exige motivo | P09 | ADR-0003 | feature/018 / PR #23 | in-review |
| RF-085 | Resolvido exige solução | P09 | ADR-0003 | feature/018 / PR #23 | in-review |
| RF-086 | Fechado é terminal | P09 | ADR-0003 | feature/018 / PR #23 | in-review |
| RF-087–092 | Observadores, comentários, visibilidade, filtros | P09 | ADR-0002 | feature/018 / PR #23 | in-review |

## SLA

| RF/RNF | Descrição resumida | Spec | ADR | Branch/PR | Status |
|--------|-------------------|------|-----|-----------|--------|
| RF-120 | Política configurável | P12 | ADR-0001 | feature/018 / PR #23 | in-review |
| RF-121 | SLA de Atendimento | P12 | ADR-0004 | feature/018 / PR #23 | in-review |
| RF-122 | SLA de Resolução | P12 | ADR-0004 | feature/018 / PR #23 | in-review |
| RF-123 | SLA pausado em `pending` | P12 | ADR-0003 | feature/018 / PR #23 | in-review |
| RF-124 | Prazo recalculado após pausa | P12 | — | feature/018 / PR #23 | in-review |
| RF-125–126 | Alertas e vencimento automáticos | P12 | ADR-0004 | feature/018 / PR #23 | in-review |
| RF-127 | Indicador de SLA na tela | P12 | — | feature/018 / PR #23 | in-review |

## Notificações e Encerramento

| RF/RNF | Descrição resumida | Spec | ADR | Branch/PR | Status |
|--------|-------------------|------|-----|-----------|--------|
| RF-130–132 | Validação e auto-fechamento | P13 | ADR-0003, ADR-0004 | feature/018 / PR #23 | in-review |
| RF-140–145 | Notificações in-app, WebSocket, e-mail | P14 | ADR-0004 | feature/018 / PR #23 | in-review |

## Dashboards, Auditoria e Admin

| RF/RNF | Descrição resumida | Spec | ADR | Branch/PR | Status |
|--------|-------------------|------|-----|-----------|--------|
| RF-150–151 | Dashboards operacionais | P15 | ADR-0001 | feature/018 / PR #23 | in-review |
| RF-160–161 | Dashboard gerencial e relatórios | P16 | ADR-0001 | feature/018 / PR #23 | in-review |
| RF-170–171 | Auditoria imutável | P17 | ADR-0001 | feature/018 / PR #23 | in-review |
| RF-180–182 | Console de administração | P18 | ADR-0001 | feature/018 / PR #23 | in-review |

## Plataforma Super-Admin

| RF/RNF | Descrição resumida | Spec | ADR | Branch/PR | Status |
|--------|-------------------|------|-----|-----------|--------|
| RF-190 | Dashboard global com métricas agregadas | P19 | ADR-0001 | feature/019 | in-progress |
| RF-191 | Listagem de companies com contadores | P19 | ADR-0001 | feature/019 | in-progress |
| RF-192 | Provisionamento de tenant pelo super-admin | P19 | ADR-0001 | feature/019 | in-progress |
| RF-193 | Soft delete de tenant | P19 | ADR-0002 | feature/019 | in-progress |
| RF-194 | Tenant `is_system` protegido contra exclusão | P19 | ADR-0001 | feature/019 | in-progress |

## HUB Modular

| RF/RNF | Descrição resumida | Spec | ADR | Branch/PR | Status |
|--------|-------------------|------|-----|-----------|--------|
| RF-200 | Catálogo global de módulos (`modules`) | P20 | ADR-0006 | feature/020 | pending |
| RF-201 | Super-admin libera/revoga módulos por empresa | P20, P21 | ADR-0006 | feature/020, feature/021 | pending |
| RF-202 | `/auth/me` retorna `enabled_modules` | P20 | ADR-0006 | feature/020 | pending |
| RF-203 | Módulo não liberado → 404 no backend | P20, P24 | ADR-0002, ADR-0006 | feature/020, feature/024 | pending |
| RF-204 | Home do HUB exibe cards dos módulos liberados | P22 | ADR-0006 | feature/022 | pending |
| RF-205 | Menu lateral data-driven por módulos liberados | P23 | ADR-0006 | feature/023 | pending |
| RF-206 | Rota de módulo não liberado → redirect para `/` | P23 | ADR-0006 | feature/023 | pending |
| RF-207 | UI de gestão de módulos por empresa no super-admin | P21 | ADR-0006 | feature/021 | pending |
| RF-208 | Novo tenant recebe `manutencao` liberado automaticamente | P20 | ADR-0006 | feature/020 | pending |
| RF-209 | Routers de manutenção aplicam `require_module` | P24 | ADR-0006 | feature/024 | pending |

---

## Como atualizar

Após merge de uma spec:
1. Atualize a coluna `Branch/PR` com o número do PR no GitHub.
2. Atualize `Status` para `done`.
3. Atualize o frontmatter da spec (`status: done`).

Para automatizar: um script pode ler os frontmatters `satisfies:` de todas as specs
e gerar esta tabela automaticamente via GitHub MCP ou script Python.
