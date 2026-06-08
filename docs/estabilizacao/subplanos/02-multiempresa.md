# Subplano 02 — Multiempresa / Contexto de Tenant

**Specs:** P01 (Multi-Tenancy)
**Prioridade:** 🔴 Crítico — isolamento de dados é invariante central
**Status diagnóstico:** ⏳ Pendente

---

## Escopo da spec

- Entidade `Tenant` (name, slug, is_active, is_system, deleted_at, audit)
- JWT carrega `tenant_id` → ContextVar via `get_current_user()`
- `TenantMixin`: adiciona `tenant_id` FK + índice em todos os modelos de domínio
- `BaseRepository`: auto-filtra `WHERE tenant_id = :current` em todas as queries
- Cross-tenant → 404 (nunca 403)
- Celery: `tenant_id` passado explicitamente no payload do job (não derivado do ContextVar)
- Tenant inativo → rejeita autenticação

---

## Arquivos relevantes

- `backend/app/modules/tenants/models.py` (Tenant + is_system + deleted_at)
- `backend/app/shared/tenant_mixin.py` (TenantMixin)
- `backend/app/shared/base_repository.py` (BaseRepository + tenant scoping)
- `backend/app/shared/tenant_context.py` (ContextVar, set_tenant, get_tenant, tenant_context)
- `backend/app/core/deps.py` (get_current_user → set_tenant)
- `backend/alembic/versions/` (migração p01 + p19)

---

## Fluxos a validar

- [ ] Dados criados no tenant A não aparecem para o tenant B
- [ ] Acesso a ID de outro tenant retorna 404, não 403
- [ ] Tenant inativo → autenticação rejeitada
- [ ] ContextVar corretamente isolado entre requisições concorrentes
- [ ] Job Celery recebe `tenant_id` no payload; não deriva do ContextVar
- [ ] `deleted_at` (soft delete P19): tenant deletado não aparece nas listagens
- [ ] `is_system=True`: tenant-plataforma não pode ser deletado via API

---

## Problemas catalogados (Fase A)

| EST-ID | Classificação | Descrição | Arquivo:Linha | Reprodução |
|--------|--------------|-----------|---------------|------------|
| — | — | *A preencher* | — | — |

---

## Notas de risco

- Qualquer falha no TenantMixin/BaseRepository vaza dados entre tenants.
- P19 adicionou `deleted_at` + `is_system` ao modelo Tenant — verificar se o `BaseRepository` do módulo administration inclui o filtro `deleted_at IS NULL`.
- Verificar se a migração p19 foi aplicada sem problemas em banco existente.
