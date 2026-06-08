---
id: P14
slug: notificacoes
status: done
version: 1.0.0
owner: jhowworks
depends_on: [P01, P02, P04, P09, P12, P13]
satisfies: [RF-140, RF-141, RF-142, RF-143, RF-144, RF-145, RNF-DISP-003, RNF-DISP-004, RNF-INT-005]
adrs: [ADR-0001, ADR-0004]
branch: feature/014-notificacoes
last_updated: 2026-06-01
---

# P14 — Notificações (In-App + WebSocket + E-mail)

## Objetivo

Notificar participantes sobre eventos relevantes do chamado em dois canais: in-app (persistido + push via WebSocket) e e-mail (assíncrono via Celery/SMTP). As notificações são configuráveis por tipo e por usuário.

## Escopo

- Entidade `notifications`: persistência de cada notificação por destinatário.
- Serviço `notification_service.notify()`: interface chamada por P09, P12 e P13 com o evento e a lista de destinatários.
- Canal in-app: notificação persistida + push via WebSocket para usuários conectados.
- Canal e-mail: task Celery que envia e-mail via SMTP configurado.
- Resolução de destinatários por tipo de evento (solicitante, responsável, observadores, supervisor de equipe).
- Preferências de notificação por usuário (opt-out por tipo e/ou canal).
- Sino de notificações no frontend: contador de não-lidas, lista, marcar como lido.
- WebSocket de notificações: conexão por usuário autenticado; push em tempo real.

## Fora do Escopo

- SMS / push mobile (futuro).
- E-mail com template HTML avançado (texto simples por enquanto; HTML como evolução).
- Digest diário/semanal (futuro).
- Notificações fora do escopo de chamados (alertas de sistema, etc.) — futuro.

## Dependências

- **P01** (Multi-Tenancy).
- **P02** (Fundação Frontend) — cliente WebSocket base.
- **P04** (Usuários e Permissões).
- **P09**, **P12**, **P13** — emissores de eventos; chamam `notification_service.notify()`.
- Redis (broker Celery e pub/sub para broadcast WebSocket multi-instância).
- SMTP configurado no Docker Compose (Mailhog ou SMTP real).

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `notifications` | Nova tabela |
| `notification_preferences` | Nova tabela |

### `notifications`
```
id              UUID, PK
tenant_id       UUID, FK → tenants, INDEX
recipient_id    UUID, FK → users, INDEX
ticket_id       UUID, FK → tickets, nullable, INDEX
event_type      String, NOT NULL             # ex.: "ticket_assigned", "sla_breached"
title           String, NOT NULL
body            String, NOT NULL
is_read         Boolean, DEFAULT false
read_at         DateTime, nullable
email_sent      Boolean, DEFAULT false
email_sent_at   DateTime, nullable
created_at      DateTime, INDEX
```

### `notification_preferences`
```
id              UUID, PK
tenant_id       UUID, FK → tenants, INDEX
user_id         UUID, FK → users
                 UNIQUE(tenant_id, user_id, event_type)
event_type      String, NOT NULL
in_app_enabled  Boolean, DEFAULT true
email_enabled   Boolean, DEFAULT true
```

## Tipos de Evento e Destinatários Padrão

