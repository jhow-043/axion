---
id: P21
slug: hub-admin-modulos
status: in-review
version: 0.1.0
owner: jhowworks
depends_on: [P19, P20]
satisfies: [RF-201, RF-207]
adrs: [ADR-0002, ADR-0006]
branch: feature/021-hub-admin-modulos
last_updated: 2026-06-15
---

# P21 — Gestão de Módulos no Super-Admin

## Objetivo

Expor endpoints de gestão de módulos para o super-administrador (listar catálogo, ver quais
módulos cada empresa tem liberados, liberar e revogar módulos por empresa) e criar a UI
correspondente dentro da área `/plataforma` já existente (P19).

## Escopo

### Backend
- `GET /api/v1/admin/platform/modules` — lista o catálogo global de módulos.
- `GET /api/v1/admin/platform/tenants/{tenant_id}/modules` — lista módulos liberados por empresa.
- `POST /api/v1/admin/platform/tenants/{tenant_id}/modules` — libera um módulo para a empresa.
- `DELETE /api/v1/admin/platform/tenants/{tenant_id}/modules/{module_id}` — revoga módulo.
- Todos protegidos por `require_system_admin()`.
- Todos retornam 404 se o tenant não existir (ADR-0002).

### Frontend
- Nova seção **"Módulos"** na área `/plataforma/empresas` (ou modal dentro de `CompanyList`).
- Visualização por empresa: lista de módulos do catálogo com toggle liga/desliga.
- Feedback visual ao liberar/revogar (toast + atualização da lista).

## Fora do Escopo

- CRUD de módulos no catálogo (adicionar/remover módulos do catálogo é operação de deploy).
- Histórico de liberações (audit log já cobre via P17).
- Billing, cotas ou limites de uso.
- Impersonation de tenant para testar o módulo.

## Dependências

- **P19** (Plataforma Super-Admin) — área `/plataforma`, `require_system_admin`, `CompanyList`.
- **P20** (Núcleo de Módulos) — tabelas `modules` e `tenant_modules`, `ModuleRepository`.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `modules` | Lida (catálogo) |
| `tenant_modules` | Criada / Removida (liberar / revogar) |

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/admin/platform/modules` | Listar catálogo de módulos | `system_admin` |
| GET | `/api/v1/admin/platform/tenants/{id}/modules` | Módulos liberados para a empresa | `system_admin` |
| POST | `/api/v1/admin/platform/tenants/{id}/modules` | Liberar módulo para a empresa | `system_admin` |
| DELETE | `/api/v1/admin/platform/tenants/{id}/modules/{module_id}` | Revogar módulo | `system_admin` |

### Body de `POST /api/v1/admin/platform/tenants/{id}/modules`
```json
{
  "module_id": "uuid-do-modulo"
}
```

### Response de `GET /api/v1/admin/platform/tenants/{id}/modules`
```json
{
  "catalog": [
    { "id": "uuid", "code": "manutencao", "name": "Gestão de Manutenção", "icon": "Wrench", "is_active": true }
  ],
  "enabled": [
    { "module_id": "uuid", "module_code": "manutencao", "enabled_at": "2026-06-15T..." }
  ]
}
```

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Seção "Módulos" em `CompanyList` / modal | Exibe catálogo com toggle liga/desliga por empresa |

## Regras de Negócio

1. **system_admin obrigatório:** todos os endpoints são protegidos por `require_system_admin()`.
2. **Liberar módulo inexistente:** retorna 404 se `module_id` não existir no catálogo.
3. **Liberar módulo já liberado:** idempotente — não gera erro (HTTP 200 ou 409 com mensagem clara).
4. **Revogar módulo não liberado:** retorna 404.
5. **Tenant inexistente:** retorna 404 (ADR-0002 — não revela a existência).
6. **Módulo `manutencao` é revogável:** não há proteção especial na v1; o super-admin tem controle total.

## Critérios de Aceite

- [ ] `GET /admin/platform/modules` retorna catálogo completo apenas para `system_admin`.
- [ ] Usuário sem `system_admin` em qualquer endpoint desta spec recebe 403.
- [ ] `GET /admin/platform/tenants/{id}/modules` mostra catálogo + quais estão liberados.
- [ ] `POST` libera módulo e a linha aparece em `tenant_modules`.
- [ ] `DELETE` remove a linha de `tenant_modules`; módulo some da lista de liberados.
- [ ] Tenant inexistente → 404 em qualquer endpoint de tenant.
- [ ] UI mostra toggle correto (on/off) por módulo por empresa.
- [ ] Liberar via UI → toast de confirmação + lista atualizada.
- [ ] Revogar via UI → confirmação antes de executar + toast + lista atualizada.
- [ ] Cobertura de testes ≥ 90%.

## Estratégia de Testes

### Testes Unitários

- `PlatformModuleService.enable_module()`: cria linha em `tenant_modules`; idempotente.
- `PlatformModuleService.revoke_module()`: remove linha; 404 se não existe.

### Testes de Integração

- `GET /admin/platform/modules` com `system_admin`: 200 + lista.
- `GET /admin/platform/modules` sem `system_admin`: 403.
- `POST` com tenant existente + módulo existente: 200 + linha criada.
- `POST` idempotente: segunda chamada não gera erro.
- `DELETE` existente: 204 + linha removida.
- `DELETE` não liberado: 404.
- Tenant inexistente em qualquer endpoint: 404.

### Testes E2E

- Super-admin acessa `/plataforma/empresas`, seleciona empresa, vê módulos, libera e revoga.

## Riscos Técnicos

- **Risco:** liberar módulo para tenant com dados inconsistentes. **Mitigação:** a liberação
  não afeta dados existentes; é puramente um entitlement.

## Complexidade

**Baixa** — 4 endpoints CRUD simples + extensão da UI já existente da área de plataforma.

## Prioridade

**Alta** — sem esta spec, o super-admin não consegue controlar quais módulos cada empresa tem.

## Branch

`feature/021-hub-admin-modulos`
