---
id: P13
slug: encerramento-validacao
status: in-review
version: 1.0.0
owner: jhowworks
depends_on: [P01, P04, P09, P12]
satisfies: [RF-130, RF-131, RF-132, RNF-DISP-005]
adrs: [ADR-0001, ADR-0003, ADR-0004]
branch: feature/013-encerramento-validacao
last_updated: 2026-06-01
---

# P13 — Encerramento, Validação e Auto-Fechamento

## Objetivo

Gerenciar o ciclo de encerramento de um chamado: o técnico registra a solução, o solicitante valida (aprova ou rejeita), e o sistema fecha automaticamente se não houver resposta dentro do prazo configurado.

## Escopo

- Registro de solução (descrição obrigatória) ao marcar o chamado como Solucionado.
- Criação de pedido de validação ao solicitante.
- Fluxo de aprovação: solicitante aprova → chamado fechado.
- Fluxo de rejeição: solicitante rejeita → chamado volta para Em Atendimento (reopen).
- **Auto-fechamento:** job Celery Beat varre validações pendentes; se o prazo (`auto_close_days`, configurável por tenant) expirou, fecha o chamado automaticamente e notifica todos os envolvidos.
- Configuração do prazo de auto-fechamento em `tenant_settings`.
- Tela de validação para o solicitante.

## Fora do Escopo

- Transição de status base (P09 — a transição para Solucionado é disparada por P09; P13 complementa o que acontece *depois* dela).
- SLA (P12 — encerramento do SLA de Resolução é gerenciado por P12 ao detectar o `resolved_at`).
- Notificações em si (P14 — P13 chama o serviço de notificação).

## Dependências

- **P01** (Multi-Tenancy).
- **P04** (Usuários e Permissões).
- **P09** (Chamados) — a transição para `resolved` cria a solução e dispara o pedido de validação; a aprovação ou rejeição dispara transições de volta no fluxo de P09.
- **P10** (Timeline) — eventos de validação registrados na timeline.
- **P12** (SLA) — `resolved_at` sinaliza o fim do SLA de Resolução.
- **P14** (Notificações) — pedido de validação, aprovação, rejeição e auto-fechamento geram notificações.
- `tenant_settings.auto_close_days` — configuração gerenciada por P18.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `solutions` | Nova tabela (descrição da solução) |
| `validations` | Nova tabela (pedido de validação ao solicitante) |
| `tenant_settings` | Nova tabela (inclui `auto_close_days`) |

### `solutions`
```
id              UUID, PK
tenant_id       UUID, FK → tenants, INDEX
ticket_id       UUID, FK → tickets, UNIQUE
description     Text, NOT NULL
resolved_by     UUID, FK → users
resolved_at     DateTime, NOT NULL
```

### `validations`
```
id              UUID, PK
tenant_id       UUID, FK → tenants, INDEX
ticket_id       UUID, FK → tickets, UNIQUE
requester_id    UUID, FK → users           # solicitante do chamado
status          Enum('pending','approved','rejected'), DEFAULT 'pending'
expires_at      DateTime, NOT NULL         # created_at + tenant_settings.auto_close_days
responded_at    DateTime, nullable
responded_by    UUID, FK → users, nullable
rejection_reason Text, nullable
created_at      DateTime
```

