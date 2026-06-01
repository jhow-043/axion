# Constituição do Projeto

> Princípios invioláveis, invariantes arquiteturais e Definição de Pronto global.
> Todo agente de IA lê este documento **antes** de qualquer implementação.
> Violação de qualquer invariante bloqueia o merge.

---

## 1. Invariantes (não negociáveis)

### INV-01 — Isolamento de tenant por BaseRepository
Todo acesso a dados de domínio passa pelo `BaseRepository`.
Queries SQLAlchemy diretas de domínio são proibidas em `service.py` e `router.py`.

**Consequências:**
- `BaseRepository` aplica `WHERE tenant_id = :current_tenant` automaticamente.
- `INSERT` via `BaseRepository` seta `tenant_id` do contexto sem passagem explícita.
- Bypass do `BaseRepository` é considerado bug crítico de segurança.

**ADR:** [ADR-0001](architecture/decisions/ADR-0001-isolamento-multitenant-baserepository.md)

---

### INV-02 — Cross-tenant retorna 404, nunca 403
Tentativa de acessar registro de outro tenant resulta em `404 Not Found`.
Nunca `403 Forbidden` — para não revelar a existência do recurso.

**Consequências:**
- `BaseRepository.get(id)` com ID de outro tenant retorna `None`.
- O router trata `None` como 404 (via `raise_or_404` ou equivalente).
- Testes devem verificar 404, nunca esperar 403 neste cenário.

**ADR:** [ADR-0002](architecture/decisions/ADR-0002-cross-tenant-404-nao-403.md)

---

### INV-03 — State machine como invariante de código
As transições válidas/inválidas do chamado são definidas **em código** (`service.py`).
O catálogo configurável (P07) ajusta apenas rótulo, ordem e flags de exibição — nunca a lógica de fluxo.

**Consequências:**
- `status.code` é a âncora da máquina de estados (não o ID UUID, não o rótulo).
- Editar o catálogo não pode quebrar nenhuma transição.
- Se um `status.code` for removido do catálogo, o sistema deve rejeitar a operação.

**ADR:** [ADR-0003](architecture/decisions/ADR-0003-status-code-ancora-state-machine.md)

---

### INV-04 — Tenant explícito em jobs Celery
`ContextVar` de tenant não existe no worker Celery.
O `tenant_id` deve ser passado **explicitamente** no payload da task.

**Consequências:**
- Todo job Celery que opera dados de domínio recebe `tenant_id: UUID` no payload.
- O worker configura o `ContextVar` a partir do payload antes de executar a lógica.
- Jobs que varrem múltiplos tenants (ex.: SLA sweeper) iternam explicitamente por tenant.

**ADR:** [ADR-0004](architecture/decisions/ADR-0004-tenant-explicito-em-celery.md)

---

### INV-05 — Sem segredos em código ou valores padrão fixos
Toda variável sensível (credenciais de banco, chaves JWT, SMTP, MinIO) vem de variável de ambiente.
Valores padrão fixos para credenciais são proibidos.

**Consequências:**
- `pydantic-settings` usado para carregar config; campos obrigatórios sem default.
- `git diff` ou grep por padrões de segredo bloqueia o commit (hook configurado).
- `.env.example` documenta as variáveis sem valores reais.

---

## 2. Princípios de código

Aplicam-se a todo código gerado por humanos ou IA:

- **Responsabilidade única:** funções e componentes fazem uma coisa. Sem services-deus.
- **Nomes claros:** o nome deve dispensar comentário. `calculate_resolution_due_at()` não precisa de docstring.
- **Comentários só para o "porquê":** decisão arquitetural, workaround de bug, invariante não-óbvia. Nunca para o que o código faz.
- **Sem over-engineering:** implemente o que a spec pede. Sem abstrações para casos hipotéticos.
- **Sem backwards-compat desnecessário:** se algo não é usado, delete. Sem `# TODO: remover depois`.
- **Sem lógica de negócio no router:** `router.py` apenas valida entrada, chama o service, retorna o schema.
- **Sem acesso ao banco no service:** `service.py` recebe o repositório; não importa `AsyncSession`.

---

## 3. Padrão de módulo backend

```
modules/<nome>/
├── models.py       # ORM: TenantMixin obrigatório, índices em tenant_id
├── schemas.py      # Pydantic v2: request e response separados
├── repository.py   # herda BaseRepository — tenant automático
├── service.py      # regras de negócio, recebe repositório por DI
├── router.py       # HTTP: require_permission(), chama service, retorna schema
└── tests/
    ├── test_unit.py              # regras puras sem banco
    ├── test_integration.py       # rotas + banco de teste
    └── test_tenant_isolation.py  # isolamento obrigatório
```

---

## 4. Definição de Pronto (global)

Um P## está pronto quando **todos** os itens abaixo são verdadeiros:

- [ ] Todos os **Critérios de Aceite** da spec marcados (checkboxes)
- [ ] **Testes unitários** presentes e passando para toda regra de negócio da spec
- [ ] **Testes de integração** presentes e passando para todos os endpoints da spec
- [ ] **Testes de isolamento de tenant** presentes e passando
- [ ] `ruff check .` e `ruff format --check .` passam sem erros
- [ ] `pytest -q` passa sem erros com **cobertura ≥ 90%** (`--cov-fail-under=90`)
- [ ] Nenhum segredo ou credencial no código
- [ ] Frontmatter da spec atualizado para `status: in-review`
- [ ] PR aberto com título em Conventional Commits referenciando o P##
- [ ] CI verde no PR

---

## 5. Quando criar um ADR

Crie um ADR em `docs/architecture/decisions/` sempre que:
- Uma decisão arquitetural não-óbvia for tomada
- Uma decisão mudar ou for re-debatida
- Um tradeoff significativo for aceito

Use o template `docs/architecture/decisions/_template.md`.
Cite o ADR no frontmatter da spec (`adrs: [ADR-XXXX]`) e nas regras de negócio relevantes.

---

## 6. Escopo de agente

Cada agente implementa **uma spec por vez**.
Não cruza fronteiras de módulo além do previsto na spec.
Não inicia um P## antes de suas `depends_on` terem `status: done`.
