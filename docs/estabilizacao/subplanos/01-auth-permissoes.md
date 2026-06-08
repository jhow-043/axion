# Subplano 01 — Autenticação e Permissões

**Specs:** P03 (Autenticação), P04 (Usuários e RBAC)
**Prioridade:** 🔴 Crítico — bloqueia todo o resto se quebrado
**Status diagnóstico:** ⏳ Pendente

---

## Escopo das specs

### P03 — Autenticação
- Login: email + senha (Argon2), JWT access (15 min) + refresh (7 dias, HttpOnly cookie)
- Endpoints: `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`
- Refresh: novo par de tokens, revoga o anterior; logout invalida refresh token
- JWT payload: `sub`, `tenant_id`, `roles`, `iat`, `exp`
- `get_current_user()` seta ContextVar `tenant_id`
- Frontend: LoginPage, AuthProvider, interceptor 401 para refresh automático

### P04 — RBAC
- `require_permission(code)` como dependência FastAPI → 403 se não concedido
- 4 papéis default: Admin, Supervisor, Técnico, Solicitante (seeded por tenant)
- 13 permissões definidas em `app/core/permissions.py`
- Endpoints de roles/permissions montados em `/api/v1/roles` e `/api/v1/permissions`

---

## Arquivos relevantes

### Backend
- `backend/app/modules/auth/router.py`
- `backend/app/modules/auth/service.py`
- `backend/app/modules/auth/models.py` (RefreshToken)
- `backend/app/core/security.py` (JWT, Argon2)
- `backend/app/core/deps.py` (`get_current_user`, `require_permission`, `require_system_admin`)
- `backend/app/core/permissions.py`
- `backend/app/modules/users/seed.py`

### Frontend
- `frontend/src/features/auth/` (LoginPage, api.ts, types.ts)
- `frontend/src/app/providers/AuthProvider.tsx`
- `frontend/src/shared/api/client.ts` (interceptor 401/refresh)
- `frontend/src/app/router.tsx` (RequireAuth)

---

## Fluxos a validar

- [ ] Login com credenciais corretas → recebe access token, cookie refresh
- [ ] Login com credenciais erradas → mensagem genérica (sem vazar info)
- [ ] Usuário inativo → rejeitado no login
- [ ] GET /auth/me → retorna id, nome, email, tenant_id, roles
- [ ] Token expirado → frontend faz refresh automático, requisição refeita
- [ ] Refresh inválido/expirado → logout forçado (redirect para /login)
- [ ] Logout → refresh token invalidado; próximo refresh retorna 401
- [ ] `require_permission("ticket:create")` → 403 para papel sem permissão
- [ ] `require_permission("ticket:create")` → 200 para papel com permissão
- [ ] Tenant inativo → requisição autenticada rejeitada
- [ ] Cross-tenant no JWT → retorna 404, não 403

---

## Problemas catalogados (Fase A)

| EST-ID | Classificação | Descrição | Arquivo:Linha | Reprodução |
|--------|--------------|-----------|---------------|------------|
| — | — | *A preencher* | — | — |

---

## Notas de risco

- Se `get_current_user()` não seta o ContextVar corretamente, **todos** os módulos tenant-scoped falham.
- Drift de porta no `seed_dev.py` (imprime `:3001`; Vite usa `:5173`) pode indicar CORS mal configurado.
- Verificar se CORS permite `http://localhost:5173` com `credentials: true`.
