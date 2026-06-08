# Subplano 08 — SLA e Encerramento

**Specs:** P12 (SLA), P13 (Encerramento e Validação)
**Prioridade:** Alto
**Status diagnóstico:** ⏳ Pendente

---

## Escopo das specs

### P12 — SLA
- Dois SLAs independentes por chamado: Atendimento e Resolução
- `sla_policies`: (tipo_chamado × prioridade × [equipe opcional]) → minutos
- `sla_trackers`: estado SLA por chamado (due_at, status, pause_minutes acumulados)
- `sla_pauses`: histórico de pausas (Pendente pausa o SLA de Resolução)
- Motor: calcula `attendance_due_at` na criação; `resolution_due_at` na atribuição
- Celery Beat (a cada 5 min): detecta alerta (80%) e breach (vencido)
- UI: barras de progresso e badges de status no detalhe do chamado
- Seleção de política: mais específica vence (tipo+prio+equipe > tipo+prio > all)

### P13 — Encerramento e Validação
- Técnico registra solução (descrição obrigatória) ao marcar Solucionado
- Solicitante recebe pedido de validação: Aprovar → Fechado | Rejeitar → Em Atendimento
- Auto-fechamento: `tenant_settings.auto_close_days` após ficar Solucionado (job Celery)
- Rejeição reabre o chamado e resume o SLA

---

## Arquivos relevantes

### Backend
- `backend/app/modules/sla/` (router, service, repository, models, tasks.py)
- `backend/app/modules/closures/` (router, service, repository, models, tasks.py)
- `backend/app/modules/closures/tests/test_unit.py`

### Frontend
- `frontend/src/features/sla/components/SlaPolicyList.tsx`
- `frontend/src/features/sla/components/SlaPolicyForm.tsx`
- `frontend/src/features/sla/components/SlaIndicator.tsx`
- `frontend/src/features/tickets/components/TicketDetail.tsx` (seção SLA + validação)
- `frontend/src/features/sla/api.ts`

---

## Fluxos a validar

### Políticas de SLA
- [ ] Criar política de SLA (tipo × prioridade → minutos)
- [ ] Editar política
- [ ] Desativar política
- [ ] Política mais específica vence em seleção (verificar service)

### Tracking no chamado
- [ ] Chamado criado: `attendance_due_at` calculado corretamente
- [ ] Chamado assumido: `resolution_due_at` calculado
- [ ] SLA exibido no detalhe (barra de progresso, badge)
- [ ] Chamado em Pendente: SLA de resolução pausado
- [ ] Chamado retomado: SLA de resolução resume com acumulado correto
- [ ] Job Celery Beat rodando: detecta e marca alert/breach
- [ ] Chamado vencido: badge de breach visível

### Encerramento e validação (P13)
- [ ] Marcar Solucionado sem solução → erro de validação
- [ ] Marcar Solucionado com solução → validação criada para o solicitante
- [ ] Solicitante vê pedido de validação no chamado
- [ ] Aprovar → chamado Fechado; SLA de resolução marcado como cumprido
- [ ] Rejeitar → chamado volta a Em Atendimento; SLA retomado
- [ ] Auto-fechamento: após `auto_close_days` sem validação, chamado é fechado automaticamente
- [ ] Job auto-fechamento idempotente (não fecha duas vezes)

---

## Problemas catalogados (Fase A)

| EST-ID | Classificação | Descrição | Arquivo:Linha | Reprodução |
|--------|--------------|-----------|---------------|------------|
| EST-FE-001 | Bloqueador | Build frontend falha por dependencia `date-fns` ausente usada no indicador de SLA | `frontend/src/features/sla/components/SlaIndicator.tsx:1` | `cd frontend && npm run build` |
| — | — | *A preencher* | — | — |

## Evidencias da correcao

- 2026-06-08: removida a dependencia nao declarada `date-fns` do `SlaIndicator`.
- 2026-06-08: `npm run test -- src/utils/__tests__/dates.test.ts` passou com 4 testes.
- 2026-06-08: `npm run test` passou com 37 testes.
- 2026-06-08: `npm run build` nao aponta mais erro de `date-fns`; segue bloqueado por EST-FE-002.

---

## Notas de risco

- `TICKET_VALIDATE` está definido como permissão mas closures podem checar por papel — inconsistência apontada na exploração.
- Celery Beat precisa estar rodando para os jobs de SLA e auto-fechamento funcionarem.
- Cálculo de `resolution_due_at` com pausas acumuladas: verificar edge case de múltiplas pausas.
- Rejeição de validação deve retomar o SLA; verificar integração closures → sla.