### `tenant_settings`
```
id                  UUID, PK
tenant_id           UUID, FK → tenants, UNIQUE
auto_close_days     Integer, DEFAULT 5, NOT NULL
                     CHECK(auto_close_days BETWEEN 1 AND 90)
# outros settings futuros aqui (não criar tabelas separadas por setting)
updated_at          DateTime
updated_by          UUID, FK → users
```

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/tickets/{id}/validation` | Ver status da validação | participante |
| POST | `/api/v1/tickets/{id}/validation/approve` | Aprovar solução | solicitante do chamado |
| POST | `/api/v1/tickets/{id}/validation/reject` | Rejeitar solução | solicitante do chamado |
| GET | `/api/v1/admin/settings` | Ver configurações do tenant | `admin:config` |
| PATCH | `/api/v1/admin/settings` | Atualizar configurações (incl. `auto_close_days`) | `admin:config` |

### Body de `POST /validation/reject`
```json
{
  "rejection_reason": "O problema persiste — motor ainda travando ao iniciar."
}
```

### Resposta de `GET /tickets/{id}/validation`
```json
{
  "status": "pending",
  "expires_at": "2024-01-20T09:00:00Z",
  "days_remaining": 3,
  "solution": {
    "description": "Substituída a bobina do motor...",
    "resolved_by": { "id": "uuid", "name": "João Silva" },
    "resolved_at": "2024-01-15T14:00:00Z"
  }
}
```

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Painel de Validação | Exibido no detalhe do chamado para o solicitante quando status = "Solucionado"; exibe a solução e os botões "Aprovar" / "Rejeitar" |
| Banner de Pendente de Validação | Alerta para o solicitante na lista de chamados |

## Regras de Negócio

1. **Solução obrigatória ao resolver:** ao chamar a transição `in_progress → resolved` (P09), a descrição da solução é obrigatória. P09 cria o registro em `solutions` e chama P13 para criar o pedido de `validation`.
2. **Quem pode validar:** apenas o `requester_id` do chamado pode aprovar ou rejeitar. Nenhum outro usuário (nem admin) pode validar em nome do solicitante.
3. **Aprovação → Fechado:** atualiza `validation.status = 'approved'`; chama P09 para transição `resolved → closed`; registra evento de timeline; notifica todos os envolvidos.
4. **Rejeição → Em Atendimento:** atualiza `validation.status = 'rejected'`; chama P09 para transição `resolved → in_progress` (reabre); notifica técnico e observadores; SLA de Resolução retoma (integração com P12).
5. **Auto-fechamento:** job Celery Beat verifica validações com `status = 'pending'` e `expires_at < now()`:
   - Fecha o chamado: chama P09 para `resolved → closed`.
   - Seta `validation.status = 'approved'` (tecnicamente fechado por expiração — distinguível pelo método no evento de timeline).
   - Registra evento de timeline: `ticket_closed` com `method = 'auto'`.
   - Notifica **todos os envolvidos** (solicitante, responsável, observadores, supervisor da equipe).
6. **Prazo de auto-fechamento:** `auto_close_days` do `tenant_settings`. Se o admin alterar o prazo, novas validações usam o novo valor; validações já criadas mantêm o `expires_at` original.
7. **Somente uma validação ativa por chamado:** `UNIQUE(ticket_id)` na tabela `validations`.
8. **Rejeição com motivo:** `rejection_reason` é obrigatório ao rejeitar.

## Critérios de Aceite

- [ ] Transição para Solucionado sem descrição → 422 (verificado em P09, mas P13 valida ao criar `solutions`).
- [ ] `validations` criado com `expires_at = now() + auto_close_days`.
- [ ] Apenas o solicitante pode aprovar/rejeitar → outros recebem 403.
- [ ] Aprovação → chamado fechado; evento na timeline; notificação enviada.
- [ ] Rejeição com `rejection_reason` → chamado volta a Em Atendimento; notificação enviada.
- [ ] Rejeição sem `rejection_reason` → 422.
- [ ] Job de auto-fechamento: validação com `expires_at` no passado → chamado fechado com evento `method='auto'`; todos notificados.
- [ ] Job idempotente: rodar duas vezes no mesmo chamado não fecha duas vezes.
- [ ] `PATCH /admin/settings` altera `auto_close_days`; novas validações usam o novo prazo.

## Estratégia de Testes

### Testes Unitários

- Cálculo de `expires_at` com base no `auto_close_days`.
- Verificação de quem pode validar (apenas `requester_id`).
- Idempotência do job: chamado já `closed` → nenhuma ação.
- Regra de rejeição com motivo obrigatório.

### Testes de Integração

- `POST /validation/approve` com solicitante correto → chamado fechado + evento + notificação.
- `POST /validation/approve` com outro usuário → 403.
- `POST /validation/reject` sem `rejection_reason` → 422.
- `POST /validation/reject` com motivo → chamado reabre + evento + notificação.
- Job de auto-fechamento: criar validação expirada → rodar job → chamado fechado + evento `method='auto'`.
- `PATCH /admin/settings` → novo `auto_close_days` persiste; próxima validação usa novo prazo.

### Testes E2E

- Técnico resolve chamado → solicitante recebe notificação → aprova → chamado fechado.
- Técnico resolve chamado → solicitante rejeita com motivo → chamado reabre → técnico recebe notificação.
- Simular prazo expirado → job fecha → todos os participantes recebem notificação.

## Riscos Técnicos

- **Concorrência entre resposta do usuário e job:** solicitante aprova exatamente quando o job de auto-fechamento está rodando. Usar `SELECT FOR UPDATE` na validação ou verificar `status = 'pending'` como pré-condição antes de qualquer atualização.
- **Rejeição e SLA de Resolução (P12):** ao rejeitar, o chamado volta para Em Atendimento. P12 precisa retomar o SLA de Resolução (como se saísse de Pendente). Coordenar interface com P12 antes de implementar.
- **Notificação "todos os envolvidos" no auto-fechamento:** a lista de envolvidos deve incluir supervisor da equipe, não apenas participantes diretos. Definir interface com P14 antes de implementar.

## Complexidade

**Média** — fluxo claro, mas exige coordenação precisa com P09, P12 e P14; o job de auto-fechamento requer tratamento de concorrência.

## Prioridade

**Alta**

## Branch

`feature/013-encerramento-validacao`
