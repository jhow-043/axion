---
id: P10
slug: timeline
status: done
version: 1.0.0
owner: jhowworks
depends_on: [P01, P04, P09]
satisfies: [RF-100, RF-101]
adrs: [ADR-0001, ADR-0002]
branch: feature/010-timeline
last_updated: 2026-06-01
---

# P10 — Timeline do Chamado

## Objetivo

Registrar e exibir a linha do tempo completa de cada chamado, capturando todos os eventos relevantes de forma imutável e cronológica. A timeline é o mecanismo de auditoria operacional do chamado — diferente de P17 (auditoria administrativa).

## Escopo

- Entidade `ticket_events` (append-only): persistência de todos os eventos do chamado.
- Tipos de evento suportados: criação, mudança de status, comentário, anexo, troca de responsável, pendência (com motivo), solução registrada, pedido de validação, validação aprovada, validação rejeitada, encerramento, auto-fechamento.
- Interface `timeline_service.record_event()`: chamada por P09, P11, P12, P13 para registrar eventos.
- API de leitura da timeline com paginação.
- Componente visual de timeline no frontend (exibido no detalhe do chamado).

## Fora do Escopo

- Produção dos eventos — cada módulo origem chama `record_event()`; P10 apenas persiste e expõe.
- Comentários de texto (persistência em `ticket_comments` de P09; o evento de timeline apenas referencia o comentário).
- Auditoria administrativa do sistema (P17).

## Dependências

- **P09** (Chamados) — origem principal dos eventos; P10 é chamado por P09 e pelos demais módulos.
- **P11**, **P12**, **P13** — também chamam `record_event()` para seus respectivos eventos.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `ticket_events` | Nova tabela (append-only) |

### `ticket_events`
```
id          UUID, PK
tenant_id   UUID, FK → tenants, INDEX
ticket_id   UUID, FK → tickets, INDEX
type        Enum(ver abaixo), NOT NULL
actor_id    UUID, FK → users, nullable    # null para eventos de sistema (auto-fechamento, job de SLA)
payload     JSONB, nullable               # dados específicos do tipo de evento
created_at  DateTime, NOT NULL, INDEX
```

### Tipos de evento (`type`)
```
ticket_created
status_changed          payload: { from_status, to_status }
comment_added           payload: { comment_id, preview }
attachment_added        payload: { attachment_id, filename }
assignee_changed        payload: { from_user_id, to_user_id }
team_changed            payload: { from_team_id, to_team_id }
pending_started         payload: { reason_id, reason_name }
solution_recorded       payload: { solution_id }
validation_requested    payload: { validation_id, expires_at }
validation_approved     payload: { validated_by }
validation_rejected     payload: { rejected_by, reason }
ticket_closed           payload: { closed_by, method: "user" | "auto" }
sla_attendance_breached payload: { sla_policy_id }
sla_resolution_breached payload: { sla_policy_id }
```

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/tickets/{id}/timeline` | Listar eventos da timeline (paginado) | `ticket:read` + participante |

### Resposta de `GET /api/v1/tickets/{id}/timeline`
```json
{
  "total": 12,
  "page": 1,
  "page_size": 50,
  "items": [
    {
      "id": "uuid",
      "type": "status_changed",
      "actor": { "id": "uuid", "name": "João Silva" },
      "payload": { "from_status": "new", "to_status": "in_progress" },
      "created_at": "2024-01-15T09:00:00Z"
    }
  ]
}
```

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Componente Timeline | Exibido no detalhe do chamado; lista de eventos em ordem cronológica com ícone por tipo, ator e timestamp; suporte a paginação/scroll infinito |

## Regras de Negócio

1. **Imutabilidade:** eventos nunca são editados ou excluídos. A tabela é estritamente append-only. Nenhum endpoint de atualização ou exclusão de eventos é exposto.
2. **Ordenação:** sempre cronológica (`created_at ASC`). A API deve garantir essa ordenação independentemente da paginação.
3. **Ator nulo:** eventos gerados por jobs automáticos (auto-fechamento, alertas de SLA) têm `actor_id = null`; a UI exibe "Sistema" nesse caso.
4. **Payload tipado:** cada tipo de evento tem um schema de payload definido e validado na interface `record_event()`. Payload `null` é permitido para eventos sem dados adicionais (ex.: `ticket_created`).
5. **Visibilidade:** mesmas regras de acesso que o chamado — participantes podem ver a timeline; quem não tem acesso ao chamado, não tem acesso à timeline.
6. **Paginação:** padrão `page_size=50`; a timeline completa pode ser longa — suporte a scroll infinito no frontend.

## Interface `timeline_service.record_event()`

```python
# Contrato da interface (não é código — apenas especificação)
record_event(
    ticket_id: UUID,
    event_type: EventType,
    actor_id: UUID | None,
    payload: dict | None = None
) -> TicketEvent
```

Chamado de forma síncrona dentro da mesma transação do banco pelo módulo de origem, garantindo que o evento nunca seja perdido se a ação for confirmada.

## Critérios de Aceite

- [ ] `record_event()` persiste o evento com tipo, ator e payload corretos.
- [ ] `GET /tickets/{id}/timeline` retorna eventos em ordem cronológica.
- [ ] Evento de `ticket_created` gerado na criação do chamado.
- [ ] Evento de `status_changed` gerado em cada transição.
- [ ] Evento de `comment_added` gerado ao comentar.
- [ ] Evento de `attachment_added` gerado ao anexar (integração com P11).
- [ ] Evento de `ticket_closed` com método `"auto"` gerado pelo job de auto-fechamento (P13).
- [ ] Nenhum endpoint de edição ou exclusão de eventos está exposto.
- [ ] Usuário sem acesso ao chamado → 403 ou 404 na timeline.

## Estratégia de Testes

### Testes Unitários

- `record_event()`: serialização correta de cada tipo de payload.
- Ordenação: múltiplos eventos → ordem cronológica garantida.
- Validação de payload por tipo de evento (schema correto).

### Testes de Integração

- Criar chamado → `ticket_created` persistido.
- Transicionar status → `status_changed` persistido com `from/to` corretos.
- Comentar → `comment_added` persistido.
- `GET /timeline` → retorna todos os eventos em ordem.
- `GET /timeline` de não-participante → 403/404.

### Testes E2E

- Abrir chamado → assumir → colocar em pendente → solucionar → aprovar → timeline exibe todos os marcos em ordem com atores corretos.
- Auto-fechamento (P13) → último evento da timeline é `ticket_closed` com método `"auto"`.

## Riscos Técnicos

- **Volume de eventos:** chamados longos podem ter dezenas de eventos. Índice em `(ticket_id, created_at)` é essencial.
- **Payload heterogêneo:** JSONB é flexível mas requer validação de schema no serviço para evitar dados inconsistentes. Considerar `check constraints` ou validação Pydantic na interface.
- **Atomicidade:** `record_event()` deve ser chamado dentro da mesma transação da ação que o originou. Se chamar de forma assíncrona, há risco de o evento ser perdido em caso de rollback.

## Complexidade

**Média**

## Prioridade

**Alta**

## Branch

`feature/010-timeline`
