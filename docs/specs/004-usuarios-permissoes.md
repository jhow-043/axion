---
id: P04
slug: usuarios-permissoes
status: in-review
version: 1.0.0
owner: jhowworks
depends_on: [P01, P03]
satisfies: [RF-030, RF-031, RF-032, RF-033, RF-034, RF-035, RF-036, RNF-SEG-001]
adrs: [ADR-0001, ADR-0002]
branch: feature/004-usuarios-permissoes
last_updated: 2026-06-01
---

# P04 — Usuários e Permissões (RBAC)

## Objetivo

Gerenciar usuários dentro de cada tenant e controlar acesso a funcionalidades por meio de papéis e permissões. Fornecer a dependência `require_permission()` que todos os módulos usarão para proteger seus endpoints.

## Escopo

- CRUD de usuários (por tenant): criar, listar, detalhar, editar, ativar/desativar.
- Entidades: `users`, `roles`, `permissions`, `user_roles`.
- Papéis padrão provisionados em cada novo tenant: **Admin**, **Supervisor**, **Técnico**, **Solicitante**.
- Matriz de permissões por papel (definida abaixo).
- Dependência FastAPI `require_permission(permission_code: str)`: valida se o usuário corrente possui a permissão exigida; retorna `403` caso contrário.
- Seed de papéis e permissões padrão no provisionamento do tenant.
- Telas de gerenciamento de usuários e papéis.

## Fora do Escopo

- Autenticação/login (P03).
- Observadores de chamado — papel por chamado, não global (P09).
- Provisionamento do tenant em si (P18 / deploy).
- Permissões por equipe ou por chamado específico (granularidade futura).

## Dependências

- **P01** (Multi-Tenancy) — `BaseRepository` e ContextVar de tenant.
- **P03** (Autenticação) — `get_current_user()` fornece o usuário e seus papéis para `require_permission()`.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `users` | Nova tabela principal |
| `roles` | Nova tabela |
| `permissions` | Nova tabela |
| `user_roles` | Nova tabela (N:N users × roles) |
| `role_permissions` | Nova tabela (N:N roles × permissions) |

### `users`
```
id              UUID, PK
tenant_id       UUID, FK → tenants, INDEX
name            String, NOT NULL
email           String, NOT NULL
                UNIQUE(tenant_id, email)
password_hash   String, NOT NULL
is_active       Boolean, DEFAULT true
created_at      DateTime
updated_at      DateTime
```

### `roles`
```
id          UUID, PK
tenant_id   UUID, FK → tenants, INDEX
name        String, NOT NULL            # ex.: "Admin", "Técnico"
code        String, NOT NULL            # ex.: "admin", "technician"
is_default  Boolean, DEFAULT false      # papel do sistema (não excluível)
             UNIQUE(tenant_id, code)
```

