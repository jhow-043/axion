---
id: P22
slug: hub-home-modular
status: draft
version: 0.1.0
owner: jhowworks
depends_on: [P02, P20]
satisfies: [RF-202, RF-204]
adrs: [ADR-0006]
branch: feature/022-hub-home-modular
last_updated: 2026-06-15
---

# P22 — Home do HUB e Sessão Modular (Frontend)

## Objetivo

Atualizar a sessão do frontend para incluir `enabled_modules`, criar o registro declarativo
de módulos (`ModuleRegistry`) e implementar a Home do HUB — tela inicial que exibe os cards
dos módulos liberados para a empresa do usuário logado.

## Escopo

- `UserSession` em `frontend/src/types/api.ts` ganha o campo `enabled_modules: string[]`.
- Helper `hasModule(session, code)` em `frontend/src/utils/permissions.ts`.
- `MODULE_REGISTRY` — array declarativo em `frontend/src/config/modules.ts`:
  cada entrada define `code`, `label`, `icon`, `description`, `homeRoute`.
  É a fonte de verdade para Sidebar (P23) e Home do HUB.
- Tela `HubHome` em `frontend/src/features/hub/components/HubHome.tsx`:
  grid de cards filtrado por `session.enabled_modules`. Clique no card navega para
  `module.homeRoute`.
- Rota `/` (index) passa a renderizar `HubHome` em vez de `DashboardRedirect`.
- `DashboardRedirect` é mantido como rota acessível diretamente em `/dashboard` (sem mudança
  no redirect baseado em papel para quem já está na área de manutenção).
- `AuthProvider` já busca `/auth/me` — nenhuma mudança necessária; `enabled_modules` vem
  automaticamente após P20.

## Fora do Escopo

- Alterações no Sidebar ou no router de rotas protegidas (P23).
- Guard de acesso a rota por módulo (P23).
- Qualquer UI de gestão de módulos (P21).

## Dependências

- **P02** (Fundação Frontend) — `AuthProvider`, `UserSession`, `useAuth`.
- **P20** (Núcleo de Módulos) — `/auth/me` retornando `enabled_modules`.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `UserSession` (tipo TS) | Alterada — adiciona `enabled_modules: string[]` |
| `MODULE_REGISTRY` | Nova — configuração declarativa de módulos |
| `HubHome` | Nova tela — home do HUB |
| Rota `/` (index) | Alterada — aponta para `HubHome` |

## APIs Necessárias

Nenhuma nova — consome `GET /auth/me` já atualizado pela P20.

## Telas Necessárias

| Tela | Rota | Descrição |
|------|------|-----------|
| `HubHome` | `/` (index) | Grid de cards com os módulos liberados para a empresa |

### Comportamento da `HubHome`

- Exibe 1 card por módulo em `session.enabled_modules` que também exista no `MODULE_REGISTRY`.
- Card contém: ícone, nome do módulo, descrição curta, botão/link "Acessar".
- Clique navega para `module.homeRoute` (ex.: `/dashboard` para `manutencao`).
- Empresa sem módulos liberados: mensagem "Nenhum módulo disponível. Entre em contato com o administrador."
- Loading state enquanto a sessão é carregada.

### `MODULE_REGISTRY` (exemplo)

```ts
// frontend/src/config/modules.ts
export const MODULE_REGISTRY: ModuleDefinition[] = [
  {
    code: "manutencao",
    label: "Gestão de Manutenção",
    description: "Chamados, SLA, equipamentos e dashboards operacionais.",
    icon: "Wrench",
    homeRoute: "/dashboard",
  },
];
```

## Regras de Negócio

1. **Filtro por sessão:** `HubHome` exibe apenas módulos cujo `code` está em `session.enabled_modules`
   E cujo `code` existe no `MODULE_REGISTRY`. Módulos liberados sem entrada no registry são ignorados
   (proteção contra inconsistência de dados sem travar a UI).
2. **Sem módulos:** exibe mensagem orientando a contatar o administrador; não exibe erro.
3. **Session loading:** durante o carregamento inicial da sessão, exibe skeleton/spinner.
4. **`hasModule(session, code)`:** retorna `true` se `code` está em `session.enabled_modules`.
   Pode retornar `false` para sessão nula (sem throw).

## Critérios de Aceite

- [ ] `UserSession.enabled_modules` tipado como `string[]` em `types/api.ts`.
- [ ] `hasModule(session, "manutencao")` retorna `true` quando `enabled_modules` inclui o código.
- [ ] `hasModule(null, "manutencao")` retorna `false` sem erro.
- [ ] `MODULE_REGISTRY` exporta ao menos a entrada `manutencao` com todos os campos obrigatórios.
- [ ] Rota `/` renderiza `HubHome` (não mais `DashboardRedirect`).
- [ ] `HubHome` com sessão contendo `enabled_modules: ["manutencao"]` exibe 1 card de Manutenção.
- [ ] `HubHome` com `enabled_modules: []` exibe mensagem de "nenhum módulo disponível".
- [ ] Clique no card "Gestão de Manutenção" navega para `/dashboard`.
- [ ] Empresa com `manutencao` liberado: usuário faz login e vê o card na home.
- [ ] Testes unitários de `hasModule` e `HubHome` (renderização condicional).

## Estratégia de Testes

### Testes Unitários

- `hasModule(session, code)`: sessão com módulo → `true`; sem → `false`; nula → `false`.
- `HubHome` render com 1 módulo → 1 card; sem módulos → mensagem.
- `MODULE_REGISTRY` contém entrada para `manutencao` com campos obrigatórios.

### Testes de Integração

- Login completo → `/auth/me` com `enabled_modules` → `HubHome` exibe card.

### Testes E2E

- Usuário com `manutencao` liberado faz login → vê Home do HUB com card → clica → vai para `/dashboard`.
- Usuário sem módulos faz login → vê mensagem de "nenhum módulo disponível".

## Riscos Técnicos

- **Risco:** `DashboardRedirect` ainda sendo usado em links internos após esta spec.
  **Mitigação:** manter `DashboardRedirect` funcional em `/dashboard`; apenas o index `/` muda.

## Complexidade

**Baixa** — tipo atualizado + helper + componente novo + rota redirecionada. Sem refatoração de features existentes.

## Prioridade

**Alta** — é a experiência de entrada do HUB; sem ela, o usuário não tem uma home modular.

## Branch

`feature/022-hub-home-modular`
