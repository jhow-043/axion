# /spec-plan — Gerar plano técnico de uma spec

Lê a spec e produz um plano técnico detalhado antes de qualquer implementação.

## Uso

```
/spec-plan P##
```

Exemplo: `/spec-plan P09`

## O que o agente faz

1. **Carrega o contexto completo:**
   - `docs/constitution.md`
   - A spec alvo (`docs/specs/<id>-<slug>.md`)
   - ADRs citados no frontmatter
   - `docs/architecture/data-model.md`
   - `docs/architecture/folder-structure.md`
   - Specs das dependências (campo `depends_on`) — apenas cabeçalho + APIs

2. **Produz o plano técnico:**

   ### Arquivos a criar
   Lista completa de arquivos novos com o propósito de cada um.

   ### Arquivos a modificar
   Arquivos existentes que precisam ser alterados (ex.: `main.py` para montar o novo router).

   ### Ordem de implementação
   Sequência segura considerando dependências internas ao módulo:
   1. Models → Migrations → Repository → Service → Router → Schemas → Tests

   ### Interfaces a coordenar
   Contratos com outros módulos que devem ser acordados antes de codificar
   (ex.: interface de `notification_service.notify()`, `timeline_service.record_event()`).

   ### ADRs necessários
   Se a implementação exigir uma nova decisão arquitetural não coberta pelos ADRs existentes,
   indicar que um ADR deve ser criado antes de prosseguir.

   ### Riscos identificados
   Riscos técnicos da spec + riscos de integração com dependências.

3. **Aguarda aprovação humana** antes de prosseguir para `/spec-tasks`.

## Saída esperada

Plano em texto estruturado no chat — não cria arquivos (o plano vive na conversa).
Se um ADR novo for necessário, cria o rascunho em `docs/architecture/decisions/`.

## Contexto necessário

Leia antes:
- `docs/constitution.md`
- `docs/architecture/data-model.md`
- `docs/architecture/folder-structure.md`
