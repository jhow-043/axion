---
id: P06
slug: setores-locais
status: done
version: 1.0.0
owner: jhowworks
depends_on: [P01, P04]
satisfies: [RF-050, RF-051, RF-052]
adrs: [ADR-0001, ADR-0002]
branch: feature/006-setores-locais
last_updated: 2026-06-01
---

# P06 — Setores e Locais Prediais

## Objetivo

Manter o cadastro de setores (unidade organizacional) e de locais prediais (alvo de chamados do tipo "Manutenção Predial"), garantindo que ambos estejam disponíveis para vinculação a equipamentos (P08) e chamados (P09).

## Escopo

- CRUD de setores: criar, listar, editar, ativar/desativar.
- CRUD de locais prediais: criar, listar, editar, ativar/desativar.
- Validação de unicidade de nome por tenant em cada entidade.
- Proteção de exclusão/inativação quando referenciado por outros registros.
- Telas de gerenciamento de setores e locais.

## Fora do Escopo

- Vínculo a equipamentos (P08).
- Vínculo a chamados (P09).
- Hierarquia de locais (andar → sala → etc.) — futuro.
- Mapa/planta baixa — futuro.

## Dependências

- **P01** (Multi-Tenancy) — BaseRepository e contexto de tenant.
- **P04** (Usuários e Permissões) — `require_permission("admin:config")` para gerenciamento.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `sectors` | Nova tabela |
| `locations` | Nova tabela |

### `sectors`
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

### `locations`
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

## APIs Necessárias

### Setores

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/sectors` | Listar setores | `equipment:read` ou `admin:config` |
| POST | `/api/v1/sectors` | Criar setor | `admin:config` |
| GET | `/api/v1/sectors/{id}` | Detalhar setor | `equipment:read` ou `admin:config` |
| PATCH | `/api/v1/sectors/{id}` | Editar setor | `admin:config` |
| POST | `/api/v1/sectors/{id}/deactivate` | Desativar setor | `admin:config` |

### Locais Prediais

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/locations` | Listar locais | `ticket:read` ou `admin:config` |
| POST | `/api/v1/locations` | Criar local | `admin:config` |
| GET | `/api/v1/locations/{id}` | Detalhar local | `ticket:read` ou `admin:config` |
| PATCH | `/api/v1/locations/{id}` | Editar local | `admin:config` |
| POST | `/api/v1/locations/{id}/deactivate` | Desativar local | `admin:config` |

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Lista de Setores | Tabela com nome, descrição e status; ações de editar/desativar |
| Formulário de Setor | Criar/editar: nome, descrição |
| Lista de Locais | Tabela com nome, descrição e status; ações de editar/desativar |
| Formulário de Local | Criar/editar: nome, descrição |

*Estas telas serão integradas no Console de Administração (P18).*

## Regras de Negócio

1. **Nome único por tenant:** `UNIQUE(tenant_id, name)` em cada tabela.
2. **Proteção de inativação:** setor referenciado por equipamento ativo deve exibir aviso (não bloqueia — permite inativar, mas informa o impacto).
3. **Proteção de inativação:** local referenciado por chamado aberto deve exibir aviso (não bloqueia — permite inativar, mas informa o impacto).
4. **Local/setor inativo:** não aparece nas opções de seleção em formulários de equipamentos e chamados.
5. **Reativação:** um setor ou local inativo pode ser reativado a qualquer momento.

## Critérios de Aceite

- [ ] CRUD de setores com isolamento de tenant.
- [ ] CRUD de locais com isolamento de tenant.
- [ ] Nome duplicado no mesmo tenant → erro de validação.
- [ ] Setor inativo não aparece na seleção de equipamentos.
- [ ] Local inativo não aparece na seleção de chamados prediais.
- [ ] Inativar setor com equipamentos ativos → aviso exibido; inativação prossegue.
- [ ] Telas de lista e formulário funcionais para setores e locais.

## Estratégia de Testes

### Testes Unitários

- Unicidade de nome por tenant (service).
- Lógica de aviso de uso referenciado.

### Testes de Integração

- `POST /sectors` → setor criado com tenant_id correto.
- `POST /sectors` com nome duplicado → 422.
- `GET /sectors` → lista apenas setores do tenant corrente.
- `POST /sectors/{id}/deactivate` → is_active = false.
- Equivalente para `/locations`.

### Testes E2E

- Admin cria setor e local → aparecem nos formulários de equipamento e chamado.
- Admin desativa local → não aparece mais no formulário de abertura de chamado predial.

## Riscos Técnicos

- **Baixo.** Módulo simples de cadastro.
- Atenção à consistência na filtragem de ativos nos selects dos formulários de outros módulos (P08, P09).

## Complexidade

**Baixa**

## Prioridade

**Alta**

## Branch

`feature/006-setores-locais`