| Evento | Código | Destinatários |
|--------|--------|---------------|
| Novo chamado criado | `ticket_created` | Supervisores da equipe + admin |
| Chamado assumido | `ticket_assigned` | Solicitante + observadores |
| Mudança de status | `ticket_status_changed` | Solicitante + responsável + observadores |
| Comentário adicionado | `ticket_comment_added` | Solicitante + responsável + observadores (exceto o autor) |
| Solução registrada | `ticket_resolved` | Solicitante + observadores |
| Validação solicitada | `ticket_validation_requested` | Solicitante |
| Validação aprovada | `ticket_validation_approved` | Responsável + observadores |
| Validação rejeitada | `ticket_validation_rejected` | Responsável + observadores |
| Chamado fechado | `ticket_closed` | Solicitante + responsável + observadores |
| Auto-fechamento | `ticket_auto_closed` | Todos os participantes + supervisores da equipe |
| SLA atendimento em risco | `sla_attendance_at_risk` | Responsável + supervisores da equipe |
| SLA atendimento vencido | `sla_attendance_breached` | Responsável + supervisores da equipe |
| SLA resolução em risco | `sla_resolution_at_risk` | Responsável + supervisores da equipe |
| SLA resolução vencido | `sla_resolution_breached` | Responsável + supervisores da equipe |

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/notifications` | Listar notificações do usuário (paginado) | autenticado |
| POST | `/api/v1/notifications/{id}/read` | Marcar como lida | autenticado + dono |
| POST | `/api/v1/notifications/read-all` | Marcar todas como lidas | autenticado |
| GET | `/api/v1/notifications/preferences` | Ver preferências | autenticado |
| PATCH | `/api/v1/notifications/preferences` | Atualizar preferências | autenticado |
| WS | `/ws/notifications` | Canal de push de notificações | token na query string ou header |

### WebSocket — protocolo de mensagem (servidor → cliente)
```json
{
  "type": "notification",
  "data": {
    "id": "uuid",
    "event_type": "ticket_assigned",
    "title": "Chamado atribuído a você",
    "body": "O chamado #1234 foi atribuído a você.",
    "ticket_id": "uuid",
    "created_at": "2024-01-15T09:00:00Z"
  }
}
```

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Sino de Notificações | Ícone no topbar com contador de não-lidas; dropdown com lista recente |
| Página de Notificações | Lista paginada completa com filtro de lidas/não-lidas |
| Preferências de Notificação | Tabela de tipos × canais com toggle in-app/e-mail |

## Regras de Negócio

1. **In-app sempre persistido:** mesmo que o usuário tenha opt-out de e-mail, a notificação in-app é sempre salva.
2. **E-mail opt-out:** se `email_enabled = false` para o tipo de evento, a task de e-mail não é enfileirada.
3. **Push WebSocket:** se o usuário estiver conectado, a notificação é enviada imediatamente. Se não estiver, ela fica disponível via `GET /notifications` ao reconectar.
4. **Multi-instância:** o push WebSocket deve funcionar em ambientes com múltiplas instâncias do servidor API. Solução: Redis pub/sub — o servidor que processa o evento publica no canal Redis; todos os servidores assinam e enviam para suas conexões locais.
5. **E-mail assíncrono:** enfileirado como task Celery imediatamente após persistir a notificação. Retry automático (3 tentativas com backoff) em caso de falha SMTP.
6. **Resolução de destinatários:** feita dentro do `notification_service.notify()`, consultando os participantes do chamado e as preferências de cada um.
7. **Não notificar o autor:** quem realizou a ação não recebe notificação sobre ela (ex.: o técnico que comentou não recebe notificação de "comentário adicionado").
8. **Agrupamento:** se o mesmo evento gerar múltiplas notificações para o mesmo usuário em menos de 1 minuto, agrupar em uma (anti-flood) — registrar como evolução pós-P14.

## Interface `notification_service.notify()`

```
notify(
    event_type: str,
    ticket_id: UUID,
    actor_id: UUID,
    extra_recipients: list[UUID] = [],
    payload: dict = {}
) -> None
```

Chamado de forma síncrona (mas o envio de e-mail é assíncrono via task).

## Critérios de Aceite

- [ ] `notify()` chamado com evento → notificação persistida para cada destinatário.
- [ ] Push WebSocket recebido por usuário conectado no momento do evento.
- [ ] Usuário desconectado → notificação aparece em `GET /notifications` ao reconectar.
- [ ] `POST /notifications/{id}/read` → `is_read = true`; outro usuário → 403.
- [ ] `PATCH /preferences` com `email_enabled = false` para tipo X → e-mail não enviado para tipo X.
- [ ] Autor da ação não recebe notificação sobre ela.
- [ ] E-mail enfileirado e enviado via SMTP (verificar com Mailhog em dev).
- [ ] Multi-instância: dois servidores rodando → usuário conectado em qualquer um recebe o push.
- [ ] Contador do sino atualiza em tempo real via WebSocket.

## Estratégia de Testes

### Testes Unitários

- Resolução de destinatários: dado um evento e um chamado, a lista correta de usuários é gerada.
- Autor excluído: ator da ação não está na lista de destinatários.
- Preferências: usuário com opt-out de e-mail → task não enfileirada.

### Testes de Integração

- `notify("ticket_assigned", ...)` → notificação persistida para solicitante e observadores.
- `GET /notifications` → lista apenas notificações do usuário autenticado.
- `POST /notifications/{id}/read` → marcada como lida.
- Task de e-mail: mock de SMTP → e-mail enviado com dados corretos.
- WebSocket: conectar → receber push ao chamar `notify()`.

### Testes E2E

- Usuário A comenta no chamado → usuário B (observador, conectado) vê o sino incrementar em tempo real.
- Usuário B desconecta → usuário A faz ação → B reconecta → notificação aparece na lista.
- Admin desativa e-mail para tipo `ticket_comment_added` → comentário feito → e-mail NÃO enviado.

## Riscos Técnicos

- **Broadcast WebSocket multi-instância:** Redis pub/sub é a solução padrão. Sem isso, o push só funciona se o usuário estiver conectado na mesma instância que processou o evento.
- **Volume de notificações:** chamados movimentados geram muitas notificações. Índice em `(recipient_id, is_read, created_at)` e paginação eficiente são essenciais.
- **Falha de SMTP:** retry com backoff; notificação in-app não deve ser afetada por falha de e-mail.
- **Conexão WebSocket e autenticação:** o token JWT deve ser validado na conexão WS (via query string ou subprotocolo); tokens expirados devem desconectar o client.

## Complexidade

**Alta** — dois canais, jobs assíncronos, WebSocket com broadcast multi-instância e resolução dinâmica de destinatários.

## Prioridade

**Alta**

## Branch

`feature/014-notificacoes`
