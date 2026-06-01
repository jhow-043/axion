# CLAUDE.md

@AGENTS.md

---

## Específico do Claude Code neste projeto

### Contexto obrigatório antes de implementar

Ao iniciar qualquer implementação de spec, leia nesta ordem:
1. `docs/constitution.md` — invariantes e DoD global
2. A spec alvo (`docs/specs/<id>-<slug>.md`)
3. Os ADRs citados no frontmatter da spec (`docs/architecture/decisions/`)
4. `docs/architecture/data-model.md` — para entender entidades relacionadas

### Slash commands disponíveis

Use os comandos em `.claude/commands/` para o fluxo SDD:

| Comando | Quando usar |
|---------|-------------|
| `/spec-new` | Criar uma nova spec a partir de um requisito |
| `/spec-plan P##` | Gerar plano técnico antes de implementar |
| `/spec-tasks P##` | Quebrar em tarefas atômicas rastreáveis |
| `/spec-implement P##` | Implementar a spec completa |
| `/spec-review P##` | Revisar o trabalho contra o checklist de PR |

### Subagents especializados

Para tarefas complexas, delegue a subagents em `.claude/agents/`:
- `spec-author` — escrever/refinar specs
- `backend-implementer` — implementação backend (apenas `backend/`)
- `frontend-implementer` — implementação frontend (apenas `frontend/`)
- `test-author` — escrever testes a partir dos Critérios de Aceite
- `spec-reviewer` — revisão read-only do DoD e das invariantes

### MCP

- Use `context7` **sempre** antes de usar API de FastAPI/SQLAlchemy/Pydantic/TanStack/shadcn.
- Use `postgres` (read-only) para validar schema e índices.
- Use `playwright` para conduzir testes E2E das specs.

### Memória persistente

Decisões duráveis → ADR em `docs/architecture/decisions/`.
Requisitos → `docs/product/requirements/`.
Progresso → campo `status:` no frontmatter das specs.

### Hooks ativos

Ver `.claude/settings.json`:
- `PostToolUse` em `Edit|Write`: roda `ruff check --fix` + `ruff format` em arquivos Python.
- `PreToolUse` em `Edit|Write`: bloqueia commit com segredos detectados.