### `permissions`
```
id      UUID, PK
code    String, UNIQUE                  # ex.: "ticket:create", "user:manage"
name    String, NOT NULL               # ex.: "Criar Chamado"
```

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/users` | Listar usuários do tenant (paginado, filtros) | `user:read` |
| POST | `/api/v1/users` | Criar usuário | `user:manage` |
| GET | `/api/v1/users/{id}` | Detalhar usuário | `user:read` |
| PATCH | `/api/v1/users/{id}` | Editar usuário | `user:manage` |
| POST | `/api/v1/users/{id}/activate` | Ativar usuário | `user:manage` |
| POST | `/api/v1/users/{id}/deactivate` | Desativar usuário | `user:manage` |
| GET | `/api/v1/users/{id}/roles` | Listar papéis do usuário | `user:read` |
| POST | `/api/v1/users/{id}/roles` | Atribuir papel | `user:manage` |
| DELETE | `/api/v1/users/{id}/roles/{role_id}` | Remover papel | `user:manage` |
| GET | `/api/v1/roles` | Listar papéis disponíveis | `user:read` |
| GET | `/api/v1/permissions` | Listar permissões | `user:manage` |

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Lista de Usuários | Tabela paginada com filtro por nome/email/status/papel |
| Formulário de Usuário | Criar/editar: nome, email, senha inicial, papel |
| Detalhe do Usuário | Dados + papéis atribuídos + ações (ativar/desativar) |
| Atribuição de Papéis | Selecionar papéis para o usuário |

## Regras de Negócio

1. **Email único por tenant:** `UNIQUE(tenant_id, email)` — o mesmo email pode existir em tenants diferentes.
2. **Usuário inativo não autentica** (verificado em P03).
3. **Admin não pode remover o próprio papel de Admin** — deve existir pelo menos um Admin ativo por tenant.
4. **Papéis padrão** (Admin, Supervisor, Técnico, Solicitante) são criados automaticamente no provisionamento do tenant e marcados como `is_default = true`. Não podem ser excluídos, apenas editados no nome.
5. **Criação de usuário:** a senha inicial é gerada ou fornecida pelo admin. No primeiro login, exigir troca de senha (flag `must_change_password` — registrar como evolução imediata pós-MVP).
6. **Permissões agregadas:** o usuário tem o conjunto-união das permissões de todos os seus papéis.

## Matriz de Permissões Padrão

| Permissão | Código | Admin | Supervisor | Técnico | Solicitante |
|-----------|--------|-------|-----------|---------|-------------|
| Gerenciar usuários | `user:manage` | ✓ | | | |
| Visualizar usuários | `user:read` | ✓ | ✓ | | |
| Gerenciar equipes | `team:manage` | ✓ | ✓ | | |
| Criar chamado | `ticket:create` | ✓ | ✓ | ✓ | ✓ |
| Listar/ver chamados | `ticket:read` | ✓ | ✓ | ✓ | ✓* |
| Assumir chamado | `ticket:assign` | ✓ | ✓ | ✓ | |
| Transicionar chamado | `ticket:transition` | ✓ | ✓ | ✓ | |
| Validar solução | `ticket:validate` | ✓ | ✓ | | ✓** |
| Ver dashboards operacionais | `dashboard:operational` | ✓ | ✓ | ✓ | |
| Ver dashboard gerencial | `dashboard:management` | ✓ | ✓ | | |
| Gerenciar configurações | `admin:config` | ✓ | | | |
| Ver equipamentos | `equipment:read` | ✓ | ✓ | ✓ | ✓ |
| Gerenciar equipamentos | `equipment:manage` | ✓ | ✓ | | |

\* Solicitante vê apenas chamados que abriu ou onde é observador.
\*\* Solicitante só valida chamados que ele abriu.

## Critérios de Aceite

- [ ] CRUD completo de usuários com isolamento de tenant.
- [ ] `require_permission("user:manage")` bloqueia (403) usuário sem a permissão.
- [ ] Admin não consegue remover o próprio papel de Admin se for o único.
- [ ] Papéis padrão criados automaticamente no provisionamento.
- [ ] Permissões agrupadas por papel retornadas em `GET /auth/me`.
- [ ] Usuário inativo não autentica (verificado via P03).
- [ ] Email duplicado no mesmo tenant retorna erro de validação.
- [ ] Tela de usuários exibe lista paginada com filtros.

## Estratégia de Testes

### Testes Unitários

- Resolução de permissões: usuário com papéis A e B → tem a união das permissões.
- Validação: email duplicado no mesmo tenant → erro; mesmo email em tenant diferente → ok.
- Guard de admin único: remoção do último admin → erro.

### Testes de Integração

- `POST /users` com `user:manage` → usuário criado com tenant_id correto.
- `POST /users` sem `user:manage` → 403.
- `GET /users` → lista apenas usuários do tenant do solicitante.
- `POST /users/{id}/roles` → papel atribuído → `GET /auth/me` retorna papel.
- `require_permission()` como dependência em endpoint de teste → bloqueia/permite corretamente.

### Testes E2E

- Admin cria técnico → técnico loga → vê apenas o permitido para seu papel.
- Supervisor tenta acessar configurações → 403.
- Admin tenta remover o próprio papel de Admin sozinho → erro.

## Riscos Técnicos

- **Consistência da matriz de permissões entre módulos:** cada módulo que usa `require_permission()` deve usar um código de permissão existente. Registrar todos os códigos em um arquivo central (`core/permissions.py`).
- **Mudança de papel em sessão ativa:** papéis são lidos do banco a cada request (via `get_current_user()`), não apenas do token. Garante consistência sem exigir relogin.
- **Performance:** leitura de papéis e permissões a cada request — considerar cache em memória (Redis) para o conjunto de permissões por papel.

## Complexidade

**Média** — padrão RBAC bem estabelecido; o risco está na consistência dos códigos de permissão entre módulos.

## Prioridade

**Crítica** — `require_permission()` é bloqueador de todos os endpoints protegidos dos demais módulos.

## Branch

`feature/004-usuarios-permissoes`
