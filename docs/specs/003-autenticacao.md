---
id: P03
slug: autenticacao
status: approved
version: 1.0.0
owner: jhowworks
depends_on: [P00, P01, P02, P04]
satisfies: [RF-020, RF-021, RF-022, RF-023, RF-024, RF-025, RF-026, RNF-SEG-002, RNF-SEG-003, RNF-SEG-004]
adrs: [ADR-0001, ADR-0002]
branch: feature/003-autenticacao
last_updated: 2026-06-01
---

# P03 — Autenticação

## Objetivo

Autenticar usuários da plataforma com segurança, emitir e renovar tokens JWT, e expor o contrato de identidade do usuário corrente que todos os módulos protegidos irão consumir.

## Escopo

- Endpoint de login: verificação de email + senha (Argon2), emissão de `access_token` (curta duração, ex.: 15 min) e `refresh_token` (longa duração, ex.: 7 dias).
- Endpoint de refresh: validação do `refresh_token`, emissão de novo par de tokens (rotação de refresh).
- Endpoint de logout: invalidação do `refresh_token` (blocklist em Redis ou flag no banco).
- Endpoint `me`: retorna dados do usuário autenticado (id, nome, email, tenant_id, papéis).
- Payload JWT: `sub` (user_id), `tenant_id`, `roles`, `iat`, `exp`.
- Dependência FastAPI `get_current_user()`: valida o token Bearer, resolve o usuário e configura o ContextVar de tenant (integração com P01).
- Hashing de senha com Argon2 (via `passlib[argon2]`).
- Tela de Login completa no frontend (integração com P02).
- Guard de rota no frontend por autenticação (sem papel — apenas "está logado").

## Fora do Escopo

- RBAC e verificação de permissões (P04).
- Cadastro de usuários (P04 — apenas admin pode criar usuários).
- Recuperação de senha (futuro).
- AD/LDAP/SSO (futuro).
- Multi-fator (futuro).

## Dependências

- **P00** (Fundação Backend) — deps, exceptions, config.
- **P01** (Multi-Tenancy) — a dependência `get_current_user()` configura o ContextVar de tenant.
- **P02** (Fundação Frontend) — `AuthProvider` e client HTTP prontos para integrar o fluxo de login.
- **P04** (Usuários) — lê a entidade `User` para verificar credenciais e retornar dados. *Coordenação:* P04 define o modelo `User`; P03 acessa apenas os campos de credenciais (email, password_hash, is_active, tenant_id, roles). Implementar P04 antes ou em paralelo com alinhamento de contrato.

## Entidades Impactadas

| Entidade | Ação | Nota |
|----------|------|------|
| `users` | Leitura (email, password_hash, is_active, tenant_id) | Definida em P04 |
| `refresh_tokens` | Nova tabela (ou blocklist Redis) | Gerenciada por P03 |

Estrutura de `refresh_tokens` (se persistido em banco):
```
id            UUID, PK
user_id       UUID, FK → users
token_hash    String, UNIQUE         # hash do refresh token
expires_at    DateTime
revoked_at    DateTime, nullable
created_at    DateTime
```

## APIs Necessárias

| Método | Rota | Descrição | Autenticação |
|--------|------|-----------|-------------|
| POST | `/api/v1/auth/login` | Login com email + senha | Pública |
| POST | `/api/v1/auth/refresh` | Renovar tokens com refresh_token | Pública (token no body/cookie) |
| POST | `/api/v1/auth/logout` | Invalidar refresh_token | Bearer token |
| GET | `/api/v1/auth/me` | Dados do usuário autenticado | Bearer token |

