# /spec-new — Criar nova spec

Cria um novo arquivo de spec em `docs/specs/` a partir de um requisito ou ideia.

## Uso

```
/spec-new <nome-descritivo>
```

Exemplo: `/spec-new manutencao-preventiva`

## O que o agente faz

1. **Determina o próximo ID** — lê `docs/README.md` e encontra o maior ID P## existente; usa o próximo número.

2. **Entrevista o usuário** (se a descrição for insuficiente):
   - Qual o objetivo desta funcionalidade?
   - Quais entidades de banco são afetadas?
   - Quais specs existentes são dependências?
   - Quais requisitos do catálogo (`docs/product/requirements/functional.md`) esta spec realiza?

3. **Cria o arquivo** `docs/specs/<id>-<slug>.md` usando o template em `docs/specs/_template.md`.
   - Preenche o frontmatter com `status: draft`, `version: 0.1.0`, `owner` e data atual.
   - Mapeia dependências a partir do mapa em `docs/README.md`.
   - Preenche o campo `satisfies` com os RF/RNF relevantes.

4. **Registra no índice** — adiciona a entrada na tabela "Catálogo de Specs" em `docs/README.md`.

5. **Valida contra a Constituição** — verifica se há invariantes que a spec deve citar explicitamente.

## Saída esperada

- Arquivo `docs/specs/<id>-<slug>.md` com status `draft`
- Entrada adicionada ao catálogo em `docs/README.md`
- Mensagem com próximos passos: revisar → aprovar → `/spec-plan`

## Contexto necessário

Antes de executar, leia:
- `docs/constitution.md`
- `docs/product/glossary.md`
- `docs/product/requirements/functional.md`
- `docs/specs/_template.md`
- `docs/README.md` (para o próximo ID e dependências)
