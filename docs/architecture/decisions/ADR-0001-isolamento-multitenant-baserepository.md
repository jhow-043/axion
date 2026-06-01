---
id: ADR-0001
title: "Isolamento de tenant via BaseRepository obrigatório"
status: accepted
date: 2026-06-01
supersedes: ~
superseded_by: ~
---

# ADR-0001 — Isolamento de tenant via BaseRepository obrigatório

## Contexto

O sistema é multi-tenant com isolamento por `tenant_id` em todas as tabelas de domínio.
O risco principal é que um módulo esqueça de aplicar o filtro de tenant em uma query,
expondo dados de um tenant para outro — uma falha de segurança crítica.

Precisávamos de uma estratégia que tornasse o comportamento seguro o *padrão* e o
comportamento inseguro (query sem filtro de tenant) explicitamente difícil ou impossível
no fluxo normal de desenvolvimento.

## Decisão

Todo acesso a dados de domínio deve usar o `BaseRepository`.
O `BaseRepository` aplica `WHERE tenant_id = :current_tenant_id` automaticamente em
todas as operações de leitura e seta `tenant_id` em todas as operações de escrita,
usando o `ContextVar` configurado pela dependência `get_current_user()`.

Queries SQLAlchemy diretas (sem herdar de `BaseRepository`) são proibidas em `service.py`
e `router.py`. A única exceção são scripts administrativos com autenticação explícita.

## Consequências

### Positivas
- O caminho feliz é seguro por padrão — o desenvolvedor não precisa lembrar de filtrar.
- Testes de isolamento de tenant são padronizados e reutilizáveis.
- Uma única camada de segurança para auditar (o `BaseRepository`).
- Reduz superfície de ataque: bug de isolamento só pode ocorrer no `BaseRepository`.

### Negativas / Trade-offs
- Todo novo módulo precisa herdar `BaseRepository` — um passo extra no bootstrap.
- Queries complexas que precisam de JOINs entre tenants diferentes (ex.: super-admin)
  precisam de mecanismo especial (ainda não definido — futuro).
- Code review deve verificar que nenhum módulo bypassa o `BaseRepository`.

### Impacto em specs
- Todas as specs que envolvem entidades de domínio (P01 e todos que herdam).
- P01 define e testa o `BaseRepository`.
- P17 (auditoria) também usa `BaseRepository`.

## Alternativas consideradas

| Alternativa | Por que foi rejeitada |
|-------------|----------------------|
| Row-Level Security (RLS) no PostgreSQL | Exigiria configuração de role por tenant; complexidade operacional alta em on-premise |
| Decorator/middleware que verifica tenant após a query | Detecta o problema tarde demais — dado já foi buscado; não previne o vazamento |
| Confiança no desenvolvedor (sem enforcement) | Inaceitável para dado sensível; um PR descuidado compromete todos os tenants |

## Referências

- P01 spec: `docs/specs/001-multi-tenancy.md`
- Constituição, INV-01: `docs/constitution.md`
