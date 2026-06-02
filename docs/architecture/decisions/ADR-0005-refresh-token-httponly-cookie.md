---
id: ADR-0005
title: "Refresh token transportado via httpOnly cookie, não via response body"
status: accepted
date: 2026-06-02
supersedes: ~
superseded_by: ~
---

# ADR-0005 — Refresh token transportado via httpOnly cookie

## Contexto

Ao implementar P03, precisamos decidir como o `refresh_token` é entregue ao cliente:

1. **Response body:** token retornado no JSON do `POST /login` e armazenado pelo cliente (localStorage ou memória).
2. **httpOnly cookie:** backend seta `Set-Cookie: refresh_token=...; HttpOnly; SameSite=Strict; Path=/api/v1/auth/refresh`, o token nunca é acessível por JavaScript.

O frontend (P02) já foi construído com `withCredentials: true` e o interceptor de refresh não lê o corpo do login — apenas `access_token`. Qualquer abordagem de body exigiria redesign do `AuthProvider`.

## Decisão

O `refresh_token` é transportado **exclusivamente** via cookie `httpOnly`.

- `POST /login` → resposta contém apenas `{ access_token, token_type, expires_in }`.
- Backend seta `Set-Cookie: refresh_token=<token>; HttpOnly; SameSite=Strict; Max-Age=604800; Path=/api/v1/auth/refresh`.
- `POST /refresh` lê o cookie automaticamente (sem corpo); resposta retorna novo `access_token` e renova o cookie.
- `POST /logout` invalida o token no banco e limpa o cookie (`Max-Age=0`).

## Consequências

### Positivas
- **Imune a XSS:** JavaScript não consegue ler o cookie `HttpOnly`.
- **Alinhado com o frontend existente:** `AuthProvider` já está implementado para esta abordagem.
- `SameSite=Strict` mitiga ataques CSRF no endpoint de refresh.
- Superfície de ataque menor: o refresh token não trafega no body de nenhuma resposta.

### Negativas / Trade-offs
- **Clientes nativos (mobile/CLI)** não gerenciam cookies automaticamente — precisarão de endpoint alternativo ou cabeçalho customizado no futuro.
- Requer `withCredentials: true` no axios e `allow_credentials=True` no CORS do FastAPI.
- `SameSite=Strict` pode causar problemas se o frontend e backend estiverem em domínios distintos em produção — neste caso migrar para `SameSite=Lax` com revisão de CSRF.

### Impacto em specs
- P03: implementação do cookie no `router.py` (Response com `set_cookie`).
- P02: `AuthProvider` já compatível — nenhuma mudança necessária.
- Deploy (P18): documentar `SESSION_COOKIE_DOMAIN` e configuração de HTTPS para `Secure` flag em produção.

## Alternativas consideradas

| Alternativa | Por que foi rejeitada |
|-------------|----------------------|
| Response body + localStorage | Vulnerável a XSS; localStorage persiste até limpeza manual |
| Response body + memória (in-memory) | Perde sessão ao recarregar a página; frontend precisaria de redesign |
| Body + Cookie (redundante) | Complexidade desnecessária; não acrescenta segurança |

## Referências

- OWASP: [Cheat Sheet — Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- P02 `AuthProvider.tsx`: `withCredentials: true` e interceptor de refresh sem ler body
- P03 spec: `docs/specs/003-autenticacao.md`
