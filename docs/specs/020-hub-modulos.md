---
id: P20
slug: hub-modulos
status: done
version: 0.1.0
owner: jhowworks
depends_on: [P01, P03, P04, P19]
satisfies: [RF-200, RF-201, RF-202, RF-203, RF-208]
adrs: [ADR-0001, ADR-0002, ADR-0006]
branch: feature/020-hub-modulos
last_updated: 2026-06-15
---

# P20 — Núcleo de Módulos (HUB — Backend)

## Objetivo

Criar a infraestrutura de backend que permite ao HUB controlar quais módulos/produtos
estão liberados para cada empresa, aplicar gating de acesso via dependency reutilizável
e expor a lista de módulos liberados no endpoint `/auth/me`.

## Escopo

- Tabela `modules` — catálogo global de módulos disponíveis na plataforma.
- Tabela `tenant_modules` — vínculo entre tenant e módulo liberado.
- Migration Alembic com seed inicial do módulo `manutencao`.
- `ModuleRepository` com métodos: `list_catalog()`, `is_enabled(tenant_id, code)`,
  `list_enabled_for_tenant(tenant_id)`.
- Dependency `require_module(code)` em `app/core/deps.py` — retorna 404 quando o módulo
  não está liberado (coerente com ADR-0002).
- `/auth/me` passa a incluir `enabled_modules: list[str]` na resposta.
- Seed automático: ao provisionar novo tenant (serviço de P18/P19), o módulo `manutencao`
  é liberado automaticamente (retrocompatibilidade).
- Testes unitários e de integração com cobertura ≥90%.

## Fora do Escopo

- Endpoints de gestão de módulos pelo super-admin (P21).
- Alterações no frontend (P22, P23).
- Aplicação de `require_module` nos routers de manutenção (P24).
- Billing, cotas, planos ou qualquer lógica de pagamento.

## Dependências

- **P01** (Multi-Tenancy) — modelo `Tenant` e `BaseRepository` como base.
- **P03** (Autenticação) — endpoint `/auth/me` e `AuthService` a ser estendido.
- **P04** (Usuários e Permissões) — padrão de `require_permission` a ser replicado.
- **P19** (Plataforma Super-Admin) — serviço de provisionamento de tenant a ser estendido
  com o seed do módulo.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `modules` | Nova tabela (catálogo global) |
| `tenant_modules` | Nova tabela (vínculo tenant ↔ módulo) |
| `/auth/me` response | Alterada — adiciona `enabled_modules` |

### `modules`
```
id              UUID, PK
code            String, UNIQUE, NOT NULL     # âncora estável: "manutencao"
name            String, NOT NULL             # "Gestão de Manutenção"
description     Text, nullable
icon            String, nullable             # nome do ícone Lucide
sort_order      Integer, DEFAULT 0
is_active       Boolean, DEFAULT true
created_at      DateTime
updated_at      DateTime
```

### `tenant_modules`
```
id              UUID, PK
tenant_id       UUID, FK → tenants, NOT NULL
module_id       UUID, FK → modules, NOT NULL
UNIQUE          (tenant_id, module_id)
INDEX           (tenant_id)
enabled_at      DateTime, NOT NULL
```

## APIs Necessárias

Nenhuma nova rota pública nesta spec. A mudança visível é no contrato de `/auth/me`:

### Response atualizado de `GET /auth/me`
```json
{
  "id": "uuid",
  "name": "João Silva",
  "email": "joao@empresa.com",
  "tenant_id": "uuid",
  "roles": ["admin"],
  "permissions": ["ticket:create", "user:manage"],
  "enabled_modules": ["manutencao"],
  "is_active": true
}
```

## Telas Necessárias

Nenhuma — apenas backend.

## Regras de Negócio

1. **Catálogo global:** `modules` é escopo da plataforma, sem `tenant_id`. Qualquer query
   direta (sem `BaseRepository`) é permitida nessa tabela por design.
