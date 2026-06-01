# Estratégia de Testes

## Princípio fundamental

**Critério de Aceite = contrato testável.**
Cada checkbox da spec mapeia para ≥1 teste.
Sem teste para o critério → critério não está "done".

---

## Pirâmide de testes

```
         /\
        /E2E\          Playwright — fluxos de usuário completos
       /──────\
      /Integração\     httpx AsyncClient + banco de teste real
     /────────────\
    /   Unitários  \   Regras de negócio puras, sem I/O
   /────────────────\
```

### Proporção esperada
- **70% unitários** — rápidos, determinísticos, sem dependências externas.
- **25% integração** — cobertura de rotas, validação de schema, comportamento do banco.
- **5% E2E** — fluxos críticos de usuário (abertura de chamado, transições, validação).

---

## Testes Unitários

**O que testar:**
- Lógica de negócio pura em `service.py` e `state_machine.py`.
- Cálculos de SLA (prazos, pausas, acumuladores).
- Resolução de permissões (união de papéis).
- Serialização de envelopes de erro.

**Regras:**
- Sem banco, sem HTTP — use mocks mínimos para repositórios.
- Um comportamento por teste.
- Nome descritivo: `test_transition_to_pending_without_reason_raises_error`.

**Exemplo de padrão:**
```python
class TestTicketStateMachine:
    def test_valid_transition_new_to_in_progress(self):
        result = transition(current="new", to="in_progress")
        assert result == "in_progress"

    def test_invalid_transition_closed_to_any_raises(self):
        with pytest.raises(InvalidTransitionError):
            transition(current="closed", to="in_progress")
```

---

## Testes de Integração

**O que testar:**
- Cada endpoint da spec: happy path, casos de erro, validações.
- Comportamento do banco (criação, atualização, índices).
- `require_permission()` bloqueando acesso não autorizado.
- Respostas de erro com envelope padronizado.

**Setup:**
```python
# conftest.py
@pytest.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

@pytest.fixture
async def db_session():
    # PostgreSQL de teste com rollback por fixture
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()
```

**Preferência pelo banco de teste:** PostgreSQL > SQLite in-memory.
SQLite não suporta todas as features do PG16 (ex.: UUID, JSONB, índices parciais).
Use Docker Compose em CI com PostgreSQL de teste.

---

## Testes de Isolamento de Tenant (obrigatórios)

**Obrigatório em todo módulo de domínio.** Teste padrão mínimo:

```python
class TestTenantIsolation:
    async def test_cannot_read_other_tenant_data(
        self, client_tenant_a, client_tenant_b, ticket_tenant_a
    ):
        # Tenant A cria dado
        # Tenant B tenta acessar com o ID do dado de A → 404
        response = await client_tenant_b.get(f"/api/v1/tickets/{ticket_tenant_a.id}")
        assert response.status_code == 404

    async def test_list_returns_only_own_tenant_data(
        self, client_tenant_a, client_tenant_b
    ):
        # Ambos os tenants têm dados
        # Listagem de A retorna apenas dados de A
        response = await client_tenant_a.get("/api/v1/tickets")
        ids = [t["id"] for t in response.json()["items"]]
        assert ticket_tenant_b.id not in ids
```

---

## Testes E2E (Playwright via MCP)

**O que testar:**
- Fluxos descritos em "Testes E2E" de cada spec.
- Golden path: o fluxo principal sem erros.
- Casos de erro visíveis na UI (403, formulário inválido).

**Prioridade por spec:**
- P09: abertura de chamado → técnico assume → supervisor vê no dashboard.
- P03: login válido, login inválido, sessão expirada com refresh.
- P12: chamado com SLA → badge exibido → vencimento atualizado.

**Quando rodar:** antes de PRs para `develop`; após deploy em homologação.

---

## Configuração de CI

```yaml
# .github/workflows/ci.yml (ou equivalente)
jobs:
  backend:
    steps:
      - run: uv sync
      - run: ruff check .
      - run: ruff format --check .
      - run: pytest -q --tb=short
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_DB: test, POSTGRES_USER: test, POSTGRES_PASSWORD: test }

  frontend:
    steps:
      - run: pnpm install
      - run: pnpm lint
      - run: pnpm build
      - run: pnpm test
```

---

## Convenções de nomenclatura

| Arquivo | Conteúdo |
|---------|---------|
| `test_unit.py` | Testes unitários de regras de negócio puras |
| `test_integration.py` | Testes de rotas + banco |
| `test_tenant_isolation.py` | Testes de isolamento obrigatórios |
| `e2e/test_<spec_slug>.py` | Testes E2E por spec |

**Nomes de test functions:** `test_<acao>_<condicao>_<resultado_esperado>`.
Exemplo: `test_create_ticket_without_equipment_returns_422`.

---

## Cobertura mínima obrigatória

**90% de cobertura de código** em todo PR. Verificado com `pytest --cov`:

```bash
pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

Configuração em `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=90"

[tool.coverage.run]
omit = ["*/tests/*", "*/migrations/*", "app/main.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

**Linhas excluídas da cobertura:** arquivos de migração Alembic, `main.py` (bootstrap),
blocos `if TYPE_CHECKING:`, e `raise NotImplementedError` em ABCs.

**Estratégia para atingir 90%:** cobertura vem naturalmente da pirâmide (unit + integração).
Não crie testes vazios ou triviais só para subir o número — o CI rejeita PRs abaixo do limiar.

Frontend: cobertura de testes de componentes/hooks via Vitest com `c8`:
```bash
pnpm test --coverage --coverage.thresholds.lines=90
```

## Definition of Done de testes

Um PR está pronto para merge quando:
- `pytest -q` passa sem erros.
- **Cobertura ≥ 90%** (`--cov-fail-under=90`).
- Cada Critério de Aceite tem ≥1 teste.
- Testes de isolamento de tenant presentes e passando.
- Sem testes com `xfail`, `skip` ou `TODO` não resolvido.
