---
id: P09
slug: chamados-workflow
status: done
version: 1.0.0
owner: jhowworks
depends_on: [P01, P04, P05, P06, P07, P08, P10, P14]
satisfies: [RF-080, RF-081, RF-082, RF-083, RF-084, RF-085, RF-086, RF-087, RF-088, RF-089, RF-090, RF-091, RF-092, RF-041, RF-052, RF-071]
adrs: [ADR-0001, ADR-0002, ADR-0003]
branch: feature/009-chamados-workflow
last_updated: 2026-06-01
---

# P09 — Chamados: Núcleo & Workflow

## Objetivo

Implementar o módulo central da plataforma: abertura de chamados (industrial e predial), controle do fluxo de status por máquina de estados, atribuição de responsável, observadores, comentários e direcionamento a equipes. É o coração do sistema — todos os módulos de SLA, timeline, notificações e dashboards dependem dos eventos emitidos aqui.

## Escopo

- Criação de chamados com distinção de tipo:
  - **Industrial:** vinculado obrigatoriamente a um equipamento ativo.
  - **Predial:** vinculado obrigatoriamente a um local ativo.
- Campos: título, descrição, prioridade, categoria, equipe de destino.
- Listagem de chamados com filtros avançados.
- Detalhe do chamado.
- **Máquina de estados** com todas as transições válidas (ver abaixo).
- Assumir chamado (define responsável + move para Em Atendimento).
- Colocar em Pendente com motivo obrigatório.
- Registrar solução ao marcar Solucionado (descrição obrigatória).
- Observadores: adicionar/remover; recebem notificações e podem comentar.
- Comentários: qualquer participante (solicitante, responsável, observador) pode comentar.
- Cada ação registra evento na Timeline (P10) e notificação (P14).

## Fora do Escopo

- Persistência da timeline (P10 — responsável por `ticket_events`).
- Cálculo e controle de SLA (P12).
- Validação do solicitante / encerramento / auto-fechamento (P13).
- Upload de anexos (P11).
- Envio de notificações (P14 — P09 apenas emite o sinal; P14 processa).

## Dependências

- **P01** (Multi-Tenancy).
- **P04** (Usuários e Permissões).
- **P05** (Equipes).
- **P06** (Setores/Locais).
- **P07** (Catálogos — prioridades, status, categorias, motivos de pendência).
- **P08** (Equipamentos).
- **P10** (Timeline) — P09 chama `timeline_service.record_event()` a cada ação. Coordenar interface antes de implementar.
- **P14** (Notificações) — P09 chama `notification_service.notify()`. Coordenar interface antes de implementar.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `tickets` | Nova tabela principal |
| `ticket_observers` | Nova tabela (N:N tickets × users) |
| `ticket_comments` | Nova tabela |
| `solutions` | Nova tabela (descrição de solução) |

### `tickets`
```
id                  UUID, PK
tenant_id           UUID, FK → tenants, INDEX
type                Enum('industrial', 'predial'), NOT NULL
title               String, NOT NULL
description         Text, NOT NULL
priority_id         UUID, FK → priorities, NOT NULL
status_id           UUID, FK → statuses, NOT NULL
category_id         UUID, FK → categories, nullable
equipment_id        UUID, FK → equipments, nullable     # NOT NULL se type='industrial'
location_id         UUID, FK → locations, nullable      # NOT NULL se type='predial'
team_id             UUID, FK → teams, nullable
requester_id        UUID, FK → users, NOT NULL          # solicitante
assignee_id         UUID, FK → users, nullable          # técnico responsável
# timestamps de transição (para SLA e métricas)
assigned_at         DateTime, nullable                  # quando foi assumido
resolved_at         DateTime, nullable
closed_at           DateTime, nullable
created_at          DateTime
updated_at          DateTime
INDEX(tenant_id, status_id)
INDEX(tenant_id, assignee_id)
INDEX(tenant_id, team_id)
INDEX(tenant_id, equipment_id)
```

### `ticket_observers`
```
id          UUID, PK
tenant_id   UUID, FK → tenants, INDEX
ticket_id   UUID, FK → tickets
user_id     UUID, FK → users
added_at    DateTime
             UNIQUE(ticket_id, user_id)
```

