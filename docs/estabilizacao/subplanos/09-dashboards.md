# Subplano 09 — Dashboards e Relatórios

**Specs:** P15 (Dashboards Operacionais), P16 (Dashboard Gerencial e Relatórios)
**Prioridade:** Médio
**Status diagnóstico:** ⏳ Pendente

---

## Escopo das specs

### P15 — Dashboards Operacionais
- **Técnico**: chamados atribuídos por status, pendentes, SLAs em risco
- **Supervisor**: resumo geral, filas por equipe, SLAs, % de conformidade
- **Kanban**: colunas por status (exceto Fechado), drag-and-drop (chama transição P09)
- Filtros: equipe, período, prioridade
- Endpoints: `/dashboards/technician`, `/dashboards/supervisor`, `/dashboards/board`
- Refresh a cada 60s (não WebSocket)

### P16 — Dashboard Gerencial e Relatórios
- KPIs: total, abertos, fechados, por tipo/prioridade/status, horas médias de resolução, % conformidade SLA, chamados vencidos
- Ranking de equipamentos (mais chamados + criticidade)
- Performance por equipe (volume, SLA, tempo médio)
- Filtros: período (obrigatório, máx 12 meses), tipo, prioridade, equipe
- Exportação CSV (streaming on-demand)
- Endpoints: `/dashboards/management`, `/reports/tickets`, `/reports/sla`, `/reports/equipments`, `/reports/teams`

---

## Arquivos relevantes

### Backend
- `backend/app/modules/dashboards/router.py`
- `backend/app/modules/dashboards/service.py`
- `backend/app/modules/dashboards/repository.py`
- `backend/app/modules/reports/router.py` ← **sem service/schemas/models; 0 testes**

### Frontend
- `frontend/src/features/dashboards/components/TechnicianDashboard.tsx`
- `frontend/src/features/dashboards/components/SupervisorDashboard.tsx`
- `frontend/src/features/dashboards/components/ManagementDashboard.tsx`
- `frontend/src/features/dashboards/components/KanbanBoard.tsx`
- `frontend/src/features/dashboards/components/Reports.tsx`
- `frontend/src/features/dashboards/api.ts`
- Rotas: `/dashboard/technician`, `/dashboard/supervisor`, `/dashboard/board`, `/dashboard/management`, `/relatorios`

---

## Fluxos a validar

### Dashboard Técnico
- [ ] Técnico vê seus chamados por status
- [ ] Chamados com SLA em risco destacados
- [ ] Técnico não vê chamados de outros técnicos da equipe

### Dashboard Supervisor
- [ ] Supervisor vê resumo da equipe
- [ ] Filtro por equipe funciona
- [ ] % de conformidade SLA calculada corretamente

### Kanban
- [ ] Colunas exibem chamados por status (exceto Fechado)
- [ ] Drag-and-drop para transição de status funciona
- [ ] Transição inválida: card retorna à coluna original com mensagem

### Dashboard Gerencial
- [ ] KPIs exibidos com filtro de período obrigatório
- [ ] Período > 12 meses rejeitado
- [ ] Ranking de equipamentos carrega corretamente
- [ ] Performance por equipe carrega corretamente

### Relatórios (RISCO ALTO)
- [ ] `/relatorios` carrega sem erro 500
- [ ] Relatório de chamados: JSON + download CSV funcionam
- [ ] Relatório de SLA: JSON + download CSV
- [ ] Relatório de equipamentos: JSON + download CSV
- [ ] Relatório de equipes: JSON + download CSV

---

## Problemas catalogados (Fase A)

| EST-ID | Classificação | Descrição | Arquivo:Linha | Reprodução |
|--------|--------------|-----------|---------------|------------|
| EST-FE-002 | Bloqueador | Build frontend falha porque o handler de drag usa `data.columns` quando o TypeScript ainda considera `data` possivelmente indefinido | `frontend/src/features/dashboards/components/KanbanBoard.tsx:137` | `cd frontend && npm run build` |
| — | — | *A preencher* | — | — |

## Evidencias da correcao

- Issue: #27
- PR: #28
- Branch: `fix/EST-FE-002-kanban-data-narrowing`
- 2026-06-08: `npm run build` passou.
- 2026-06-08: `npm run test` passou com 37 testes.

---

## Notas de risco

- **Módulo `reports` (backend) é o maior risco desta fase**: router existe mas sem service/schemas/models e 0 testes — alta probabilidade de 500 ao acessar /relatorios.
- Kanban usa drag-and-drop que chama a API de transição do P09 — verificar se a biblioteca de DnD está configurada.
- Aggregation queries sem índices corretos podem ser lentas; verificar explain plans para tabelas grandes.
