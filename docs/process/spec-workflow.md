# Fluxo de Desenvolvimento Baseado em Specs (SDD)

## Visão geral

```
REQUISITO → SPEC → PLANO → TAREFAS → IMPLEMENTAÇÃO → REVISÃO → PROMOÇÃO
```

Cada etapa tem um responsável, um artefato e um critério de saída.
Specs são a unidade de trabalho — não existe código sem spec.

---

## Etapa 1 — Captura do Requisito

**Quando:** Nova funcionalidade, bug com impacto de produto ou melhoria identificada.

**Artefato:** Entrada em `docs/product/requirements/functional.md` (RF-###) ou
`docs/product/requirements/non-functional.md` (RNF-###).

**Critério de saída:** RF ou RNF criado com ID único e linkado à área de produto.

---

## Etapa 2 — Especificação

**Quando:** RF aprovado para desenvolvimento.

**Como:**
1. Execute `/spec-new <nome>` (ou use o subagent `spec-author`).
2. Preencha **todos** os campos do template:
   - Frontmatter com `status: draft`, dependências e RF satisfeitos.
   - Escopo + Fora do Escopo (explícito).
   - Entidades, APIs, Telas, Regras de Negócio.
   - **Critérios de Aceite como checkboxes** (testáveis e verificáveis).
   - Estratégia de Testes (unit / integração / E2E).
   - Riscos técnicos com mitigação.
3. Revise contra a `docs/constitution.md` — alguma regra viola um invariante?
4. Revise contra `docs/product/glossary.md` — termos corretos?
5. Revise o frontmatter `depends_on` contra o mapa de dependências.

**Artefato:** `docs/specs/<id>-<slug>.md` com `status: draft`

**Critério de saída:** Revisão humana → alterar para `status: approved`.

> Specs com `status: draft` **não podem ser implementadas**.

---

## Etapa 3 — Plano Técnico

**Quando:** Spec com `status: approved` + todas as `depends_on` com `status: done`.

**Como:** Execute `/spec-plan P##`.

O plano produz:
- Lista de arquivos a criar/modificar.
- Ordem de implementação dentro do módulo.
- Interfaces a coordenar com módulos adjacentes.
- ADRs necessários (se decisão nova → criar ADR antes de codificar).

**Artefato:** Plano no chat + ADR (se necessário).

**Critério de saída:** Aprovação humana do plano.

---

## Etapa 4 — Tarefas

**Quando:** Plano aprovado.

**Como:** Execute `/spec-tasks P##`.

Produz lista TodoWrite com tarefas atômicas mapeadas aos Critérios de Aceite.

**Artefato:** Lista de tarefas no TodoWrite.

**Critério de saída:** Lista criada e aprovada.

---

## Etapa 5 — Implementação

**Quando:** Tarefas criadas, branch disponível, dependências em `develop`.

**Como:** Execute `/spec-implement P##` (ou `backend-implementer` + `frontend-implementer`).

**Regras:**
- Um agente por spec — sem misturar módulos.
- Fronteira de módulo respeitada conforme a spec.
- Commits granulares em Conventional Commits.
- Hooks de lint automático após cada edição.

**Artefato:** Branch `feature/<id>-<slug>` com código + testes.

**Critério de saída:** `pytest -q` verde + ruff limpo + todos os Critérios de Aceite cobertos.
Atualizar `status: in-review` no frontmatter.

---

## Etapa 6 — Revisão

**Como:** Execute `/spec-review P##` (subagent `spec-reviewer`) + revisão humana no PR.

**O que verificar:**
- Todos os Critérios de Aceite cobertos por testes.
- Constituição respeitada (invariantes).
- Estrutura de módulo correta.
- CI verde.

**Critério de saída:** PR aprovado por revisão humana.

---

## Etapa 7 — Promoção

**Fluxo:** `feature/<id>` → `develop` (squash merge) → `main` (merge commit na release).

**Após merge:**
- Atualizar `status: done` no frontmatter da spec.
- Atualizar `docs/traceability.md` com o PR linkado.
- Se a onda estiver completa, gerar tag SemVer e notas de release.

---

## Regras de paralelismo

Ver mapa de dependências em `docs/README.md`.

- **Onda 0 (P00–P04):** sequencial (caminho crítico).
- **Onda 1 (P05–P08):** paralelo após P04.
- **P02 (frontend):** paralelo com P03/P04 (API-first com MSW).
- **Após P09:** P10 e P11 paralelos; P14 paralelo a P12/P13.
- **P17:** pode iniciar cedo (transversal).

---

## Quando criar um ADR

Toda decisão arquitetural que:
- Não é óbvia para um desenvolvedor experiente.
- Tem alternativas plausíveis que foram descartadas.
- Afeta múltiplos módulos ou specs.

Use `docs/architecture/decisions/_template.md`. Cite o ADR no frontmatter da spec.

---

## Gestão de mudanças em specs aprovadas

Se precisar alterar uma spec com `status: approved` ou `in-progress`:
1. Abra discussão explícita — spec aprovada é contrato.
2. Incremente a versão (`version: 1.0.0 → 1.1.0`).
3. Documente o que mudou e por quê no histórico da spec (seção `## Histórico de Versões`).
4. Se a mudança for arquitetural, crie ou atualize o ADR correspondente.
