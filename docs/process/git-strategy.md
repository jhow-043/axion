# Estratégia Git

## Branches

| Branch | Origem | Destino | Uso |
|--------|--------|---------|-----|
| `main` | — | — | Produção. Estável. Sem commits diretos. |
| `develop` | `main` | — | Integração/homologação. Recebe PRs aprovados. |
| `feature/<id>-<slug>` | `develop` | `develop` | Implementação de specs (ex.: `feature/009-chamados-workflow`) |
| `fix/<id>-<descricao>` | `develop` | `develop` | Correções em desenvolvimento |
| `refactor/<id>-<descricao>` | `develop` | `develop` | Refatorações |
| `docs/<id>-<descricao>` | `develop` | `develop` | Documentação |
| `hotfix/<id>-<descricao>` | `main` | `main` + `develop` | Correções críticas em produção |

---

## Commits — Conventional Commits (obrigatório)

```
feat(tickets): adiciona transição para pendente [P09]
fix(sla): corrige cálculo de pausa com fuso horário
refactor(auth): simplifica rotação de refresh token
docs(specs): atualiza critérios de aceite de P12
test(tenant): adiciona teste de isolamento em equipamentos
chore: atualiza dependências Python
```

**Formato:** `<tipo>(<escopo>): <descrição imperativa> [P##]`

- Tipo obrigatório: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
- Escopo opcional mas recomendado: nome do módulo
- Referência à spec opcional mas recomendada quando aplicável

---

## Merge

| Merge | Estratégia | Por quê |
|-------|-----------|---------|
| `feature/fix/refactor/docs → develop` | **Squash merge** | 1 commit por unidade de trabalho; histórico limpo |
| `develop → main` | **Merge commit** | Preserva o conjunto da release |
| `hotfix → main` | Merge commit + back-merge para `develop` | Rastreabilidade |

---

## Pull Requests

- Sempre contra `develop` (hotfix contra `main`).
- Título em Conventional Commits com referência ao P## (ex.: `feat(tickets): P09 — chamados núcleo e workflow`).
- Um PR por spec — sem misturar funcionalidades.
- CI obrigatório verde: lint + testes + build.

### Template de PR

```markdown
## Spec
Implementa: **P##** — [nome da spec](../docs/specs/<arquivo>.md)
Status da spec: `in-review`

## O que foi implementado
- Item 1
- Item 2

## Critérios de Aceite atendidos
- [x] Critério 1
- [x] Critério 2

## ADRs aplicados
- ADR-XXXX: motivo

## Satisfaz
RF-### · RNF-###

## Checklist
- [ ] `pytest -q` verde
- [ ] `ruff check .` e `ruff format --check .` passam
- [ ] Testes de isolamento de tenant presentes
- [ ] Sem segredos no código
- [ ] Migrations incluídas (se houve mudança de schema)
- [ ] Frontmatter da spec atualizado para `status: in-review`
```

---

## Releases — SemVer

| Versão | Quando |
|--------|--------|
| `PATCH` (0.0.x) | Correções (fix/hotfix) |
| `MINOR` (0.x.0) | Conjunto de specs de uma onda entregues |
| `MAJOR` (x.0.0) | Quebra de contrato de API |

Tag: `vMAJOR.MINOR.PATCH` no `main` após merge.
Notas de release geradas a partir dos Conventional Commits do período.

---

## Rollback

**Código:** `git revert <merge-commit>` no `main` + redeploy da tag anterior estável.
Preferir `revert` a `reset` em branches compartilhadas.

**Schema:** rollback da migration Alembic documentado no PR que alterou o schema.
Cada PR com mudança de schema deve incluir: migration `upgrade` + instrução de `downgrade`.

---

## Trabalho por Agentes de IA

- Cada agente recebe **uma spec** como fonte da tarefa e trabalha em `feature/<id>-...`.
- O agente não cruza fronteiras de módulo além do previsto na spec.
- Os **Critérios de Aceite** e a **Estratégia de Testes** da spec são o DoD.
- PRs atômicos por spec facilitam revisão e rollback.
- Respeitar o mapa de dependências: só iniciar P## quando `depends_on` estiver em `develop`.

---

## .gitignore obrigatório

```
# Ambiente
.env
*.env
.env.local
.env.*.local

# Python
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/

# Node
node_modules/
dist/
.next/

# Claude Code (overrides locais)
.claude/settings.local.json

# IDE
.vscode/
.idea/
*.iml
```
