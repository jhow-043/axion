---
id: P07
slug: catalogos-configuraveis
status: in-review
version: 1.0.0
owner: jhowworks
depends_on: [P01, P04]
satisfies: [RF-060, RF-061, RF-062, RF-063, RF-064]
adrs: [ADR-0001, ADR-0002, ADR-0003]
branch: feature/007-catalogos-configuraveis
last_updated: 2026-06-02
---

# P07 — Catálogos Configuráveis

## Objetivo

Permitir que o administrador configure prioridades, status de chamado, categorias e motivos de pendência sem necessidade de código. Os valores padrão devem ser provisionados automaticamente em cada tenant novo.

## Escopo

- CRUD de `priorities` (prioridades): Baixa, Média, Alta, Crítica — padrão editável.
- CRUD de `statuses` (status de chamado): Novo, Em Atendimento, Pendente, Solucionado, Fechado — com flags comportamentais.
- CRUD de `categories` (categorias de chamado): livre configuração.
- CRUD de `pending_reasons` (motivos de pendência): livre configuração.
- Seed de valores padrão no provisionamento de cada tenant.
- Proteção de inativação/exclusão de itens em uso.

## Fora do Escopo

- Lógica de transição de chamados (P09 — a máquina de estados é invariante de código; o catálogo apenas configura rótulos, ordem e flags).
- Aplicação de SLA por prioridade (P12).
- Telas de admin consolidadas (P18 — estas telas serão integradas ao console de administração).

## Dependências

- **P01** (Multi-Tenancy) — BaseRepository.
- **P04** (Usuários e Permissões) — `require_permission("admin:config")`.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `priorities` | Nova tabela |
| `statuses` | Nova tabela |
| `categories` | Nova tabela |
| `pending_reasons` | Nova tabela |

### `priorities`
```
id           UUID, PK
tenant_id    UUID, FK → tenants, INDEX
name         String, NOT NULL           # ex.: "Alta"
code         String, NOT NULL           # ex.: "high" — usado internamente
color        String, nullable           # ex.: "#FF5733" para UI
order        Integer, NOT NULL          # ordem de exibição
is_default   Boolean, DEFAULT false     # marcador dos valores padrão do sistema
is_active    Boolean, DEFAULT true
              UNIQUE(tenant_id, code)
```

### `statuses`
```
id                  UUID, PK
tenant_id           UUID, FK → tenants, INDEX
name                String, NOT NULL         # ex.: "Em Atendimento"
code                String, NOT NULL         # ex.: "in_progress"
order               Integer, NOT NULL
requires_reason     Boolean, DEFAULT false   # Pendente = true
requires_solution   Boolean, DEFAULT false   # Solucionado = true
is_terminal         Boolean, DEFAULT false   # Fechado = true
is_default          Boolean, DEFAULT false
is_active           Boolean, DEFAULT true
                     UNIQUE(tenant_id, code)
```

### `categories`
```
id          UUID, PK
tenant_id   UUID, FK → tenants, INDEX
name        String, NOT NULL
              UNIQUE(tenant_id, name)
description String, nullable
is_active   Boolean, DEFAULT true
```

### `pending_reasons`
```
id          UUID, PK
tenant_id   UUID, FK → tenants, INDEX
name        String, NOT NULL
              UNIQUE(tenant_id, name)
description String, nullable
is_active   Boolean, DEFAULT true
```

## APIs Necessárias

### Prioridades
| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/catalog/priorities` | Listar prioridades | `ticket:read` |
| POST | `/api/v1/catalog/priorities` | Criar prioridade | `admin:config` |
| PATCH | `/api/v1/catalog/priorities/{id}` | Editar prioridade | `admin:config` |
| POST | `/api/v1/catalog/priorities/{id}/deactivate` | Desativar | `admin:config` |

### Status
| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/catalog/statuses` | Listar status | `ticket:read` |
| PATCH | `/api/v1/catalog/statuses/{id}` | Editar nome/ordem/cor | `admin:config` |

*Nota: status não são criados ou excluídos pelo admin — apenas editados. O fluxo é invariante de código.*

