---
id: P08
slug: equipamentos
status: done
version: 1.0.0
owner: jhowworks
depends_on: [P01, P04, P06, P07]
satisfies: [RF-070, RF-071]
adrs: [ADR-0001, ADR-0002]
branch: feature/008-equipamentos
last_updated: 2026-06-01
---

# P08 — Equipamentos

## Objetivo

Cadastrar e gerenciar equipamentos industriais com seus atributos obrigatórios e opcionais, mantendo o histórico de chamados vinculados a cada equipamento como referência rastreável.

## Escopo

- CRUD de equipamentos: criar, listar, detalhar, editar, ativar/desativar.
- Campos obrigatórios: nome, código/identificação, setor, status (Ativo/Inativo).
- Campos opcionais: fabricante, modelo, número de série, observações.
- Unicidade de código por tenant.
- Página de detalhe com histórico de chamados vinculados (leitura paginada).
- Telas de lista, formulário e detalhe.

## Fora do Escopo

- Abertura de chamados (P09) — o detalhe exibe o histórico de chamados existentes, mas a criação é responsabilidade de P09.
- Ranking de equipamentos mais problemáticos (P16 — Dashboard Gerencial).
- Plano de manutenção preventiva (futuro).
- QR Code / tag de identificação (futuro).

## Dependências

- **P01** (Multi-Tenancy) — BaseRepository.
- **P04** (Usuários e Permissões) — `require_permission("equipment:manage")` e `equipment:read`.
- **P06** (Setores e Locais) — FK para `sectors`.
- **P07** (Catálogos) — nenhuma dependência direta de catálogo, mas o setor vem de P06 que depende de P07.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `equipments` | Nova tabela |

### `equipments`
```
id              UUID, PK
tenant_id       UUID, FK → tenants, INDEX
code            String, NOT NULL
                 UNIQUE(tenant_id, code)
name            String, NOT NULL
sector_id       UUID, FK → sectors, NOT NULL
status          Enum('active', 'inactive'), DEFAULT 'active'
manufacturer    String, nullable
model           String, nullable
serial_number   String, nullable
notes           Text, nullable
created_at      DateTime
updated_at      DateTime
created_by      UUID, FK → users
```

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/equipments` | Listar equipamentos (paginado, filtros) | `equipment:read` |
| POST | `/api/v1/equipments` | Criar equipamento | `equipment:manage` |
| GET | `/api/v1/equipments/{id}` | Detalhar equipamento | `equipment:read` |
| PATCH | `/api/v1/equipments/{id}` | Editar equipamento | `equipment:manage` |
| POST | `/api/v1/equipments/{id}/deactivate` | Desativar equipamento | `equipment:manage` |
| POST | `/api/v1/equipments/{id}/activate` | Reativar equipamento | `equipment:manage` |
| GET | `/api/v1/equipments/{id}/tickets` | Histórico de chamados (paginado) | `equipment:read` |

### Filtros em `GET /api/v1/equipments`

- `search` (nome ou código)
- `sector_id`
- `status` (active, inactive)
- `page`, `page_size`

### Resposta de `GET /api/v1/equipments/{id}/tickets`

Lista paginada de chamados com: id, título, status, prioridade, data de abertura, responsável. Ordenado por `created_at DESC`.

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Lista de Equipamentos | Tabela paginada com filtros por nome/código/setor/status |
| Formulário de Equipamento | Criar/editar com campos obrigatórios e opcionais |
| Detalhe do Equipamento | Dados completos + histórico de chamados vinculados |

## Regras de Negócio

1. **Código único por tenant:** `UNIQUE(tenant_id, code)`.
2. **Setor obrigatório:** o setor deve existir, pertencer ao mesmo tenant e estar ativo.
3. **Equipamento inativo** não pode ser alvo de novo chamado industrial (validação aplicada em P09 — a spec de Equipamentos mantém apenas o flag).
4. **Histórico de chamados:** somente leitura, ordenado por data decrescente. Inclui todos os chamados vinculados independentemente do status.
5. **Desativação:** não encerra chamados abertos vinculados ao equipamento. Exibir aviso se existirem chamados abertos.

## Critérios de Aceite

- [ ] CRUD de equipamentos com isolamento de tenant.
- [ ] Código duplicado no mesmo tenant → erro de validação.
- [ ] Setor inativo ou de outro tenant → erro de validação.
- [ ] `GET /equipments/{id}/tickets` retorna histórico paginado ordenado por data.
- [ ] Equipamento inativo não aparece na seleção de chamados industriais (validação em P09).
- [ ] Telas de lista, formulário e detalhe funcionais.
- [ ] Filtros de listagem funcionam corretamente.

## Estratégia de Testes

### Testes Unitários

- Validação de código único por tenant.
- Validação de setor ativo e do mesmo tenant.

### Testes de Integração

- `POST /equipments` → equipamento criado com todos os campos corretos.
- `POST /equipments` com código duplicado → 422.
- `POST /equipments` com setor inativo → 422.
- `GET /equipments` → lista apenas equipamentos do tenant corrente.
- `GET /equipments` com filtros → resultados corretos.
- `GET /equipments/{id}/tickets` → lista vazia para equipamento novo; lista correta após chamados criados (integração com P09).

### Testes E2E

- Admin cadastra equipamento completo (obrigatórios + opcionais) → aparece na lista.
- Admin abre chamado industrial para o equipamento → histórico exibe o chamado.
- Admin desativa equipamento → não aparece mais na seleção de abertura de chamado industrial.

## Riscos Técnicos

- **Baixo.** Módulo de cadastro sem regras complexas.
- O endpoint de histórico de chamados (`/tickets`) requer join com a tabela de chamados (P09). Durante o desenvolvimento isolado, pode ser retornado vazio ou mockado até que P09 esteja disponível em `develop`.

## Complexidade

**Baixa**

## Prioridade

**Alta**

## Branch

`feature/008-equipamentos`
