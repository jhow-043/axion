---
id: P05
slug: equipes
status: done
version: 1.0.0
owner: jhowworks
depends_on: [P01, P04]
satisfies: [RF-040, RF-041, RF-042]
adrs: [ADR-0001, ADR-0002]
branch: feature/005-equipes
last_updated: 2026-06-01
---

# P05 — Equipes de Manutenção

## Objetivo

Cadastrar e gerenciar as equipes de manutenção (Mecânica, Elétrica, Automação, Predial, Instrumentação, etc.) e seus membros técnicos, de forma que chamados possam ser direcionados a equipes antes de serem assumidos por um técnico.

## Escopo

- CRUD de equipes: criar, listar, detalhar, editar, ativar/desativar.
- Gerenciamento de membros: adicionar e remover técnicos de uma equipe.
- Validação de unicidade do nome de equipe por tenant.
- Telas de listagem, formulário e gestão de membros.

## Fora do Escopo

- Roteamento de chamados para equipes (P09 — Chamados).
- Cálculo de filas e métricas por equipe (P15 — Dashboards Operacionais).
- Turnos e escala de trabalho (futuro).
- Equipes hierárquicas ou sub-equipes (futuro).

## Dependências

- **P01** (Multi-Tenancy) — BaseRepository e contexto de tenant.
- **P04** (Usuários e Permissões) — membros de equipe são usuários com papel "Técnico"; `require_permission("team:manage")`.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `teams` | Nova tabela |
| `team_members` | Nova tabela (N:N teams × users) |

### `teams`
```
id          UUID, PK
tenant_id   UUID, FK → tenants, INDEX
name        String, NOT NULL
             UNIQUE(tenant_id, name)
description String, nullable
is_active   Boolean, DEFAULT true
created_at  DateTime
updated_at  DateTime
```

### `team_members`
```
id          UUID, PK
tenant_id   UUID, FK → tenants, INDEX
team_id     UUID, FK → teams
user_id     UUID, FK → users
added_at    DateTime
             UNIQUE(team_id, user_id)
```

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/teams` | Listar equipes do tenant (paginado) | `team:manage` ou `ticket:read` |
| POST | `/api/v1/teams` | Criar equipe | `team:manage` |
| GET | `/api/v1/teams/{id}` | Detalhar equipe com membros | `team:manage` ou `ticket:read` |
| PATCH | `/api/v1/teams/{id}` | Editar equipe | `team:manage` |
| POST | `/api/v1/teams/{id}/deactivate` | Desativar equipe | `team:manage` |
| GET | `/api/v1/teams/{id}/members` | Listar membros | `team:manage` ou `ticket:read` |
| POST | `/api/v1/teams/{id}/members` | Adicionar membro | `team:manage` |
| DELETE | `/api/v1/teams/{id}/members/{user_id}` | Remover membro | `team:manage` |

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Lista de Equipes | Tabela com nome, status e nº de membros; ações de editar/desativar |
| Formulário de Equipe | Criar/editar: nome, descrição |
| Gestão de Membros | Lista de membros da equipe com ação de adicionar/remover |

## Regras de Negócio

1. **Nome único por tenant:** `UNIQUE(tenant_id, name)`.
2. **Membro ativo:** apenas usuários ativos do mesmo tenant podem ser adicionados como membros.
3. **Equipe inativa não recebe novos chamados:** validação aplicada em P09 — a spec de Equipes apenas mantém o flag `is_active`.
4. **Membro único por equipe:** `UNIQUE(team_id, user_id)` — não duplicar o mesmo técnico na mesma equipe.
5. **Remoção de membro:** não bloqueia mesmo que o membro tenha chamados abertos na equipe — a responsabilidade do chamado permanece no técnico.
6. **Desativação de equipe:** não encerra chamados vinculados; apenas bloqueia novos. Validar se há chamados abertos e avisar (sem bloquear).

## Critérios de Aceite

- [ ] CRUD de equipes com isolamento de tenant.
- [ ] Nome duplicado no mesmo tenant → erro de validação.
- [ ] Adicionar membro inativo → erro de validação.
- [ ] Adicionar membro de outro tenant → erro de validação ou 404.
- [ ] Membro duplicado na equipe → erro de validação.
- [ ] Equipe inativa não aparece nas opções de roteamento de chamado (integração com P09).
- [ ] Telas de lista, formulário e membros funcionais.

## Estratégia de Testes

### Testes Unitários

- Validação de unicidade de nome por tenant (no service).
- Validação de membro ativo e do mesmo tenant.
- Prevenção de membro duplicado.

### Testes de Integração

- `POST /teams` → equipe criada com tenant_id correto.
- `POST /teams` com nome duplicado no mesmo tenant → 422.
- `POST /teams/{id}/members` com usuário inativo → 422.
- `GET /teams` → lista apenas equipes do tenant corrente.
- `DELETE /teams/{id}/members/{user_id}` → membro removido.

### Testes E2E

- Admin cria equipe "Elétrica" → adiciona técnico → lista mostra membro.
- Admin remove técnico da equipe → lista de membros atualizada.
- Admin tenta adicionar mesmo técnico duas vezes → exibe erro.

## Riscos Técnicos

- **Baixo.** Módulo simples sem regras de negócio complexas.
- Atenção ao isolamento de tenant ao listar usuários elegíveis para adição como membros (não exibir usuários de outros tenants).

## Complexidade

**Baixa**

## Prioridade

**Alta**

## Branch

`feature/005-equipes`
