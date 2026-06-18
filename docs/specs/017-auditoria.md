---
id: P17
slug: auditoria
status: done
version: 1.0.0
owner: jhowworks
depends_on: [P00, P01, P04]
satisfies: [RF-170, RF-171, RNF-OBS-001, RNF-OBS-002]
adrs: [ADR-0001, ADR-0002]
branch: feature/017-auditoria
last_updated: 2026-06-01
---

# P17 — Auditoria & Rastreabilidade

## Objetivo

Registrar uma trilha de auditoria para ações sensíveis do sistema (configurações, usuários, permissões, SLA), complementando a timeline operacional do chamado (P10) com um registro administrativo imutável e consultável.

## Escopo

- Entidade `audit_logs`: registro de quem fez o quê, quando, em qual entidade e com quais dados (antes/depois).
- Cobertura de ações auditadas: criação/edição/exclusão de usuários, papéis, equipes, equipamentos, políticas de SLA, configurações do tenant, catálogos (prioridades, status, categorias, motivos).
- Mixin `AuditableMixin` ou decorator para facilitar o registro nos módulos.
- API de consulta com filtros.
- Tela de consulta de auditoria (integrada em P18).

## Fora do Escopo

- Timeline operacional do chamado (P10 — cobre eventos funcionais de chamados).
- Auditoria de login/logout (registrar como evolução — logs de acesso).
- Auditoria de leitura (somente escritas/configurações são auditadas).
- Exportação de logs (futuro).

## Dependências

- **P00** (Fundação Backend) — convenções de modelo e serviço.
- **P01** (Multi-Tenancy) — `tenant_id` nos logs.
- **P04** (Usuários e Permissões) — `require_permission("admin:config")` para consulta; ator nos logs.

*Nota: P17 pode ser desenvolvido em paralelo a P05–P08 e integrado gradualmente — cada módulo que for implementado adiciona a chamada ao `audit_service.log()` em suas ações sensíveis.*

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `audit_logs` | Nova tabela |

### `audit_logs`
```
id              UUID, PK
tenant_id       UUID, FK → tenants, INDEX
actor_id        UUID, FK → users, nullable    # null para ações de sistema
action          String, NOT NULL              # ex.: "user.created", "sla_policy.updated"
entity_type     String, NOT NULL              # ex.: "User", "SlaPolicy"
entity_id       UUID, NOT NULL               # ID do recurso afetado
before          JSONB, nullable               # estado antes da alteração
after           JSONB, nullable               # estado após a alteração
ip_address      String, nullable
created_at      DateTime, NOT NULL, INDEX
INDEX(tenant_id, entity_type)
INDEX(tenant_id, actor_id)
INDEX(tenant_id, created_at)
```

### Convenção de `action`
```
<entidade>.<operação>
Exemplos:
  user.created
  user.updated
  user.deactivated
  role.permission_added
  team.member_added
  team.member_removed
  equipment.created
  equipment.deactivated
  sla_policy.created
  sla_policy.updated
  catalog.priority_updated
  tenant_settings.updated
```

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/audit` | Consultar logs de auditoria (paginado) | `admin:config` |

### Parâmetros de filtro (query string)
- `actor_id` — filtrar por usuário que realizou a ação.
- `entity_type` — filtrar por tipo de entidade (ex.: "User", "SlaPolicy").
- `entity_id` — filtrar por ID específico de um recurso.
- `action` — filtrar por tipo de ação.
- `date_from`, `date_to` — período.
- `page`, `page_size`.

### Resposta de `GET /api/v1/audit`
```json
{
  "total": 240,
  "page": 1,
  "page_size": 50,
  "items": [
    {
      "id": "uuid",
      "actor": { "id": "uuid", "name": "Admin Principal" },
      "action": "sla_policy.updated",
      "entity_type": "SlaPolicy",
      "entity_id": "uuid",
      "before": { "resolution_minutes": 480 },
      "after": { "resolution_minutes": 360 },
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Consulta de Auditoria | Tabela paginada com filtros (ator, entidade, período); detalhe do antes/depois inline |

*Integrada no Console de Administração (P18).*

## Regras de Negócio

1. **Imutabilidade:** logs de auditoria são append-only. Nenhum endpoint de edição ou exclusão.
2. **Cobertura:** toda ação de escrita em entidades sensíveis (listadas no escopo) deve gerar um log. Responsabilidade de cada módulo ao usar o `audit_service.log()`.
3. **Antes/Depois:** para `updated`, capturar o estado antes e depois da alteração. Para `created`, somente `after`. Para `deleted`/`deactivated`, somente `before`.
4. **Ator nulo:** ações de sistema (jobs, seed) têm `actor_id = null`; exibir "Sistema" na UI.
5. **Acesso:** apenas Admin pode consultar o log de auditoria.
6. **Retenção:** logs retidos por 12 meses por padrão (configurável como evolução — sem implementação de limpeza no MVP).

## Interface `audit_service.log()`

```
log(
    action: str,                        # ex.: "sla_policy.updated"
    entity_type: str,                   # ex.: "SlaPolicy"
    entity_id: UUID,
    actor_id: UUID | None,
    before: dict | None = None,
    after: dict | None = None
) -> AuditLog
```

Chamado de forma síncrona dentro da mesma transação do módulo de origem (mesmo padrão de P10).

## Critérios de Aceite

- [ ] `audit_service.log()` persiste o registro com todos os campos corretos.
- [ ] Editar política de SLA → log com `before` e `after` corretos.
- [ ] Criar usuário → log com `after` e `before = null`.
- [ ] Desativar usuário → log com `before` e `after` corretos.
- [ ] `GET /audit` retorna apenas logs do tenant do admin autenticado.
- [ ] Filtros funcionam: por `actor_id`, `entity_type`, `date_from/to`.
- [ ] Nenhum endpoint de edição ou exclusão de logs exposto.
- [ ] Usuário sem papel Admin → 403.

## Estratégia de Testes

### Testes Unitários

- `audit_service.log()`: serialização correta dos campos `before`/`after`.
- Ator nulo em chamadas de sistema.

### Testes de Integração

- Editar política de SLA → log criado com dados corretos.
- Criar usuário → log com `action = "user.created"`.
- `GET /audit` com filtro de `entity_type = "User"` → apenas logs de usuários.
- `GET /audit` com não-admin → 403.
- Logs são imutáveis: nenhum endpoint de DELETE/PATCH existente.

### Testes E2E

- Admin altera política de SLA → consulta auditoria → vê o log com antes/depois.
- Admin desativa um usuário → log aparece na auditoria com o campo `is_active: false` em `after`.

## Riscos Técnicos

- **Volume de logs:** ações de configuração são relativamente raras — o volume de `audit_logs` tende a ser menor que o de `ticket_events`. Índices compostos adequados são suficientes.
- **Captura de `before`:** exige leitura do estado atual antes da atualização (uma query adicional). Em atualizações concorrentes, o `before` deve ser capturado dentro da mesma transação com `SELECT FOR UPDATE` para ser preciso.
- **Sensibilidade dos dados:** `before`/`after` podem conter dados sensíveis (ex.: configurações). Não logar campos de senha ou dados de PII — definir lista de campos excluídos por entidade.

## Complexidade

**Média**

## Prioridade

**Média**

## Branch

`feature/017-auditoria`
