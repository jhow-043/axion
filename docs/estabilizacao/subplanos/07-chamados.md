# Subplano 07 — Chamados (Núcleo, Timeline, Anexos, Notificações)

**Specs:** P09 (Chamados Core), P10 (Timeline), P11 (Anexos MinIO), P14 (Notificações)
**Prioridade:** 🔴 Crítico — módulo central da plataforma
**Status diagnóstico:** ⏳ Pendente

---

## Escopo das specs

### P09 — Chamados Core
- Tipos: industrial (equipamento obrigatório) | predial (local obrigatório)
- State machine: Novo → Em Atendimento (assumir) → Pendente (motivo) / Solucionado → Fechado
- Atribuição: define responsável + move para Em Atendimento
- Pendente: requer motivo de pendência
- Solucionado: requer descrição da solução → cria registro de validação (P13)
- Observadores: adicionar/remover; podem comentar, não transicionar
- Comentários: qualquer participante; edição própria em janela de 15 min
- Cada ação emite: evento timeline (P10) + notificação (P14)
- Listagem com filtros avançados

### P10 — Timeline
- Registro imutável e cronológico de eventos do chamado
- 12+ tipos de evento (criado, status_changed, comentário, anexo, atribuição, etc.)
- `GET /tickets/:id/timeline` paginado
- Componente TicketTimeline no detalhe do chamado

### P11 — Anexos MinIO
- Presigned URL para PUT direto no MinIO
- Confirmação após upload
- Listagem e download (presigned GET, expira)
- Deleção (somente uploader/admin/responsável)
- MIME + tamanho validados antes da URL (imagens ≤10MB, vídeos ≤200MB)
- Chave isolada por tenant: `{tenant_id}/{ticket_id}/{uuid}.ext`

### P14 — Notificações
- In-app (sempre persistida) + WebSocket push (se conectado)
- E-mail async via Celery (respeitando preferências)
- Sinos no topbar: contador de não-lidas, dropdown
- Página `/notifications`: lista paginada com filtros
- Preferências: `/notifications/preferences`
- 14 tipos de evento mapeados com regras de destinatários

---

## Arquivos relevantes

### Backend
- `backend/app/modules/tickets/` (router, service, repository, models, schemas)
- `backend/app/modules/timeline/` (router, service, repository, models)
- `backend/app/modules/attachments/` (router, service, repository, models)
- `backend/app/modules/notifications/` (router, service, repository, models, tasks.py, websocket.py)
- `backend/app/core/storage.py`

### Frontend
- `frontend/src/features/tickets/components/TicketList.tsx`
- `frontend/src/features/tickets/components/TicketForm.tsx`
- `frontend/src/features/tickets/components/TicketDetail.tsx`
- `frontend/src/features/timeline/components/TicketTimeline.tsx`
- `frontend/src/features/attachments/components/AttachmentUpload.tsx`
- `frontend/src/features/attachments/components/AttachmentGallery.tsx`
- `frontend/src/features/notifications/components/NotificationBell.tsx`
- `frontend/src/features/notifications/components/NotificationList.tsx`
- `frontend/src/features/notifications/components/NotificationPreferences.tsx`
- `frontend/src/features/notifications/hooks/useNotificationSocket.ts`

---

## Fluxos a validar

### Criação
- [ ] Criar chamado industrial: equipamento + setor + prioridade + categoria → aparece na lista
- [ ] Criar chamado predial: local + prioridade + categoria → aparece na lista
- [ ] Criar chamado industrial sem equipamento → erro de validação
- [ ] Criar chamado predial sem local → erro de validação

### Listagem e filtros
- [ ] Filtrar por tipo (industrial/predial)
- [ ] Filtrar por status, prioridade, setor
- [ ] Busca por texto
- [ ] Paginação

### Fluxo de estados
- [ ] Novo → assumir → Em Atendimento (responsável definido)
- [ ] Em Atendimento → Pendente (com motivo de pendência)
- [ ] Pendente → Em Atendimento (retomada)
- [ ] Em Atendimento → Solucionado (com descrição da solução)
- [ ] Transição inválida → erro adequado (não 500)
- [ ] Observador tenta transicionar → 403

### Comentários
- [ ] Adicionar comentário → aparece na listagem
- [ ] Editar comentário próprio dentro de 15 min → alterado
- [ ] Editar comentário após 15 min → bloqueado

### Observadores
- [ ] Adicionar observador → aparece no chamado
- [ ] Remover observador → some do chamado

### Timeline (P10)
- [ ] Cada ação no chamado gera evento na timeline
- [ ] Timeline exibida no detalhe do chamado (cronológica, paginada)

### Anexos (P11)
- [ ] Upload de imagem: 3 passos (URL presigned → PUT → confirm)
- [ ] Arquivo aparece na galeria do chamado
- [ ] Download via presigned URL
- [ ] Deleção por uploader
- [ ] Arquivo > 10MB bloqueado antes de gerar URL
- [ ] MinIO acessível (docker compose up -d)

### Notificações (P14)
- [ ] Ação no chamado → notificação in-app para destinatários corretos
- [ ] Sino no topbar exibe contador de não-lidas
- [ ] Marcar como lida → contador decrementado
- [ ] Página /notifications exibe lista
- [ ] WebSocket: notificação aparece em tempo real (sem refresh)
- [ ] Preferências: desativar tipo de notificação → não recebe mais

---

## Problemas catalogados (Fase A)

| EST-ID | Classificação | Descrição | Arquivo:Linha | Reprodução |
|--------|--------------|-----------|---------------|------------|
| — | — | *A preencher* | — | — |

---

## Notas de risco

- Tickets não têm "editar" direto (apenas transições de estado) — confirmar que a UI não oferece botão de edição de campos.
- MinIO precisa estar rodando e com bucket configurado para upload funcionar.
- WebSocket `useNotificationSocket` — integração na tela de notificações não confirmada na exploração estática.
- Chamados são o módulo mais complexo; qualquer problema em dependências (setores/locais/equipamentos/catálogos) se manifesta aqui.
