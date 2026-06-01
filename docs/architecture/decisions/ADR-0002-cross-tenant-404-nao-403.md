---
id: ADR-0002
title: "Acesso cross-tenant retorna 404, não 403"
status: accepted
date: 2026-06-01
supersedes: ~
superseded_by: ~
---

# ADR-0002 — Acesso cross-tenant retorna 404, não 403

## Contexto

Quando um usuário do tenant A tenta acessar um recurso que existe no tenant B
(ex.: `GET /api/v1/tickets/{id}` com o UUID de um ticket do tenant B), precisamos
decidir qual HTTP status retornar.

A resposta natural seria `403 Forbidden`, mas isso revela que o recurso *existe* —
um atacante que enumera UUIDs aleatórios saberia quais IDs existem em outros tenants.

## Decisão

Acesso cross-tenant retorna sempre `404 Not Found`, nunca `403 Forbidden`.

O `BaseRepository.get(id)` com ID de outro tenant retorna `None` (o filtro `WHERE tenant_id`
exclui o resultado). O router trata `None` como 404.

Do ponto de vista do usuário e do atacante, o recurso simplesmente "não existe" para eles.

## Consequências

### Positivas
- Não revela a existência de recursos de outros tenants (evita IDOR via enumeração).
- Comportamento consistente: a mesma mensagem genérica para "não encontrado" e "não autorizado cross-tenant".
- Simplifica o código do router — uma única verificação `if not resource: raise 404`.

### Negativas / Trade-offs
- Diagnóstico mais difícil quando um desenvolvedor acidentalmente usa o ID de tenant errado
  em desenvolvimento — o erro é silencioso.
- Logs devem registrar o tenant do recurso buscado vs. tenant do usuário para auditoria
  (mas não expor isso na resposta).

### Impacto em specs
- P01 define e testa este comportamento.
- Todos os módulos que implementam `GET /{id}` devem seguir este padrão.
- P17 (auditoria) pode registrar tentativas cross-tenant nos logs internos.

## Alternativas consideradas

| Alternativa | Por que foi rejeitada |
|-------------|----------------------|
| `403 Forbidden` para cross-tenant | Revela existência do recurso — vulnerabilidade IDOR |
| `404` apenas para GET, `403` para POST/DELETE | Inconsistência; POST cross-tenant ainda vazaria info via corpo de erro diferente |
| Mensagem de erro específica no 404 indicando isolamento | Ainda revelaria que o recurso existe em outro contexto |

## Referências

- OWASP: Broken Object Level Authorization (BOLA/IDOR)
- P01 spec: `docs/specs/001-multi-tenancy.md`
- Constituição, INV-02: `docs/constitution.md`
