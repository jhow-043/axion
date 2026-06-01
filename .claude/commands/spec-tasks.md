# /spec-tasks — Quebrar spec em tarefas atômicas

Converte o plano técnico em tarefas rastreáveis mapeadas aos Critérios de Aceite.

## Uso

```
/spec-tasks P##
```

Exemplo: `/spec-tasks P09`

## Pré-requisito

`/spec-plan P##` deve ter sido executado e aprovado nesta sessão ou numa sessão anterior
cujo plano foi documentado.

## O que o agente faz

1. **Lê os Critérios de Aceite** da spec como fonte das tarefas (um critério → ≥1 tarefa).

2. **Cria a lista de tarefas** usando TodoWrite com:
   - Tarefas de implementação (por arquivo/camada: models → repo → service → router → tests)
   - Tarefas de teste (unit → integração → E2E)
   - Tarefas de validação (ruff, pytest, critérios de aceite)
   - Tarefa final: atualizar `status` da spec para `in-review` no frontmatter

3. **Mapeia rastreabilidade:**
   Para cada tarefa, indica qual Critério de Aceite ela satisfaz.

4. **Identifica paralelizáveis:**
   Agrupa tarefas que podem rodar em paralelo (ex.: backend + testes unitários são independentes do frontend).

## Saída esperada

Lista de tarefas no TodoWrite + resumo no chat com o mapeamento tarefa ↔ critério de aceite.

## Regras

- Cada tarefa deve ser pequena o suficiente para completar em um único passo de ferramenta.
- Nenhuma tarefa "implementar o módulo X" — sempre granular (ex.: "criar models.py com entidade Ticket").
- A última tarefa sempre verifica que `pytest -q` passa sem erros.
