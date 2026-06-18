---
id: P23
slug: hub-menu-rotas
status: done
version: 0.1.0
owner: jhowworks
depends_on: [P22]
satisfies: [RF-205, RF-206]
adrs: [ADR-0002, ADR-0006]
branch: feature/023-hub-menu-rotas
last_updated: 2026-06-15
---

# P23 — Menu e Rotas Modulares

## Objetivo

Tornar o menu lateral (Sidebar) e o router do frontend orientados a dados, exibindo apenas
os itens e rotas dos módulos liberados para a empresa do usuário. Proteger rotas de módulos
via guard `RequireModule`, garantindo que acesso por URL direta a módulo não liberado
redirecione para a Home do HUB.

## Escopo

- **Sidebar data-driven:** substituir o array estático `NAV_ITEMS` por itens derivados de
  `session.enabled_modules` filtrados contra o `MODULE_REGISTRY`.
  Cada módulo no registry declara seus `navItems` (label, ícone, rota).
- **`MODULE_REGISTRY` estendido:** cada `ModuleDefinition` ganha `navItems: NavItem[]`
  e `routes: RouteDefinition[]` (além do que foi criado em P22).
- **Guard `RequireModule`:** novo componente `frontend/src/shared/components/RequireModule.tsx`
  que verifica `hasModule(session, code)` e redireciona para `/` se falso.
- **Router atualizado:** rotas de módulo (tickets, equipments, setores, sla, dashboards, etc.)
  envolvidas em `RequireModule` com o código `"manutencao"`.
- **Título do shell:** `Sidebar.tsx` remove o texto hardcoded "Manutenção"; exibe nome do
  módulo ativo ou o nome da plataforma (configurável via `MODULE_REGISTRY`).
- Manter o link "Plataforma" com gate `system_admin` (inalterado).

## Fora do Escopo

- Aplicação de `require_module` no backend dos routers (P24).
- Lazy loading por módulo (todas as features ainda importadas no bundle; otimização futura).
- Menu multi-nível (suporte a sub-módulos) — evolução futura.

## Dependências

- **P22** (Home do HUB e Sessão Modular) — `MODULE_REGISTRY`, `hasModule`, `UserSession.enabled_modules`.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `Sidebar.tsx` | Alterada — menu data-driven via `MODULE_REGISTRY` |
| `router.tsx` | Alterada — rotas de módulo protegidas por `RequireModule` |
| `MODULE_REGISTRY` | Estendida — adiciona `navItems` e `routes` por módulo |
| `RequireModule.tsx` | Nova — guard de rota por módulo |

## APIs Necessárias

Nenhuma.

## Telas Necessárias

Nenhuma tela nova — alterações nos componentes existentes.

## Regras de Negócio

1. **Sidebar:** exibe itens apenas de módulos em `session.enabled_modules`. O link
   "Plataforma" continua gateado por `system_admin` (independente de módulo).
2. **`RequireModule`:** se `hasModule(session, code)` for falso, redireciona para `/`
   (Home do HUB). Não exibe página de "sem permissão" — redireciona silenciosamente.
3. **Rota de manutenção acessada por URL direta sem módulo:** `RequireModule` intercepta
   antes de renderizar o componente e redireciona para `/`.
4. **Loading de sessão:** `RequireModule` aguarda o carregamento da sessão antes de decidir
   (mesmo comportamento de `RequireAuth`).
5. **Módulo não no registry:** se `enabled_modules` incluir um código que não existe no
   `MODULE_REGISTRY`, nenhum item de menu é exibido para esse código (sem erro).

## Critérios de Aceite

- [ ] `MODULE_REGISTRY` inclui `navItems` para `manutencao` com os 7 itens do menu atual.
- [ ] `Sidebar.tsx` não contém mais o array `NAV_ITEMS` hardcoded.
- [ ] Usuário com `manutencao` liberado vê os 7 itens de menu (Dashboard, Chamados, Equipamentos, etc.).
- [ ] Usuário sem módulos liberados vê menu sem itens de produto (apenas link "Plataforma" se for system_admin).
- [ ] `RequireModule` existe em `shared/components/RequireModule.tsx`.
- [ ] Acessar `/tickets` sem o módulo `manutencao` liberado redireciona para `/`.
- [ ] Acessar `/tickets` com o módulo liberado renderiza normalmente.
- [ ] O mesmo comportamento se aplica a `/dashboard`, `/equipments`, `/sla`, `/setores`.
- [ ] Título do Sidebar não exibe mais "Manutenção" hardcoded.
- [ ] Link "Plataforma" continua aparecendo apenas para `system_admin`.
- [ ] Cobertura de testes ≥ 90% nos componentes alterados.

## Estratégia de Testes

### Testes Unitários

- `Sidebar` com sessão com módulo → exibe itens; sem módulo → sem itens de produto.
- `RequireModule` com módulo liberado → renderiza `<Outlet />`; sem módulo → `<Navigate to="/" />`.
- `MODULE_REGISTRY["manutencao"].navItems` contém os 7 itens esperados.

### Testes de Integração

- Sessão carregada com `enabled_modules: ["manutencao"]` → Sidebar exibe itens de manutenção.
- Sessão com `enabled_modules: []` → Sidebar sem itens de módulo.

### Testes E2E

- Usuário com módulo liberado: navega para `/tickets` via URL → sucesso.
- Usuário sem módulo: navega para `/tickets` via URL → redireciona para `/`.
- Usuário sem módulo: menu não exibe itens de manutenção.

## Riscos Técnicos

- **Risco:** `RequireModule` chamado antes de sessão carregada exibe flash de redirect.
  **Mitigação:** aguardar `isLoading === false` antes de avaliar (mesmo padrão de `RequireAuth`).
- **Risco:** módulo futuro esquece de registrar `navItems` no `MODULE_REGISTRY`.
  **Mitigação:** TypeScript força o tipo completo em `ModuleDefinition`; build falha se faltar.

## Complexidade

**Média** — envolve refatorar Sidebar e router, criar guard e estender o registry. Nenhuma lógica de domínio é alterada.

## Prioridade

**Alta** — sem esta spec, o sistema continua expondo rotas e menu de forma estática independente do módulo liberado.

## Branch

`feature/023-hub-menu-rotas`
