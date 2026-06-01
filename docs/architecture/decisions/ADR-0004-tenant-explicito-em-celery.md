---
id: ADR-0004
title: "tenant_id passado explicitamente em tasks Celery"
status: accepted
date: 2026-06-01
supersedes: ~
superseded_by: ~
---

# ADR-0004 — tenant_id passado explicitamente em tasks Celery

## Contexto

O isolamento de tenant usa um `ContextVar` Python configurado pela dependência
`get_current_user()` no início de cada requisição HTTP. O `BaseRepository` lê
este `ContextVar` para filtrar automaticamente por tenant.

O problema: workers Celery executam tasks em processos separados, fora do ciclo de
vida de uma requisição HTTP. O `ContextVar` não é serializado junto com a task —
ele simplesmente não existe no worker.

Se um worker tentar usar o `BaseRepository` sem configurar o `ContextVar`, ou tentará
ler um tenant indefinido (erro), ou pior, usará o valor do `ContextVar` de uma task
anterior que ainda esteja no mesmo processo (vazamento de tenant).

## Decisão

Toda task Celery que opera dados de domínio recebe `tenant_id: str` (UUID como string)
explicitamente no payload da task.

O worker configura o `ContextVar` de tenant a partir do payload **antes** de qualquer
acesso ao banco. Padrão de implementação:

```python
@celery_app.task
def process_sla_alerts(tenant_id: str, tracker_ids: list[str]) -> None:
    with tenant_context(UUID(tenant_id)):  # configura ContextVar
        # BaseRepository funciona normalmente aqui
        ...
```

Jobs que varrem múltiplos tenants (ex.: SLA sweeper global) iteram explicitamente
por tenant, configurando o contexto em cada iteração:

```python
@celery_app.task
def sla_breach_sweep() -> None:
    for tenant_id in get_active_tenant_ids():  # query sem filtro de tenant
        with tenant_context(tenant_id):
            check_breaches_for_tenant(tenant_id)
```

## Consequências

### Positivas
- Sem risco de vazamento de tenant entre tasks no mesmo worker.
- Comportamento explícito e auditável — o `tenant_id` está sempre visível no payload.
- Logs do Celery mostram o tenant de cada task.
- Retry automático preserva o `tenant_id` no payload.

### Negativas / Trade-offs
- Toda task de domínio precisa receber e configurar o `tenant_id` — pequeno overhead de boilerplate.
- Se o chamador esquecer de passar o `tenant_id`, o worker falha explicitamente
  (melhor do que vazar dados silenciosamente).
- O `get_active_tenant_ids()` no sweeper global não usa `BaseRepository`
  (é uma das poucas queries sem filtro de tenant permitidas).

### Impacto em specs
- P01 (Multi-Tenancy): documenta e testa a convenção de passagem explícita.
- P12 (SLA): `sla_breach_sweep` e `sla_alert_sweep` passam `tenant_id` explicitamente.
- P13 (Encerramento): `auto_close_sweep` passa `tenant_id` explicitamente.
- P14 (Notificações): task de envio de e-mail recebe `tenant_id` no payload.

## Alternativas consideradas

| Alternativa | Por que foi rejeitada |
|-------------|----------------------|
| Confiar no ContextVar existente no worker | ContextVar não sobrevive à serialização da task; risco de usar tenant errado |
| Passar sessão de banco serializada | Impossível — sessão SQLAlchemy não é serializável |
| Desabilitar isolamento de tenant em workers | Inaceitável — workers processam dados sensíveis de múltiplos tenants |
| Header HTTP simulado no worker | Artificial e frágil; não reflete o modelo de request/response |

## Referências

- Python ContextVar: contextvars.ContextVar (PEP 567)
- P01 spec: `docs/specs/001-multi-tenancy.md`
- Constituição, INV-04: `docs/constitution.md`