2. **Liberação:** presença de linha em `tenant_modules` = módulo liberado; ausência = bloqueado.
   Não existe estado "suspenso" na v1.
3. **Gating — 404:** `require_module(code)` resolve `is_enabled(tenant_id, code)` no banco
   e retorna `404` (nunca 403) quando não liberado — coerente com ADR-0002.
4. **Seed de provisionamento:** `TenantProvisioningService` (P18/P19) deve inserir uma linha
   em `tenant_modules` para `manutencao` ao criar qualquer novo tenant.
5. **Retrocompatibilidade:** migration inclui data script que libera `manutencao` para todos
   os tenants existentes no momento da execução.
6. **`enabled_modules` no token:** a lista é resolvida no banco a cada chamada de `/auth/me`,
   não cacheada no JWT — coerente com o padrão de permissões (sem cache stale).

## Critérios de Aceite

- [ ] Migration cria `modules` e `tenant_modules` e é idempotente (`IF NOT EXISTS`).
- [ ] Seed inicial insere o módulo `manutencao` em `modules`.
- [ ] Data script da migration libera `manutencao` para todos os tenants existentes.
- [ ] `ModuleRepository.is_enabled(tenant_id, "manutencao")` retorna `True` para tenant com linha em `tenant_modules`.
- [ ] `ModuleRepository.is_enabled(tenant_id, "outro")` retorna `False` para módulo não liberado.
- [ ] `require_module("manutencao")` aplicada em uma rota de teste retorna 200 para tenant com módulo liberado.
- [ ] `require_module("manutencao")` retorna 404 para tenant sem o módulo (sem mensagem reveladora).
- [ ] `GET /auth/me` retorna `enabled_modules: ["manutencao"]` para tenant com módulo liberado.
- [ ] `GET /auth/me` retorna `enabled_modules: []` para tenant sem módulos liberados.
- [ ] Novo tenant provisionado via `TenantProvisioningService` tem `manutencao` liberado automaticamente.
- [ ] Isolamento: `is_enabled` de tenant A não retorna dados de tenant B.
- [ ] Cobertura de testes ≥ 90%.

## Estratégia de Testes

### Testes Unitários

- `ModuleRepository.is_enabled()`: tenant com linha → `True`; sem linha → `False`.
- `ModuleRepository.list_enabled_for_tenant()`: retorna apenas módulos do tenant correto.
- `require_module` dependency: módulo liberado → passa; não liberado → HTTPException 404.

### Testes de Integração

- `/auth/me` com tenant com `manutencao` liberado → `enabled_modules: ["manutencao"]`.
- `/auth/me` com tenant sem módulos → `enabled_modules: []`.
- Rota protegida com `require_module("manutencao")`: tenant liberado → 200; não liberado → 404.
- `TenantProvisioningService.provision()`: novo tenant tem linha em `tenant_modules`.
- Isolamento de tenant: `is_enabled` com `tenant_id` de outro tenant → `False` mesmo que
  o módulo esteja liberado para o tenant original.

### Testes E2E

Não aplicável nesta spec (mudanças apenas no backend/contrato de API).

## Riscos Técnicos

- **Risco:** tenants existentes em produção não terão o módulo liberado após a migration.
  **Mitigação:** data script na própria migration que libera `manutencao` para todos os
  tenants ativos (`is_active = true, deleted_at IS NULL`) no momento do `alembic upgrade`.
- **Risco:** o `/auth/me` pode ficar lento com query adicional de módulos.
  **Mitigação:** query simples com JOIN direto em `tenant_modules` + `modules`; mesma
  estratégia já usada para permissões. Cache Redis pode ser adicionado em v1.1.

## Complexidade

**Baixa** — 2 tabelas novas, 1 repository, 1 dependency e extensão de 1 endpoint.
Sem alteração de lógica de domínio existente.

## Prioridade

**Crítica** — fundação que todas as outras specs do HUB dependem.

## Branch

`feature/020-hub-modulos`
