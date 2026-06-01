---
id: P##
slug: nome-do-modulo
status: draft          # draft | approved | in-progress | in-review | done
version: 0.1.0
owner: jhowworks
depends_on: []         # ex.: [P01, P04]
satisfies: []          # ex.: [RF-080, RF-081, RNF-SEG-001]
adrs: []               # ex.: [ADR-0001, ADR-0003]
branch: feature/0##-nome-do-modulo
last_updated: YYYY-MM-DD
---

# P## — Nome do Módulo

## Objetivo

Uma ou duas frases descrevendo o que este plano entrega e por que é necessário.

## Escopo

Lista detalhada do que será implementado neste plano.

- Item 1
- Item 2

## Fora do Escopo

O que explicitamente **não** faz parte deste plano (evita scope creep e define fronteiras).

- Item fora
- Item fora

## Dependências

- **P##** (Nome) — motivo da dependência.
- *(Nenhuma se for o ponto de partida)*

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `nome_tabela` | Nova tabela / Alterada / Lida |

### `nome_tabela`
```
id          UUID, PK
tenant_id   UUID, FK → tenants, INDEX
campo       Tipo, constraints
created_at  DateTime
updated_at  DateTime
```

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/recurso` | Listar recursos | `permissao:code` |

### Body de `POST /api/v1/recurso`
```json
{
  "campo": "valor"
}
```

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Nome da Tela | Descrição do que a tela faz |

*(Nenhuma — apenas backend, se aplicável)*

## Regras de Negócio

1. **Regra 1:** descrição precisa da regra.
2. **Regra 2:** ...

## Critérios de Aceite

- [ ] Critério testável e verificável 1
- [ ] Critério testável e verificável 2
- [ ] Critério de isolamento de tenant testado

## Estratégia de Testes

### Testes Unitários

- Regra de negócio pura 1: cenário → resultado esperado.

### Testes de Integração

- Endpoint feliz: request → response esperado.
- Endpoint com erro: request inválido → status e mensagem esperados.
- Isolamento de tenant: dado de tenant A não retorna para tenant B.

### Testes E2E

*(Não aplicável / ou: fluxo descrito em linguagem de usuário)*

## Riscos Técnicos

- **Risco:** descrição. **Mitigação:** como resolver.

## Complexidade

**Baixa / Média / Alta** — justificativa em uma linha.

## Prioridade

**Crítica / Alta / Média / Baixa**

## Branch

`feature/0##-nome-do-modulo`
