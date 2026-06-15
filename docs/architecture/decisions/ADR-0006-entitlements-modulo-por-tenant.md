---
id: ADR-0006
title: "Catálogo global de módulos e liberação por tenant"
status: accepted
date: 2026-06-15
supersedes: ~
superseded_by: ~
---

# ADR-0006 — Catálogo global de módulos e liberação por tenant

## Contexto

O projeto nasceu como um único produto de Gestão de Manutenção. A direção evoluiu para um
**HUB modular**, onde a mesma plataforma deve suportar múltiplos produtos/módulos e cada
empresa (tenant) enxerga apenas os módulos que lhe foram liberados.

Precisávamos decidir:
1. Como representar o catálogo de módulos disponíveis na plataforma.
2. Como vincular quais módulos cada empresa pode usar.
3. Como enforçar esse vínculo no backend sem criar complexidade desnecessária.
4. Como expor essa informação ao frontend para guiar navegação e rotas.

Restrições relevantes:
- Sem billing, sem planos, sem cotas na v1 — apenas liga/desliga simples por empresa.
- O padrão de segurança do sistema (cross-tenant → 404, ADR-0002) deve ser preservado.
- A adição deve ser **aditiva** — sem refatorar código de manutenção existente.

## Decisão

### 1. Modelo de dados (2 tabelas novas)

**`modules`** — catálogo global, **sem `tenant_id`** (pertence à plataforma, não a um tenant):
- `code` único (ex.: `"manutencao"`) — identificador estável usado no código e no frontend.
- `name`, `description`, `icon`, `sort_order`, `is_active`.
- Semente inicial: 1 linha com `code = "manutencao"`.

**`tenant_modules`** — vínculo tenant ↔ módulo liberado:
- `tenant_id` + `module_id`, constraint UNIQUE.
- `enabled_at` — quando foi liberado (rastreabilidade mínima).
- Presença da linha = módulo ativo. Ausência = módulo não liberado.
- Sem `TenantMixin` (a tabela já é scoped por `tenant_id`); sem `BaseRepository` (consulta
  cruzada controlada apenas pela camada de admin).

### 2. Backend — dependency `require_module(code)`

Nova factory em `app/core/deps.py`, espelhando exatamente o padrão de `require_permission`:

```python
def require_module(module_code: str) -> Callable:
    async def _check(current_user=Depends(get_current_user), db=Depends(get_db)):
        repo = ModuleRepository(db)
        if not await repo.is_enabled(current_user.tenant_id, module_code):
            raise HTTPException(status_code=404, detail="Recurso não encontrado.")
        return current_user
    return _check
```

- Retorna **404** (não 403) quando o módulo não está liberado — coerente com ADR-0002
  (não revela a existência do recurso para quem não tem acesso).
- Aplicada nos routers do módulo `manutencao` e em qualquer módulo futuro.

### 3. `/auth/me` passa a retornar `enabled_modules`

O endpoint `/auth/me` inclui `enabled_modules: list[str]` (lista de `module.code` liberados
para o tenant do usuário autenticado). O frontend usa esse campo para:
- Decidir quais cards mostrar na Home do HUB.
- Filtrar os itens do menu lateral.
- Decidir quais rotas registrar / quais bloquear.

### 4. Gestão pelo super-admin

Endpoints sob `/api/v1/admin/platform/modules/` (requer `system_admin`):
- Listar catálogo global de módulos.
- Listar módulos liberados por empresa.
- Liberar / revogar módulo para uma empresa.

### 5. Seed automático no provisionamento de tenant

Ao criar um novo tenant (P18/P19), o serviço de provisionamento libera automaticamente o
módulo `manutencao` — mantendo compatibilidade total com tenants existentes.

## Consequências

### Positivas
- **Aditivo:** nenhum código de manutenção existente é alterado na fase de núcleo; apenas
  os routers ganham `require_module` na fase de consolidação.
- **Consistência:** o padrão de gating (404, DB lookup por request) é idêntico ao de
  permissões — curva de aprendizado zero para o time.
- **Extensível:** novos módulos entram com 1 linha no seed + registro no frontend, sem
  mudança de arquitetura.
- **Sem complexidade prematura:** sem planos, billing ou cotas na v1.

### Negativas / Trade-offs
- Módulos verificados no banco a cada request (como permissões) — sem cache na v1.
  Aceitável; adicionar cache Redis é evolução simples se houver pressão de latência.
- `modules` é uma tabela global sem isolamento de tenant — o super-admin pode ver e gerenciar
  todos. É o comportamento desejado, mas requer cuidado ao adicionar endpoints administrativos.
- O frontend precisa de lógica dinâmica no Sidebar e no router; substitui o array estático
  `NAV_ITEMS` — mudança necessária mas não trivial.

### Impacto em specs
- **P20** — tabelas, `require_module`, `enabled_modules` no `/auth/me`.
- **P21** — endpoints e UI de gestão de módulos no super-admin.
- **P22** — home do HUB, `MODULES` registry no frontend, `UserSession.enabled_modules`.
- **P23** — Sidebar e router modulares, guard `RequireModule`.
- **P24** — aplicar `require_module` nos routers do módulo `manutencao`.

## Alternativas consideradas

| Alternativa | Por que foi rejeitada |
|-------------|----------------------|
| Planos/pacotes com agrupamento de módulos | Complexidade desnecessária na v1; evolução futura quando houver pressão de negócio |
| Feature flags via env var por tenant | Não escala; impede gestão em runtime; sem UI |
| Permissão RBAC para cada módulo (ex.: `manutencao:access`) | Confunde permissão de *papel* com entitlement de *produto*; forçaria criar papel por módulo |
| Retornar 403 quando módulo não liberado | Viola ADR-0002 — não revela a existência do recurso para quem não tem acesso |
| Tabela `tenant_modules` com `TenantMixin` | `TenantMixin` impede queries cross-tenant necessárias para o super-admin; a coluna `tenant_id` explícita já garante isolamento |

## Referências

- ADR-0001 — Isolamento via BaseRepository: `docs/architecture/decisions/ADR-0001-*.md`
- ADR-0002 — Cross-tenant retorna 404: `docs/architecture/decisions/ADR-0002-*.md`
- P19 — Plataforma super-admin (origem da área de gestão): `docs/specs/019-*.md`
- Plano de transformação HUB: `.claude/plans/voc-vai-me-ajudar-cozy-lerdorf.md`
