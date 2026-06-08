# Inventário de Módulos

## Backend — `backend/app/modules/`

| Módulo | Router | Service | Repo | Models | Testes | Endpoints principais | Spec(s) |
|--------|--------|---------|------|--------|--------|----------------------|---------|
| **auth** | ✅ | ✅ | ✅ | ✅ | ✅ (2 arquivos) | POST /auth/login, /refresh, /logout; GET /auth/me | P03 |
| **users** | ✅ | ✅ | ✅ | ✅ | ✅ (3 arquivos) | CRUD /users; /roles; /permissions | P04 |
| **teams** | ✅ | ✅ | ✅ | ✅ | ✅ (3 arquivos) | CRUD /teams; /teams/:id/members | P05 |
| **locations** | ✅ | ✅ | ✅ | ✅ | ✅ (3 arquivos) | CRUD /sectors; CRUD /locations | P06 |
| **catalog** | ✅ | ✅ | ✅ | ✅ | ✅ (3 arquivos) | /catalog/priorities, /statuses, /categories, /pending-reasons | P07 |
| **equipments** | ✅ | ✅ | ✅ | ✅ | ✅ (3 arquivos) | CRUD /equipments; /equipments/:id/tickets | P08 |
| **tickets** | ✅ | ✅ | ✅ | ✅ | ✅ (3 arquivos) | CRUD /tickets; assign, transition, observers, comments | P09 |
| **timeline** | ✅ | ✅ | ✅ | ✅ | ✅ (3 arquivos) | GET /tickets/:id/timeline | P10 |
| **attachments** | ✅ | ✅ | ✅ | ✅ | ✅ (3 arquivos) | upload-url, confirm, list, download-url, delete | P11 |
| **sla** | ✅ | ✅ | ✅ | ✅ | ✅ (4 arquivos) | CRUD /sla/policies; GET /tickets/:id/sla | P12 |
| **closures** | ✅ | ✅ | ✅ | ✅ | ✅ (1 arquivo) | GET/POST /tickets/:id/validation; GET/PATCH /admin/closures/settings | P13 |
| **notifications** | ✅ | ✅ | ✅ | ✅ | ❌ 0 testes | GET/POST /notifications; /preferences; WS /ws/notifications | P14 |
| **dashboards** | ✅ | ✅ | ✅ | — | ✅ (3 arquivos) | /dashboards/technician, /supervisor, /board, /management | P15, P16 |
| **reports** | ✅ | ❌ | ❌ | — | ❌ 0 testes | GET /reports/tickets, /sla, /equipments, /teams | P16 |
| **audit** | ✅ | ✅ | ✅ | ✅ | ✅ (3 arquivos) | GET /audit-logs | P17 |
| **administration** | ✅ | ✅ | ✅ | — | ✅ (4 arquivos) | CRUD /admin/tenants; GET /admin/tenants/dashboard | P18, P19 |
| **tenants** | ❌ router | ✅ model | — | ✅ | ✅ (3 arquivos) | gerenciado via administration | P01, P19 |

### Infraestrutura cross-cutting (backend)

| Componente | Arquivo | Função |
|-----------|---------|--------|
| TenantMixin | `app/shared/tenant_mixin.py` | Adiciona `tenant_id` FK em todos os modelos de domínio |
| BaseRepository | `app/shared/base_repository.py` | Auto-filtra `WHERE tenant_id = :current` em todas as queries |
| TenantContext | `app/shared/tenant_context.py` | ContextVar para propagar `tenant_id` na requisição |
| get_current_user | `app/core/deps.py` | Valida Bearer JWT, seta ContextVar, retorna User ORM |
| require_permission | `app/core/deps.py` | Factory de dependência para RBAC |
| require_system_admin | `app/core/deps.py` | Checa permissão `system_admin` (super-admin) |
| StorageService | `app/core/storage.py` | Presigned URLs MinIO (upload/download) |
| Celery app | `app/core/celery_app.py` | Worker async para SLA, closures, notifications |
| Permissões (13 códigos) | `app/core/permissions.py` | Registro central de todos os códigos de permissão |

### Migrations Alembic (`backend/alembic/versions/`)

| Migração | Tabelas criadas/alteradas |
|----------|--------------------------|
| p01 | `tenants` |
| p03_p04 | `permissions`, `roles`, `users`, `refresh_tokens`, `user_roles`, `role_permissions` |
| p05 | `teams`, `team_members` |
| p06 | `sectors`, `locations` |
| p07 | `priorities`, `statuses`, `categories`, `pending_reasons` |
| p08 | `equipments` |
| p09 | `tickets`, `ticket_observers`, `ticket_comments`, `solutions` |
| p10 | `ticket_events` |
| p11 | `attachments` |
| p12 | `sla_policies`, `sla_trackers`, `sla_pauses` |
| p13 | `validations`, `tenant_settings` |
| p14 | `notifications`, `notification_preferences` |
| p17 | `audit_logs` |
| p19 | `tenants` (+`is_system`, +`deleted_at`) |

