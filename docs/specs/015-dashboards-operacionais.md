---
id: P15
slug: dashboards-operacionais
status: done
version: 1.0.0
owner: jhowworks
depends_on: [P01, P04, P09, P12]
satisfies: [RF-150, RF-151]
adrs: [ADR-0001, ADR-0002]
branch: feature/015-dashboards-operacionais
last_updated: 2026-06-05
---

# P15 — Dashboards Operacionais (Técnico & Supervisor)

## Objetivo

Fornecer visões de trabalho diário para técnicos e supervisores: o técnico vê seus chamados e SLAs; o supervisor vê a operação das equipes, filas por equipe, SLAs e um **Kanban** interativo por status que permite transicionar chamados via drag-and-drop.

## Escopo

- **Dashboard do Técnico:** chamados atribuídos ao usuário por status, pendências, SLAs em risco.
- **Dashboard do Supervisor:** visão operacional com contagens por status e equipe, SLAs em risco da equipe, filas por equipe.
- **Kanban do Supervisor:** board com colunas por status; cards de chamados arrastáveis que disparam transições de status válidas.
- Endpoints de agregação dedicados (leitura otimizada).
- Filtros por equipe, período e prioridade.

## Fora do Escopo

- Indicadores gerenciais e relatórios históricos (P16).
- Dashboard do Solicitante (apenas lista de chamados com filtro — coberto pela lista de P09).
- Configuração de dashboards personalizados (futuro).

## Dependências

- **P01** (Multi-Tenancy).
- **P04** (Usuários e Permissões) — `require_permission("dashboard:operational")`.
- **P05** (Equipes) — filas e filtros por equipe.
- **P09** (Chamados) — fonte dos dados; transição de status via Kanban reutiliza a lógica de P09.
- **P12** (SLA) — `sla_trackers` para chamados em risco.

## Entidades Impactadas

