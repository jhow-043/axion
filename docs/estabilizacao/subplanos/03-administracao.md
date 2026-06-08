# Subplano 03 — Administração da Empresa / Plataforma

**Specs:** P18 (Console de Administração), P19 (Gestão de Plataforma — in-progress)
**Prioridade:** 🔴 Alto — branch atual; área mais recente e propensa a erros
**Status diagnóstico:** ⏳ Pendente

---

## Escopo das specs

### P18 — Console de Administração
- Console com sidebar: Empresa, Usuários, Equipes, Setores, Catálogos, SLA, Notificações, Auditoria
- P18 é **orquestrador**: não duplica lógica, delega para os módulos existentes
- Seção Empresa: `tenant_settings.auto_close_days` (1–90 dias)
- Provisioning de tenant: cria Tenant → seed roles/perms/defaults → cria admin inicial (transação)
- Todas as alterações de config auditadas (P17)
- Requer permissão `ADMIN_CONFIG`

### P19 — Gestão de Plataforma (Super-Admin)
- Rota `/plataforma` restrita a `system_admin`
- `GET /admin/platform/dashboard`: métricas globais (total empresas, usuários, chamados)
- `DELETE /admin/platform/tenants/:id`: soft delete (bloqueia `is_system`)
- Frontend: PlatformArea, GlobalDashboard, CompanyList, CompanyProvisionModal
- Soft delete: `deleted_at`, filtro automático em queries de tenant

---

## Arquivos relevantes

### Backend
- `backend/app/modules/administration/router.py`
- `backend/app/modules/administration/service.py`
- `backend/app/modules/administration/repository.py`
- `backend/app/modules/tenants/models.py` (is_system, deleted_at)
- `backend/app/core/deps.py` (require_system_admin)

### Frontend
- `frontend/src/features/administration/components/AdminConsole.tsx`
- `frontend/src/features/administration/components/sections/` (8 seções)
- `frontend/src/features/platform/components/PlatformArea.tsx`
- `frontend/src/features/platform/components/CompanyList.tsx`
- `frontend/src/features/platform/components/CompanyProvisionModal.tsx`
- `frontend/src/features/platform/api.ts`
- `frontend/src/app/router.tsx` (rota /plataforma, /administracao/*)

---

## Fluxos a validar

### Administração (/administracao)
- [ ] Admin consegue acessar /administracao (ADMIN_CONFIG)
- [ ] Técnico/Solicitante não consegue acessar → comportamento adequado (não 500)
- [ ] Seção Empresa: visualizar e editar `auto_close_days`
- [ ] Seção Usuários: lista usuários do tenant atual
- [ ] Seção Equipes: lista equipes do tenant atual
- [ ] Seção Setores: lista setores; pode criar/editar/desativar
- [ ] Seção Catálogos: gerenciar prioridades, status, categorias, motivos de pendência
- [ ] Seção SLA: gerenciar políticas de SLA
- [ ] Seção Notificações: visualizar/editar regras de notificação
- [ ] Seção Auditoria: visualizar logs com filtros

### Plataforma (/plataforma) — Super-Admin
- [ ] Login com `admin@plataforma.local` → rota /plataforma disponível no menu
- [ ] Dashboard global: exibe contagens (empresas, usuários, chamados)
- [ ] Lista de empresas: paginação, busca
- [ ] Provisionar nova empresa: modal + transação completa (tenant + seed + admin inicial)
- [ ] Empresa provisionada aparece na lista
- [ ] Admin da empresa provisionada consegue fazer login com as credenciais criadas
- [ ] Soft delete de empresa: `deleted_at` setado; não aparece na lista
- [ ] Soft delete de tenant `is_system` → bloqueado com erro adequado
- [ ] Usuário não-system-admin não acessa /plataforma → comportamento adequado (não 500)

---

## Problemas catalogados (Fase A)

| EST-ID | Classificação | Descrição | Arquivo:Linha | Reprodução |
|--------|--------------|-----------|---------------|------------|
| — | — | *A preencher* | — | — |

## Evidencias da varredura

- 2026-06-08: `uv run pytest tests/administration -q` com `DEBUG=false` executou 33 testes de administracao com sucesso.
- A execucao parcial falhou apenas no gate global de cobertura (`--cov-fail-under=90`), esperado quando se mede `app` inteiro rodando somente um subdiretorio.
- 2026-06-08: `uv run pytest -q` com `DEBUG=false` passou com 690 testes e cobertura 93,78%.

---

## Notas de risco

- P19 é `in-progress` — maior probabilidade de problemas de runtime.
- Super-admin opera **fora** do contexto de tenant; verificar se `require_system_admin` desvia corretamente da cadeia `get_current_user → set_tenant`.
- Provisioning é uma transação longa (tenant + seed + user); verificar rollback em caso de falha parcial.
- `deleted_at IS NULL` deve estar no filtro base do repository de tenants — verificar se foi implementado.