**POST `/api/v1/auth/login`** — Request:
```json
{ "email": "tecnico@empresa.com", "password": "senha123" }
```
Response `200`:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```
Response `401` (credenciais inválidas — mensagem genérica):
```json
{ "error": "INVALID_CREDENTIALS", "message": "Email ou senha incorretos." }
```

**GET `/api/v1/auth/me`** — Response `200`:
```json
{
  "id": "uuid",
  "name": "João Silva",
  "email": "tecnico@empresa.com",
  "tenant_id": "uuid",
  "roles": ["technician"],
  "is_active": true
}
```

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Login | Formulário (email + senha), validação client-side, exibição de erro de credenciais, redirect pós-login |

## Regras de Negócio

1. **Senha nunca em texto claro:** comparação sempre via `passlib.verify(plain, hash)`.
2. **Resposta genérica de erro:** login inválido retorna sempre a mesma mensagem, independente de o email existir ou não (evita user enumeration).
3. **Usuário inativo:** não autentica — retorna a mesma mensagem genérica de credenciais inválidas.
4. **Rotação de refresh token:** a cada refresh, o token antigo é revogado e um novo par é emitido.
5. **Refresh token revogado:** tentativa de uso de token revogado invalida **todos** os tokens do usuário (sinalizador de roubo de token).
6. **Expiração do access token:** 15 minutos (configurável em `core/config.py`).
7. **Expiração do refresh token:** 7 dias (configurável).
8. **ContextVar de tenant:** a dependência `get_current_user()` deve configurar o ContextVar de tenant (P01) imediatamente após validar o token.

## Critérios de Aceite

- [ ] Login com credenciais válidas retorna `access_token` e `refresh_token`.
- [ ] Login com senha errada retorna `401` com mensagem genérica.
- [ ] Login com email inexistente retorna `401` com a **mesma** mensagem genérica.
- [ ] Login com usuário inativo retorna `401`.
- [ ] `GET /api/v1/auth/me` com token válido retorna dados do usuário.
- [ ] `GET /api/v1/auth/me` com token expirado retorna `401`.
- [ ] `POST /api/v1/auth/refresh` com token válido retorna novo par; token antigo é revogado.
- [ ] `POST /api/v1/auth/refresh` com token revogado invalida todos os tokens do usuário.
- [ ] `POST /api/v1/auth/logout` revoga o refresh token.
- [ ] ContextVar de tenant configurado corretamente após `get_current_user()`.
- [ ] Tela de login: erro de credenciais exibido; redirect pós-login para rota original.

## Estratégia de Testes

### Testes Unitários

- `verify_password(plain, hash)` → correto e incorreto.
- `create_access_token(data, expires_delta)` → payload correto, expiração correta.
- `decode_token(token)` → token válido, expirado, inválido.
- Rotação de refresh: revogação do antigo ao emitir novo.

### Testes de Integração

- `POST /login` → usuário válido → tokens emitidos com payload correto.
- `POST /login` → credenciais inválidas → `401` genérico.
- `POST /login` → usuário inativo → `401` genérico.
- `GET /me` → token válido → dados do usuário com tenant_id e roles.
- `GET /me` → sem token → `401`.
- `POST /refresh` → token válido → novo par; antigo revogado.
- `POST /refresh` → token revogado → todos os tokens do usuário invalidados.
- `POST /logout` → token revogado com sucesso.

### Testes E2E

- Usuário navega para rota privada → redirect para login → preenche credenciais → logado → vê dashboard.
- Usuário com senha errada → mensagem de erro → permanece na tela de login.
- Sessão expira enquanto usa o sistema → refresh silencioso → continua usando.
- Logout → redirect para login → `me` retorna `401`.

## Riscos Técnicos

- **Rotação de refresh e race condition:** múltiplas requisições simultâneas com o mesmo refresh token antes da rotação — implementar lock ou aceitar idempotência na janela curta.
- **Armazenamento do refresh token:** decisão de cookie `httpOnly` vs. localStorage impacta configuração de CORS no backend e segurança XSS/CSRF.
- **Chave de assinatura JWT:** rotação de chave sem invalidar todas as sessões ativas requer suporte a múltiplas chaves válidas simultaneamente — registrar como item de evolução.

## Complexidade

**Média** — os padrões de segurança são bem definidos, mas requerem atenção a detalhes.

## Prioridade

**Crítica** — bloqueador de todos os endpoints protegidos.

## Branch

`feature/003-autenticacao`