### `ticket_comments`
```
id          UUID, PK
tenant_id   UUID, FK → tenants, INDEX
ticket_id   UUID, FK → tickets
author_id   UUID, FK → users
content     Text, NOT NULL
created_at  DateTime
updated_at  DateTime
```

### `solutions`
```
id              UUID, PK
tenant_id       UUID, FK → tenants, INDEX
ticket_id       UUID, FK → tickets, UNIQUE
description     Text, NOT NULL
resolved_by     UUID, FK → users
resolved_at     DateTime
```

## Máquina de Estados

```
Novo (new)
  └──► Em Atendimento (in_progress)   [assumir — define responsável; encerra SLA de Atendimento]
         ├──► Pendente (pending)       [exige motivo; pausa SLA de Resolução]
         │      └──► Em Atendimento   [retomar; recalcula SLA de Resolução]
         └──► Solucionado (resolved)  [exige descrição de solução; inicia prazo de validação]
                ├──► Em Atendimento   [solicitante rejeita]
                └──► Fechado (closed) [solicitante aprova ou auto-fechamento]
```

Transições proibidas (exemplo): Novo→Fechado, Pendente→Solucionado (deve passar por Em Atendimento), Fechado→qualquer estado.

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| POST | `/api/v1/tickets` | Criar chamado | `ticket:create` |
| GET | `/api/v1/tickets` | Listar chamados (filtros, paginado) | `ticket:read` |
| GET | `/api/v1/tickets/{id}` | Detalhar chamado | `ticket:read` |
| POST | `/api/v1/tickets/{id}/assign` | Assumir chamado (define responsável + Em Atendimento) | `ticket:assign` |
| POST | `/api/v1/tickets/{id}/transition` | Transição de status | `ticket:transition` |
| POST | `/api/v1/tickets/{id}/observers` | Adicionar observador | `ticket:read` (participante) |
| DELETE | `/api/v1/tickets/{id}/observers/{user_id}` | Remover observador | `ticket:transition` |
| POST | `/api/v1/tickets/{id}/comments` | Adicionar comentário | `ticket:read` (participante) |
| PATCH | `/api/v1/tickets/{id}/comments/{cid}` | Editar comentário (próprio, dentro de janela) | participante |
| GET | `/api/v1/tickets/{id}/comments` | Listar comentários | `ticket:read` |

### Body de `POST /api/v1/tickets`
```json
{
  "type": "industrial",
  "title": "Falha no motor da bomba B-01",
  "description": "Motor travando ao iniciar...",
  "priority_id": "uuid",
  "category_id": "uuid",
  "equipment_id": "uuid",
  "team_id": "uuid"
}
```

### Body de `POST /api/v1/tickets/{id}/transition`
```json
{
  "to_status": "pending",
  "pending_reason_id": "uuid",   // obrigatório se to_status = "pending"
  "solution_description": "..."  // obrigatório se to_status = "resolved"
}
```

### Filtros em `GET /api/v1/tickets`
- `type`, `status_code`, `priority_id`, `team_id`, `assignee_id`, `requester_id`, `equipment_id`, `location_id`, `search` (título), `created_from`, `created_to`, `page`, `page_size`.
- **Solicitante:** vê apenas chamados onde é `requester_id` ou `observer`.

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Abertura de Chamado | Formulário com tipo (industrial/predial), campos e upload de evidências (integrado com P11) |
| Lista de Chamados | Tabela paginada com filtros; ações rápidas por papel |
| Detalhe do Chamado | Dados + status atual + ações de fluxo + comentários + timeline (P10) + anexos (P11) |

## Regras de Negócio