---

## Frontend — `frontend/src/features/`

| Feature | api.ts | components/ | hooks/ | types.ts | CRUD implementado | Rota(s) | Spec(s) |
|---------|--------|------------|--------|----------|-------------------|---------|---------|
| **auth** | ✅ | LoginPage | — | ✅ | Login | /login | P03 |
| **users** | ✅ | UserList, UserForm, UserDetail, RoleAssignment | — | ✅ | ✅ Completo + roles | /users | P04 |
| **teams** | ✅ | TeamList, TeamForm, TeamMembers | — | ✅ | ✅ Completo + membros | /teams | P05 |
| **equipments** | ✅ | EquipmentList, EquipmentForm, EquipmentDetail | — | ✅ | ✅ Completo | /equipments | P08 |
| **tickets** | ✅ | TicketList, TicketForm, TicketDetail | — | ✅ | Criar/Listar/Ver/Transições (sem edit direto) | /tickets | P09 |
| **locations** | ✅ | LocationList, LocationForm, SectorList, SectorForm, SetoresLocaisPage | — | ✅ | ✅ Completo (setor + local) | /setores, /locais | P06 |
| **catalog** | ✅ | — (via Administration) | — | ✅ | Via /administracao/catalogos | — | P07 |
| **sla** | ✅ | SlaPolicyList, SlaPolicyForm, SlaIndicator | — | ✅ | ✅ Completo | /sla | P12 |
| **notifications** | ✅ | NotificationBell, NotificationList, NotificationPreferences | useNotificationSocket | ✅ | Listar/Lido/Preferências | /notifications | P14 |
| **attachments** | ✅ | AttachmentUpload, AttachmentGallery | — | ✅ | Upload 3 passos + Delete | (embutido em TicketDetail) | P11 |
| **timeline** | ✅ | TicketTimeline | — | ✅ | Read-only | (embutido em TicketDetail) | P10 |
| **dashboards** | ✅ | TechnicianDashboard, SupervisorDashboard, ManagementDashboard, KanbanBoard, Reports | — | ✅ | Read-only (dashboards + relatórios) | /dashboard/*, /relatorios | P15, P16 |
| **administration** | ✅ | AdminConsole + 8 seções | — | ✅ | Console admin (orquestra módulos) | /administracao/* | P18 |
| **platform** | ✅ | PlatformArea, GlobalDashboard, CompanyList, CompanyProvisionModal | — | ✅ | ✅ Completo (CRUD tenants) | /plataforma | P19 |

### Infraestrutura cross-cutting (frontend)

| Componente | Arquivo | Função |
|-----------|---------|--------|
| Router | `src/app/router.tsx` | React Router v7; RequireAuth guard; todas as rotas |
| AuthProvider | `src/app/providers/AuthProvider.tsx` | Sessão, login/logout, refresh automático |
| Axios client | `src/shared/api/client.ts` | Bearer token, interceptor de 401 (refresh), withCredentials |
| Sidebar | `src/shared/components/layout/Sidebar.tsx` | Menu lateral com permission-aware items |
| AppShell | `src/shared/components/layout/AppShell.tsx` | Layout principal (sidebar + topbar + content) |

### Rotas protegidas — todas via `RequireAuth`

Verificação de permissão está em nível de **componente** (`hasPermission()`), não de rota.
Risco: usuário pode navegar para a URL; a API responde 403 e a tela pode quebrar.

---

## Gaps identificados na exploração estática

| # | Módulo | Tipo | Descrição | Risco |
|---|--------|------|-----------|-------|
| 1 | reports (backend) | ❌ Sem implementação | Router existe mas sem service/schemas/models; 0 testes | Alto — tela /relatorios provavelmente quebra |
| 2 | notifications (backend) | ⚠️ Sem testes | Módulo completo porém sem cobertura de testes | Médio |
| 3 | router.tsx (frontend) | ⚠️ Design | Sem guardas de rota por permission; só checagem por componente | Médio |
| 4 | closures (backend) | ⚠️ Inconsistência | `TICKET_VALIDATE` definido mas closures checam por papel, não permissão | Médio |
| 5 | seed_dev.py | ⚠️ Drift | Imprime porta `:3001`, Vite usa `:5173` | Baixo (documentação) |
| 6 | platform/admin | ⚠️ Risco | Soft delete + queries cross-tenant; módulo mais recente (in-progress) | Alto |
| 7 | useNotificationSocket | ⚠️ Integração incerta | Hook existe; integração na tela de notificações não confirmada | Médio |

---

*Atualizado na Fase A conforme diagnóstico de cada subplano.*
