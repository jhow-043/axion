---
id: ADR-0003
title: "status.code como âncora invariante da máquina de estados"
status: accepted
date: 2026-06-01
supersedes: ~
superseded_by: ~
---

# ADR-0003 — status.code como âncora invariante da máquina de estados

## Contexto

O status do chamado é uma entidade configurável (P07) — o admin pode renomear os rótulos,
mudar a ordem de exibição e ajustar flags visuais. Isso permite que cada empresa adapte
a terminologia ao seu vocabulário.

Ao mesmo tempo, a máquina de estados (P09) define transições com lógica de negócio
rígida: `new → in_progress`, `in_progress → pending`, `resolved → closed`, etc.

O risco é: se a âncora da máquina for o UUID ou o rótulo do status, uma edição do
catálogo pode silenciosamente quebrar o fluxo de chamados.

## Decisão

A máquina de estados usa `status.code` (string) como âncora, não o UUID nem o rótulo.

Os códigos válidos são constantes em código: `"new"`, `"in_progress"`, `"pending"`,
`"resolved"`, `"closed"`. O catálogo configurável pode alterar `name` (rótulo exibido),
`order` e flags visuais — mas nunca o `code`.

Tentativa de editar o `code` de um status padrão é bloqueada pela API.
Tentativa de remover um status com `code` reconhecido pela state machine é bloqueada.

## Consequências

### Positivas
- O admin pode personalizar rótulos ("Em Andamento" em vez de "Em Atendimento") sem risco.
- A lógica de fluxo é auditável no código-fonte — não depende de dados do banco.
- Testes de máquina de estados são determinísticos e independentes do banco.
- Onboarding de novos tenants com seed de catálogo é simples.

### Negativas / Trade-offs
- Os códigos são constantes em código — adicionar um novo código requer deploy.
- O catálogo não pode ter status completamente customizados com comportamento diferente
  (ex.: "Em Espera de Peça" com pausa de SLA diferente de "Pendente") — isso exigiria
  mudança de código, não de configuração. Registrado como evolução futura.
- Requer validação na API de edição de catálogo para proteger os códigos reservados.

### Impacto em specs
- P07 (Catálogos): seed deve criar os 5 status com os códigos corretos; edição bloqueia alteração de `code`.
- P09 (Chamados): `state_machine.py` usa códigos constantes.
- P12 (SLA): hooks de transição identificados por `status.code`.
- P13 (Encerramento): auto-fechamento verifica `status.code == "resolved"`.

## Alternativas consideradas

| Alternativa | Por que foi rejeitada |
|-------------|----------------------|
| UUID do status como âncora | Se o status for recriado (mesmo código, novo UUID), a state machine quebra |
| Rótulo como âncora | Edição de rótulo (muito comum) quebraria silenciosamente o fluxo |
| Status como enum em banco (sem catálogo configurável) | Impede personalização de rótulos; inflexível para empresas com terminologia diferente |

## Referências

- P07 spec: `docs/specs/007-catalogos-configuraveis.md`
- P09 spec: `docs/specs/009-chamados-workflow.md`
- Constituição, INV-03: `docs/constitution.md`