1. **Tipo industrial:** `equipment_id` obrigatório; equipamento deve estar ativo no mesmo tenant.
2. **Tipo predial:** `location_id` obrigatório; local deve estar ativo no mesmo tenant.
3. **Status inicial:** todo chamado começa como `new`.
4. **Assumir = Em Atendimento:** a ação de assumir define o `assignee_id` e move para `in_progress`. Apenas técnicos com `ticket:assign` podem assumir.
5. **Pendente exige motivo:** `pending_reason_id` é obrigatório. O motivo deve estar ativo no tenant.
6. **Solucionado exige descrição:** `solution_description` é obrigatória ao marcar como `resolved`. Cria registro em `solutions`.
7. **Observador:** pode comentar mas não pode realizar ações de transição. Solicitante e responsável são notificados automaticamente (não precisam ser observadores explicitamente).
8. **Comentário:** qualquer participante (solicitante, responsável, observador) pode comentar. Edição permitida apenas pelo autor em janela de 15 minutos.
9. **Fechado é terminal:** chamado `closed` não pode mais ser transitado.
10. **Cada ação emite:** evento de timeline (`ticket_events` via P10) + notificação (`notifications` via P14).
11. **Visibilidade:** Solicitante vê apenas chamados onde é requester ou observer. Técnico vê chamados da sua equipe e os atribuídos a ele. Supervisor e Admin veem todos.

## Critérios de Aceite

- [ ] Criar chamado industrial sem `equipment_id` → 422.
- [ ] Criar chamado predial sem `location_id` → 422.
- [ ] Criar chamado com equipamento inativo → 422.
- [ ] Chamado criado inicia com status `new`.
- [ ] Assumir chamado → status muda para `in_progress`; `assignee_id` e `assigned_at` preenchidos.
- [ ] Transition para `pending` sem `pending_reason_id` → 422.
- [ ] Transition para `resolved` sem `solution_description` → 422.
- [ ] Transition inválida (ex.: `closed` → `in_progress`) → 422.
- [ ] Comentário adicionado por participante → aparece em `GET /tickets/{id}/comments`.
- [ ] Comentário de não-participante → 403.
- [ ] Cada ação registra evento de timeline (verificar chamada ao `timeline_service`).
- [ ] Filtros de listagem retornam resultados corretos.
- [ ] Solicitante não vê chamados de outros solicitantes.

## Estratégia de Testes

### Testes Unitários

- Máquina de estados: todas as transições válidas retornam o próximo estado correto.
- Máquina de estados: todas as transições inválidas levantam exceção.
- Validação de tipo: industrial sem equipamento → erro; predial sem local → erro.
- Regra de visibilidade: solicitante filtrado apenas para seus chamados.

### Testes de Integração

- `POST /tickets` industrial → chamado criado com equipment_id e status `new`.
- `POST /tickets/{id}/assign` → status = `in_progress`, assignee_id preenchido.
- `POST /tickets/{id}/transition` `pending` com motivo → status = `pending`.
- `POST /tickets/{id}/transition` `pending` sem motivo → 422.
- `POST /tickets/{id}/transition` `resolved` com solução → `solutions` criado.
- `POST /tickets/{id}/transition` de `closed` → 422.
- Comentário de participante → 201; de não-participante → 403.
- Listagem com filtro de status → retorna apenas chamados no status correto.

### Testes E2E

- Solicitante abre chamado industrial → técnico assume → supervisor vê no dashboard.
- Técnico coloca em pendente com motivo → SLA pausado (via P12).
- Técnico registra solução → solicitante recebe notificação (via P14).
- Solicitante tenta transicionar status → 403.

## Riscos Técnicos

- **Coerência entre status configurável (P07) e máquina de estados:** a máquina usa `status.code` como âncora — se o código for alterado, o fluxo quebra. Proteger com validação no seed e ao editar status.
- **Concorrência em transições:** dois usuários tentando transicionar o mesmo chamado simultaneamente → usar lock otimista (versão ou `SELECT FOR UPDATE`).
- **Interface com P10 e P14:** estas dependências devem ter interface definida antes de P09 ser implementado. Usar padrão de "emitir evento interno" (lista de eventos a processar) que P10 e P14 registram/enviam assincronamente.
- **Volume de dados:** índices adequados em `tickets` para suportar os filtros complexos.

## Complexidade

**Alta** — módulo central com mais regras de negócio, mais dependências e maior impacto no sistema.

## Prioridade

**Crítica**

## Branch

`feature/009-chamados-workflow`
