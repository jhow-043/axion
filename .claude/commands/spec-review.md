# /spec-review — Revisar implementação de uma spec

Realiza revisão automatizada do trabalho contra o DoD, a Constituição e o checklist de PR.

## Uso

```
/spec-review P##
```

Exemplo: `/spec-review P09`

## O que o agente faz (modo read-only — não altera código)

### 1. Critérios de Aceite
Para cada checkbox da spec, verifica:
- [ ] Existe teste cobrindo este critério?
- [ ] O teste passa?
- [ ] A implementação realiza o critério conforme descrito?

### 2. Constituição (`docs/constitution.md`)
- [ ] Todo acesso a dados de domínio usa `BaseRepository`?
- [ ] Nenhum endpoint retorna 403 para cross-tenant (deve ser 404)?
- [ ] A state machine do chamado é invariante de código (se aplicável)?
- [ ] Jobs Celery passam `tenant_id` explicitamente?
- [ ] Nenhum segredo ou credencial no código?

### 3. Isolamento de tenant
- [ ] Existe teste específico de isolamento (dois tenants, sem vazamento)?
- [ ] Todo modelo com dados de domínio herda `TenantMixin`?
- [ ] `BaseRepository` usado em todo acesso de leitura/escrita de domínio?

### 4. Estrutura de módulo
- [ ] `router.py` sem lógica de negócio?
- [ ] `service.py` sem acesso direto ao banco?
- [ ] `repository.py` herda `BaseRepository`?
- [ ] Testes organizados em `modules/<nome>/tests/`?

### 5. Qualidade de código
- [ ] `ruff check .` passa?
- [ ] `ruff format --check .` passa?
- [ ] `pytest -q` passa sem erros?
- [ ] Funções pequenas, responsabilidade única?
- [ ] Nenhum comentário óbvio (só o "porquê")?

### 6. PR
- [ ] Título em Conventional Commits com referência ao P##?
- [ ] Descrição cita critérios de aceite atendidos?
- [ ] Um PR por spec (sem misturar funcionalidades)?
- [ ] CI verde?

## Saída esperada

Relatório em texto no chat com:
- Lista de itens ✅ aprovados
- Lista de itens ❌ com problema + localização no código
- Recomendação: "Aprovado para merge" ou "Requer correções"

O agente não abre PRs, não faz commits, não edita código.
Para correções, use `/spec-implement P##` apontando os problemas encontrados.

## Contexto necessário

- `docs/constitution.md` (obrigatório)
- A spec alvo
- Diff do PR (via GitHub MCP ou `git diff develop`)