### Categorias
| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/catalog/categories` | Listar categorias | `ticket:read` |
| POST | `/api/v1/catalog/categories` | Criar categoria | `admin:config` |
| PATCH | `/api/v1/catalog/categories/{id}` | Editar | `admin:config` |
| POST | `/api/v1/catalog/categories/{id}/deactivate` | Desativar | `admin:config` |

### Motivos de Pendência
| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/catalog/pending-reasons` | Listar motivos | `ticket:transition` |
| POST | `/api/v1/catalog/pending-reasons` | Criar motivo | `admin:config` |
| PATCH | `/api/v1/catalog/pending-reasons/{id}` | Editar | `admin:config` |
| POST | `/api/v1/catalog/pending-reasons/{id}/deactivate` | Desativar | `admin:config` |

## Telas Necessárias

Telas de gestão de cada catálogo — serão integradas ao Console de Administração (P18). Cada tela segue o padrão: lista com ações inline de editar/desativar + formulário de criação/edição.

## Regras de Negócio

1. **Seed padrão:** ao provisionar um tenant, os valores padrão abaixo são inseridos automaticamente:
   - Prioridades: Baixa (`low`), Média (`medium`), Alta (`high`), Crítica (`critical`).
   - Status: Novo (`new`), Em Atendimento (`in_progress`), Pendente (`pending`, `requires_reason=true`), Solucionado (`resolved`, `requires_solution=true`), Fechado (`closed`, `is_terminal=true`).
2. **Status — imutabilidade do fluxo:** o código (`code`) e as flags comportamentais (`requires_reason`, `requires_solution`, `is_terminal`) dos status padrão não podem ser alterados pelo admin. Apenas `name`, `color` e `order` são editáveis.
3. **Status — criação proibida pelo admin:** admin não pode criar novos status — o fluxo de chamado é definido pelo sistema.
4. **Itens em uso:** prioridade, categoria ou motivo de pendência referenciado por chamado ativo → inativação exibe aviso (não bloqueia).
5. **Código interno:** o campo `code` de prioridades e status é definido pelo sistema (não editável pelo admin) e usado pela máquina de estados e pelo motor de SLA.

## Critérios de Aceite

- [ ] Seed padrão criado ao provisionar tenant.
- [ ] Admin edita nome de prioridade → chamados passam a exibir o novo nome.
- [ ] Admin cria nova categoria → aparece no formulário de abertura de chamado.
- [ ] Admin desativa categoria → não aparece mais no formulário.
- [ ] Admin tenta criar/excluir status → recebe erro (não permitido).
- [ ] Admin tenta alterar flags comportamentais de status padrão → recebe erro.
- [ ] Motivo de pendência inativo não aparece ao colocar chamado em pendente.

## Estratégia de Testes

### Testes Unitários

- Seed: todos os valores padrão criados com os campos corretos.
- Validação: tentativa de alterar `code` ou flags de status → erro.
- Tentativa de criar/excluir status → erro.

### Testes de Integração

- Provisionamento de tenant → seed aplicado.
- `PATCH /catalog/priorities/{id}` → nome alterado.
- `POST /catalog/categories` → categoria criada; aparece em `GET`.
- `POST /catalog/categories/{id}/deactivate` → não aparece mais em listagem de ativos.
- `PATCH /catalog/statuses/{id}` tentando alterar `requires_reason` → 422.

### Testes E2E

- Admin acessa configurações → edita nome de prioridade "Alta" para "Urgente" → formulário de chamado exibe "Urgente".
- Admin cria categoria "Elétrica" → nova opção aparece na abertura de chamado.

## Riscos Técnicos

- **Acoplamento entre catálogo e máquina de estados (P09):** o status `code` é a âncora que liga os dois. Qualquer alteração nos códigos padrão quebra o fluxo. Mitigar com proteção explícita nos endpoints e testes de regressão.
- **Seed duplicado:** provisionar o mesmo tenant duas vezes não deve duplicar os valores padrão. Seed deve ser idempotente.

## Complexidade

**Média** — simples no CRUD, mas requer cuidado no contrato entre catálogo e máquina de estados.

## Prioridade

**Alta**

## Branch

`feature/007-catalogos-configuraveis`