Nenhuma nova entidade. Leitura agregada de `tickets`, `sla_trackers`, `teams`, `users`.

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/dashboards/technician` | Dashboard do técnico | `dashboard:operational` |
| GET | `/api/v1/dashboards/supervisor` | Dashboard do supervisor | `dashboard:operational` (papel Supervisor+) |
| GET | `/api/v1/dashboards/board` | Dados do Kanban por status | `dashboard:operational` (papel Supervisor+) |

### Resposta de `GET /dashboards/technician`
```json
{
  "assigned_tickets": {
    "total": 12,
    "by_status": {
      "new": 2,
      "in_progress": 7,
      "pending": 3
    }
  },
  "sla_at_risk": [
    { "ticket_id": "uuid", "title": "...", "sla_type": "resolution", "due_at": "..." }
  ],
  "sla_breached": [
    { "ticket_id": "uuid", "title": "...", "sla_type": "attendance", "breached_at": "..." }
  ]
}
```

### Resposta de `GET /dashboards/supervisor`

Parâmetros: `team_id` (opcional), `priority_id` (opcional), `date_from`, `date_to`.

```json
{
  "summary": {
    "total_open": 45,
    "by_status": { "new": 5, "in_progress": 28, "pending": 12 },
    "by_priority": { "critical": 3, "high": 10, "medium": 22, "low": 10 }
  },
  "teams": [
    {
      "team_id": "uuid",
      "team_name": "Elétrica",
      "total_open": 15,
      "sla_at_risk": 3,
      "sla_breached": 1
    }
  ],
  "sla_summary": {
    "attendance_compliance_pct": 92,
    "resolution_compliance_pct": 78
  }
}
```

### Resposta de `GET /dashboards/board`

Parâmetros: `team_id` (opcional), `assignee_id` (opcional), `priority_id` (opcional).

```json
{
  "columns": [
    {
      "status_code": "new",
      "status_name": "Novo",
      "tickets": [
        { "id": "uuid", "title": "...", "priority": "high", "assignee": null, "sla_status": "running" }
      ]
    }
  ]
}
```

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Dashboard Técnico | Cards de resumo por status, lista de SLAs em risco e vencidos, link para lista filtrada |
| Dashboard Supervisor | Cards de resumo geral, tabela de filas por equipe, percentuais de SLA |
| Kanban | Board com colunas de status; cards arrastáveis com drag-and-drop (dnd-kit); transição ao soltar |

## Regras de Negócio

1. **Visibilidade do técnico:** vê apenas chamados onde é `assignee_id`.
2. **Visibilidade do supervisor:** vê chamados das equipes que supervisiona (equipes onde é membro e tem papel Supervisor). Admin vê todos.
3. **Kanban — transição via drag:** arrastar um card para outra coluna dispara `POST /tickets/{id}/transition` (P09) com as regras normais de validação. Se a transição for inválida (ex.: arrastar para "Fechado" diretamente), o card retorna à posição original com mensagem de erro.
4. **Kanban — colunas:** exibir colunas na ordem configurada em `statuses.order` (P07). Não exibir coluna "Fechado" no Kanban operacional (chamados fechados ficam no histórico).
5. **Dados em tempo quase real:** o dashboard não precisa de atualização em streaming; um `refetch` a cada 60 segundos com TanStack Query é suficiente. O Kanban pode ser atualizado por WebSocket se o usuário estiver na tela (evolução).
6. **Percentual de SLA:** `compliance_pct = chamados_dentro_do_prazo / total_chamados_com_sla × 100` no período.

## Critérios de Aceite

- [ ] `GET /dashboards/technician` retorna apenas chamados do técnico autenticado.
- [ ] Supervisor com equipe X → `GET /dashboards/supervisor` mostra dados apenas das suas equipes.
- [ ] Kanban exibe chamados agrupados por status na ordem correta.
- [ ] Arrastar card para coluna válida → status transicionado via P09; card permanece na nova coluna.
- [ ] Arrastar card para transição inválida → card retorna; erro exibido ao usuário.
- [ ] SLAs em risco e vencidos aparecem corretamente (integração com P12).
- [ ] Técnico não consegue acessar dashboard do supervisor → 403.

## Estratégia de Testes

### Testes Unitários

- Cálculo de percentual de SLA.
- Filtro de visibilidade: técnico → apenas seus chamados; supervisor → apenas suas equipes.
- Agrupamento de tickets por status para o board.

### Testes de Integração

- `GET /dashboards/technician` com dados semeados → contagens corretas.
- `GET /dashboards/supervisor` com filtro de equipe → apenas dados da equipe filtrada.
- `GET /dashboards/board` → colunas com tickets corretos.
- Drag-and-drop simulado: `POST /tickets/{id}/transition` via board → status alterado.

### Testes E2E

- Supervisor arrasta card de "Novo" para "Em Atendimento" → card permanece na coluna; lista do técnico atualiza.
- Supervisor arrasta card para "Fechado" diretamente → card retorna; mensagem de erro.
- Dashboard do técnico exibe SLA em risco com prazo correto.

## Riscos Técnicos

- **Performance das agregações:** queries com múltiplos JOINs e agrupamentos em tabelas grandes. Usar índices compostos em `tickets(tenant_id, status_id, assignee_id, team_id)` e considerar views materializadas se necessário.
- **Kanban e concorrência:** dois supervisores arrastando o mesmo card simultaneamente. A primeira transição confirmada pelo backend prevalece; a segunda verifica o status atual e pode retornar erro de transição inválida.
- **Drag-and-drop em mobile:** dnd-kit suporta touch, mas testar em dispositivos tácteis (ambiente industrial frequentemente usa tablets).

## Complexidade

**Média** — queries de agregação e o Kanban com drag-and-drop são os pontos de maior atenção.

## Prioridade

**Alta**

## Branch

`feature/015-dashboards-operacionais`
