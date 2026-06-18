---
id: P24
slug: hub-consolidacao-manutencao
status: done
version: 0.1.0
owner: jhowworks
depends_on: [P20, P23]
satisfies: [RF-203, RF-209]
adrs: [ADR-0001, ADR-0002, ADR-0006]
branch: feature/024-hub-consolidacao-manutencao
last_updated: 2026-06-15
---

# P24 — Consolidação do Módulo `manutencao`

## Objetivo

Aplicar a dependency `require_module("manutencao")` em todos os routers do domínio de
manutenção no backend, garantindo que o gating seja enforçado também na camada de API
(não apenas no frontend). Sem alterar nenhuma regra de negócio.

## Escopo

- Adicionar `require_module("manutencao")` como dependency nos routers dos domínios:
  `tickets`, `sla`, `closures`, `equipments`, `locations`, `catalog`, `timeline`,
  `dashboards`, `reports`.
- Módulos que são infraestrutura do HUB e **não** recebem `require_module`: `auth`,
  `users`, `teams`, `notifications`, `attachments`, `audit`, `administration`.
- Verificar e corrigir o módulo `reports` (identificado no diagnóstico como tendo router
  sem service/models/tests completos).
- Atualizar testes de integração existentes para garantir que um tenant sem o módulo
  receba 404 em todas as rotas de manutenção.

## Fora do Escopo

- Qualquer alteração de lógica de negócio (state machine, SLA, validações).
- Criação de novos módulos além de `manutencao`.
- Refatoração de organização de pastas dos módulos.

## Dependências

- **P20** (Núcleo de Módulos) — `require_module` disponível em `app/core/deps.py`.
- **P23** (Menu e Rotas Modulares) — frontend já bloqueia por módulo; esta spec fecha o
  gating no backend.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `tickets/router.py` | Alterada — `require_module` adicionada |
| `sla/router.py` | Alterada — `require_module` adicionada |
| `closures/router.py` | Alterada — `require_module` adicionada |
| `equipments/router.py` | Alterada — `require_module` adicionada |
| `locations/router.py` | Alterada — `require_module` adicionada |
| `catalog/router.py` | Alterada — `require_module` adicionada |
| `timeline/router.py` | Alterada — `require_module` adicionada |
| `dashboards/router.py` | Alterada — `require_module` adicionada |
| `reports/router.py` | Alterada — `require_module` adicionada + sanar déficit técnico |
| Testes de integração dos módulos acima | Atualizados — cenário "sem módulo → 404" |

## APIs Necessárias

Nenhuma nova. Mudança de comportamento nas rotas existentes:
- Tenant sem `manutencao` liberado em qualquer rota do domínio → `404 Not Found`.
- Tenant com `manutencao` liberado → comportamento idêntico ao atual.

## Telas Necessárias

Nenhuma.

## Regras de Negócio

1. **Gating no backend:** `require_module("manutencao")` aplicada como dependency no router,
   não no service (garante que o check seja feito antes de qualquer acesso a dado).
2. **Retorno 404:** coerente com ADR-0002 — não revela a existência do endpoint para tenants
   sem o módulo.
3. **Módulos HUB são isentos:** `auth`, `users`, `teams`, `notifications`, `attachments`,
   `audit`, `administration` nunca recebem `require_module` — são núcleo da plataforma.
4. **`reports` — saneamento:** verificar e implementar qualquer camada faltante (service,
   models, testes) identificada no inventário de módulos. Não expandir escopo além do necessário.
5. **Compatibilidade:** tenants com `manutencao` liberado (todos os existentes após P20) não
   percebem nenhuma diferença.

## Como aplicar `require_module` num router

Padrão a seguir (exemplo em `tickets/router.py`):

```python
from app.core.deps import require_module

MODULE = "manutencao"

@router.get("/tickets")
async def list_tickets(
    _: User = Depends(require_module(MODULE)),
    current_user: User = Depends(get_current_user),
    ...
):
    ...
```

Alternativamente, incluir como dependency no nível do router:

```python
router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    dependencies=[Depends(require_module("manutencao"))],
)
```

A segunda forma é preferida por eliminar repetição em cada endpoint.

## Critérios de Aceite

- [ ] Tenant com `manutencao` liberado: todos os endpoints do domínio continuam funcionando normalmente.
- [ ] Tenant sem `manutencao`: `GET /api/v1/tickets` retorna 404.
- [ ] Tenant sem `manutencao`: `POST /api/v1/tickets` retorna 404.
- [ ] Tenant sem `manutencao`: `GET /api/v1/equipments` retorna 404.
- [ ] Tenant sem `manutencao`: `GET /api/v1/sla` retorna 404.
- [ ] Tenant sem `manutencao`: `GET /api/v1/dashboards/management` retorna 404.
- [ ] Tenant sem `manutencao`: `GET /api/v1/reports` retorna 404.
- [ ] Endpoints HUB (`/users`, `/auth/*`, `/notifications`, etc.) funcionam normalmente para qualquer tenant autenticado independente de módulo.
- [ ] `reports` tem testes de integração funcionando (saneamento do déficit técnico).
- [ ] Cobertura de testes ≥ 90% em todos os routers alterados.

## Estratégia de Testes

### Testes Unitários

- Nenhum novo — a dependency já foi testada em P20.

### Testes de Integração

Para cada router do domínio de manutenção, adicionar fixture de "tenant sem módulo" e verificar:
- `GET /recurso` com tenant sem módulo → 404.
- `POST /recurso` com tenant sem módulo → 404.
- `GET /recurso` com tenant com módulo → 200 (comportamento atual inalterado).

### Testes E2E

- Chamada direta à API com token de tenant sem módulo → 404 em endpoint de ticket.

## Riscos Técnicos

- **Risco:** algum endpoint de manutenção não receber a dependency e continuar acessível.
  **Mitigação:** aplicar a dependency no nível do `APIRouter` (não por endpoint), cobrindo
  todos os endpoints do router automaticamente.
- **Risco:** saneamento de `reports` descobrir débito técnico maior que o esperado.
  **Mitigação:** se o escopo do reports for maior, abrir spec separada e marcar como
  dependência desta. Não misturar correção de reports com gating de módulo num PR só.

## Complexidade

**Baixa** — adicionar dependency em 9 routers + testes de cenário "sem módulo". Nenhuma
lógica de negócio é tocada. Risco principal é esquecer algum router — coberto pelos testes.

## Prioridade

**Alta** — sem esta spec, o gating é apenas no frontend (segurança cosmética). A defesa real
é no backend.

## Branch

`feature/024-hub-consolidacao-manutencao`
