---
id: P01
slug: multi-tenancy
status: approved
version: 1.0.0
owner: jhowworks
depends_on: [P00]
satisfies: [RF-010, RF-011, RF-012, RF-013, RNF-SEG-001, RNF-SEG-009]
adrs: [ADR-0001, ADR-0002, ADR-0004]
branch: feature/001-multi-tenancy
last_updated: 2026-06-01
---

# P01 — Multi-Tenancy & Contexto de Tenant

## Objetivo

Garantir isolamento completo de dados entre empresas (tenants) com o mínimo de cerimônia por módulo. Todo acesso a dados de domínio deve ser automaticamente restrito ao tenant do usuário autenticado, sem que cada módulo precise implementar essa lógica individualmente.

## Escopo

- Entidade `Tenant` (nome, slug único, status ativo/inativo, timestamps de auditoria).
- Resolução do tenant a partir do JWT (campo `tenant_id` no payload) e armazenamento em Python `ContextVar` para a duração da requisição.
- `TenantMixin`: coluna `tenant_id` (FK → `tenants`) com índice, adicionada via herança a todas as entidades de domínio.
- `BaseRepository`: repositório base que aplica `WHERE tenant_id = :current_tenant_id` automaticamente em todas as queries de leitura e seta `tenant_id` em todas as escritas.
- Dependência FastAPI `get_current_tenant()`: extrai o tenant do contexto e injeta em endpoints e serviços.
- Utilidades de teste: fixture `with_tenant(tenant_id)` que configura o contexto corretamente para testes de isolamento.
- Documentação da convenção: como passar o `tenant_id` para tasks Celery (passagem explícita no payload do job — não via ContextVar).

## Fora do Escopo

- UI de gestão de empresas (P18 — Administração).
- Billing, planos ou limitações por tenant.
- Provisionamento de tenant (seed inicial — parte do deploy/onboarding).
- Super-admin global (usuário que gerencia múltiplos tenants) — futuro.

## Dependências

- **P00** (Fundação do Backend) — engine, sessão, base declarativa e BaseRepository inicial.
- **P03** (Autenticação) — fonte do `tenant_id` no token JWT. *Nota de coordenação:* P01 define a interface; P03 implementa a emissão do campo no token. Ambos devem alinhar o contrato do payload JWT antes de implementar.

## Entidades Impactadas

| Entidade | Ação |
|----------|------|
| `tenants` | Nova tabela principal |
| Todas as entidades de domínio futuras | Herdam `TenantMixin` (coluna `tenant_id`) |

Estrutura mínima de `Tenant`:
```
id            UUID, PK
name          String, NOT NULL
slug          String, UNIQUE, NOT NULL        # ex.: "empresa-alfa"
is_active     Boolean, DEFAULT true
created_at    DateTime
updated_at    DateTime
```

## APIs Necessárias

Nenhuma rota pública neste plano. A lógica é inteiramente interna (middleware + contexto + BaseRepository).

Rotas de gestão de tenants (criar, listar, ativar/desativar) são responsabilidade de **P18 — Administração**.

## Telas Necessárias

Nenhuma.

## Regras de Negócio

1. **Isolamento por padrão:** toda query que herda de `BaseRepository` filtra por `tenant_id` do contexto ativo. Não existe "query sem tenant" em código de domínio — apenas em scripts de manutenção com autenticação administrativa explícita.
2. **Acesso cruzado proibido:** tentativa de acessar ou modificar registro de outro tenant resulta em "não encontrado" (HTTP 404) — nunca "proibido" (403), para não revelar a existência do recurso.
3. **Escrita automática:** em todo `INSERT`, o `BaseRepository` seta `tenant_id` com o valor do contexto atual.
4. **Tasks Celery:** o `tenant_id` deve ser passado **explicitamente** no payload da task, nunca assumido do ContextVar (que não existe no worker). O worker configura o ContextVar a partir do payload antes de executar a lógica.
5. **Tenant inativo:** requisições de usuários de um tenant inativo devem ser rejeitadas (HTTP 403 ou 401, a definir em P03).

## Critérios de Aceite

- [ ] `BaseRepository.get(id)` nunca retorna registro de outro tenant, mesmo que o `id` exista para outro tenant.
- [ ] `BaseRepository.create(data)` sempre seta `tenant_id` do contexto, sem necessidade de passá-lo explicitamente.
- [ ] Fixture `with_tenant(id)` configura corretamente o contexto para testes.
- [ ] Teste de isolamento: dois tenants com dados semelhantes; query de um nunca retorna dados do outro.
- [ ] Worker Celery com `tenant_id` no payload → contexto configurado corretamente antes da execução.
- [ ] Módulo que herda `TenantMixin` tem a coluna e o índice criados via migration.

## Estratégia de Testes

### Testes Unitários

- Resolução do `tenant_id` a partir de um payload JWT mockado → ContextVar configurado corretamente.
- `BaseRepository`: query de leitura gera SQL com `WHERE tenant_id = ?` — verificar via `echo=True` ou inspeção do statement.
- `TenantMixin`: presença da coluna `tenant_id` no modelo ORM.

### Testes de Integração

- Criar dois tenants e registros em cada um. `BaseRepository` com tenant A não retorna registros do tenant B e vice-versa.
- `BaseRepository.create()` com contexto do tenant A seta `tenant_id = A` automaticamente.
- Task Celery mockada: payload com `tenant_id` → contexto configurado → query retorna apenas dados daquele tenant.

### Testes E2E

- Login com usuário do tenant A → operação de listagem → resultado só contém dados do tenant A.
- Login com usuário do tenant B → mesma operação → resultado só contém dados do tenant B.

## Riscos Técnicos

- **Vazamento por bypass do BaseRepository:** se um módulo escrever uma query direta com SQLAlchemy sem herdar do `BaseRepository`, o filtro não é aplicado. Mitigar com revisão de PR obrigatória e testes de isolamento por módulo.
- **Propagação de tenant em tasks Celery:** ContextVar não sobrevive à serialização. A passagem explícita deve ser padrão documentado e verificado.
- **Performance:** índice em `tenant_id` é obrigatório em todas as tabelas de domínio para evitar full scans.
- **Slug único global:** garantir unicidade de slug entre todos os tenants (índice único na tabela).

## Complexidade

**Alta** — decisão arquitetural que afeta todos os módulos e deve ser acertada antes de qualquer desenvolvimento de domínio.

## Prioridade

**Crítica** — bloqueador de todos os módulos de domínio.

## Branch

`feature/001-multi-tenancy`
