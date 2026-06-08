---
id: P19
slug: plataforma-superadmin
status: in-progress
version: 0.1.0
owner: jhowworks
depends_on: [P01, P04, P17, P18]
satisfies: [RF-190, RF-191, RF-192, RF-193, RF-194]
adrs: [ADR-0001, ADR-0002]
branch: feature/019-plataforma-superadmin
last_updated: 2026-06-08
---

# P19 — Gestão de Plataforma (Super-Admin)

## Objetivo

Prover uma área exclusiva para o super-administrador da plataforma gerenciar todas as empresas (tenants) provisionadas na instância, com dashboard global de métricas agregadas, provisionamento de novos tenants e soft delete de tenants encerrados.

## Escopo

- Coluna `is_system` no modelo `Tenant` — marca o tenant reservado da plataforma (não pode ser excluído nem impersonado).
- Coluna `deleted_at` no modelo `Tenant` — soft delete com filtro automático nas queries.
- Migration P19: adiciona `is_system`, `deleted_at` e índice em `tenants`.
- `DashboardRepository`: queries de métricas globais agregadas (total de companies, usuários, chamados).
- Endpoint `GET /admin/platform/dashboard` — dashboard global para super-admin.
- Endpoint `DELETE /admin/platform/tenants/{tenant_id}` — soft delete de tenant (protegido de tenants `is_system`).
- Frontend — Área da Plataforma (`PlatformArea`) com:
  - `GlobalDashboard`: KPIs globais (companies, usuários, tickets) com listagem paginada de empresas.
  - `CompanyList`: tabela de empresas com status, contadores e ações.
  - `CompanyProvisionModal`: formulário de criação de novo tenant com provisionamento automático.
- Rota `/platform` protegida por papel `system_admin` (global, fora do escopo de tenant).

## Fora do Escopo

- Billing / planos por tenant (futuro).
- Impersonation de tenant pelo super-admin (futuro, requer spec própria).
- Configuração de limites por empresa (quotas, storage) — futuro.
- White-label por tenant — futuro.

## Dependências

- **P01** (Multi-Tenancy) — modelo `Tenant` e `BaseRepository`.
- **P04** (Usuários e Permissões) — papel `system_admin` e guard `require_system_admin`.
- **P17** (Auditoria) — log de criação e deleção de tenant.
- **P18** (Administração) — `AdminService` e `TenantRepository` base.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `tenants` | Alterada — adiciona `is_system`, `deleted_at` |

### Mudanças em `tenants`
```
is_system   Boolean, NOT NULL, DEFAULT false
deleted_at  DateTime, NULLABLE — preenchido em soft delete
```

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/admin/platform/dashboard` | Dashboard global com métricas e lista de companies | `system_admin` |
| DELETE | `/api/v1/admin/platform/tenants/{id}` | Soft delete de tenant | `system_admin` |

### Response de `GET /admin/platform/dashboard`
```json
{
  "total_companies": 12,
  "active_companies": 10,
  "suspended_companies": 2,
  "total_users": 347,
  "total_tickets": 5823,
  "companies": [{ "id": "...", "name": "...", "slug": "...", "is_active": true, "is_system": false, "created_at": "...", "user_count": 28, "ticket_count": 412, "plan": null }],
  "page": 1,
  "page_size": 20,
  "total_company_pages": 1
}
```

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| `/platform` — `PlatformArea` | Container da área de plataforma; renderiza sub-rota ativa |
| `/platform/dashboard` — `GlobalDashboard` | KPIs globais + tabela de companies com paginação |
| Modal `CompanyProvisionModal` | Formulário de criação de tenant com nome e slug |

## Regras de Negócio

1. **Tenant do sistema:** tenant com `is_system = true` não pode ser excluído nem ter seu papel alterado.
2. **Soft delete:** `deleted_at` preenchido oculta o tenant de todas as queries normais; a migration usa `IF NOT EXISTS` para ser idempotente.
3. **Isolamento:** o dashboard global só é acessível por usuários com papel `system_admin`; não retorna dados do próprio tenant da plataforma nas métricas de "clients".
4. **Provisionamento:** criação de novo tenant via modal dispara o mesmo fluxo de seed de P18 (papéis padrão, configurações).

## Critérios de Aceite

- [ ] `GET /admin/platform/dashboard` retorna métricas corretas e lista paginada de companies.
- [ ] Tenant com `is_system = true` não pode ser deletado (retorna 409).
- [ ] `DELETE /admin/platform/tenants/{id}` preenche `deleted_at` e o tenant some das listagens.
- [ ] Rota `/platform` redireciona para login se o usuário não for `system_admin`.
- [ ] `GlobalDashboard` exibe KPIs e tabela de companies com paginação funcional.
- [ ] `CompanyProvisionModal` cria tenant e recarrega a lista.
- [ ] Tenant deletado (soft) não aparece no `GlobalDashboard`.
- [ ] Migration P19 é idempotente (`IF NOT EXISTS`).

## Estratégia de Testes

### Testes Unitários

- `DashboardRepository.get_global_stats()`: retorna totais corretos com tenants deletados excluídos.
- `AdminService.delete_tenant()` com tenant `is_system`: deve lançar `ConflictError`.
- `TenantRepository._active_stmt()`: filtra tenants com `deleted_at IS NOT NULL`.

### Testes de Integração

- `GET /admin/platform/dashboard` com `system_admin`: 200 + dados corretos.
- `GET /admin/platform/dashboard` sem `system_admin`: 403.
- `DELETE /admin/platform/tenants/{id}` (normal): 204, tenant não aparece mais.
- `DELETE /admin/platform/tenants/{id}` (is_system): 409.

### Testes E2E

- Super-admin acessa `/platform`, vê dashboard com lista de companies e pode criar nova company.

## Riscos Técnicos

- **Risco:** queries agregadas cross-tenant podem ser lentas em instâncias com muitos tenants. **Mitigação:** índices em `tenants.deleted_at` e `users.tenant_id`; queries com `COUNT` simples sem JOINs desnecessários.

## Complexidade

**Média** — envolve mudanças no modelo `Tenant`, nova camada de dashboard global e proteção de rota por papel global.

## Prioridade

**Alta** — necessário para operação da plataforma SaaS (onboarding de novos clientes).

## Branch

`feature/019-plataforma-superadmin`
