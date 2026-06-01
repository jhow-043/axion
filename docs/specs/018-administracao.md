---
id: P18
slug: administracao
status: approved
version: 1.0.0
owner: jhowworks
depends_on: [P04, P05, P06, P07, P12, P14]
satisfies: [RF-180, RF-181, RF-182]
adrs: [ADR-0001, ADR-0002]
branch: feature/018-administracao
last_updated: 2026-06-01
---

# P18 — Administração (Console de Configuração)

## Objetivo

Consolidar em um único console todas as telas de configuração do sistema, oferecendo ao administrador acesso centralizado a equipes, catálogos, locais, setores, usuários, permissões, SLAs, notificações, prazo de auto-fechamento e gestão de empresas (tenants). P18 é um **orquestrador de UI** — não duplica regras de negócio, que vivem nos módulos.

## Escopo

- Console de administração com navegação por seções.
- Seções e conteúdo:
  - **Empresa:** informações do tenant (nome, slug) e configurações gerais (`auto_close_days`, limiar de SLA).
  - **Usuários:** lista, criação, edição, ativação/desativação, papéis (reusa módulo P04).
  - **Equipes:** lista, criação, edição, membros (reusa módulo P05).
  - **Setores:** lista, criação, edição (reusa módulo P06).
  - **Locais:** lista, criação, edição (reusa módulo P06).
  - **Catálogos:** prioridades, status (editável), categorias, motivos de pendência (reusa módulo P07).
  - **SLA:** políticas de SLA (reusa módulo P12).
  - **Notificações:** preferências globais padrão (reusa módulo P14).
  - **Auditoria:** log de auditoria (reusa módulo P17).
- Gestão de tenants (super-admin): listar, criar, ativar/desativar tenants. *Nota: super-admin é um papel global fora do escopo de tenant — implementar com cuidado de isolamento.*

## Fora do Escopo

- Regras de negócio dos módulos (cada módulo mantém as suas).
- Billing / planos por tenant.
- Configuração de integração AD/LDAP (futuro).
- White-label por tenant (futuro).

## Dependências

- **P04** (Usuários e Permissões) — `require_permission("admin:config")`.
- **P05** (Equipes).
- **P06** (Setores/Locais).
- **P07** (Catálogos).
- **P12** (SLA).
- **P13** (tenant_settings com `auto_close_days`).
- **P14** (Notificações — preferências).
- **P17** (Auditoria).
- **P01** (Multi-Tenancy — gestão de tenants).

## Entidades Impactadas

Nenhuma nova entidade de domínio. Consolida acesso às existentes.

Única adição: `tenant_settings` já definida em P13 — P18 expõe a edição completa desse registro.

## APIs Necessárias

P18 não cria novos endpoints de domínio — apenas orquestra os endpoints dos módulos existentes. A única API nova é a de gestão de tenants (super-admin):

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/admin/tenants` | Listar todos os tenants | super-admin |
| POST | `/api/v1/admin/tenants` | Criar novo tenant (provisionar) | super-admin |
| PATCH | `/api/v1/admin/tenants/{id}` | Editar tenant | super-admin |
| POST | `/api/v1/admin/tenants/{id}/activate` | Ativar tenant | super-admin |
| POST | `/api/v1/admin/tenants/{id}/deactivate` | Desativar tenant | super-admin |

*Super-admin: usuário com papel `system_admin` que não pertence a nenhum tenant específico; acessa o sistema fora do contexto de tenant. Implementar com verificação explícita e sem passar pelo `BaseRepository` filtrado.*

Endpoint de settings do tenant (definido em P13, consolidado aqui para referência):
- `GET/PATCH /api/v1/admin/settings` — já coberto em P13.

## Telas Necessárias

| Seção | Tela | Descrição |
|-------|------|-----------|
| Empresa | Configurações Gerais | Nome do tenant, `auto_close_days`, limiar de SLA |
| Usuários | Lista + Formulário | Reusa telas de P04 dentro do contexto do console |
| Equipes | Lista + Membros | Reusa telas de P05 |
| Setores | Lista + Formulário | Reusa telas de P06 |
| Locais | Lista + Formulário | Reusa telas de P06 |
| Catálogos | Prioridades / Status / Categorias / Motivos | Reusa telas de P07 |
| SLA | Políticas de SLA | Reusa telas de P12 |
| Notificações | Preferências Globais | Reusa telas de P14 |
| Auditoria | Log de Auditoria | Reusa telas de P17 |
| Tenants (super-admin) | Lista + Formulário | Tela específica de P18 para gestão de empresas |

### Layout do Console
- Sidebar secundária (dentro do layout shell de P02) com as seções listadas.
- Área de conteúdo renderiza o componente do módulo correspondente.
- Cada seção é um módulo React importado do respectivo `feature/` — sem duplicar componentes.

## Regras de Negócio

1. **P18 é orquestrador:** nenhuma regra de negócio nova. Toda validação, autorização e lógica vivem nos módulos que P18 chama.
2. **Acesso restrito a Admin:** todas as seções exigem `require_permission("admin:config")`, verificado no módulo de origem.
3. **Provisionar tenant:** ao criar um novo tenant, o sistema deve:
   a. Criar o registro em `tenants`.
   b. Executar o seed de dados padrão (papéis, permissões, prioridades, status padrão, `tenant_settings`).
   c. Criar o usuário admin inicial do tenant.
   Tudo em uma única transação ou operação coordenada.
4. **Super-admin fora do contexto de tenant:** o papel `system_admin` deve ser identificado sem `tenant_id`. O `BaseRepository` não deve ser usado para queries de `tenants` feitas pelo super-admin (consulta global sem filtro de tenant).
5. **Alterações no console auditadas:** qualquer alteração de configuração gera log em P17.

## Critérios de Aceite

- [ ] Admin acessa o console e navega entre todas as seções sem erros.
- [ ] Cada seção exibe e permite editar as configurações do seu módulo.
- [ ] Usuário sem papel Admin → 403 ao acessar qualquer seção do console.
- [ ] Provisionar novo tenant via super-admin → tenant criado, seed aplicado, admin inicial criado.
- [ ] Desativar tenant → usuários do tenant não conseguem mais autenticar.
- [ ] Alterar `auto_close_days` → novas validações usam o novo prazo (integração com P13).
- [ ] Toda alteração de configuração gera log de auditoria (P17).
- [ ] Console não duplica lógica — delega tudo aos módulos.

## Estratégia de Testes

### Testes Unitários

- Fluxo de provisionar tenant: todos os passos do seed executados em ordem.
- Super-admin: verificação de papel sem tenant_id.

### Testes de Integração

- `POST /admin/tenants` → tenant + seed + admin inicial criados em transação.
- `POST /admin/tenants/{id}/deactivate` → usuários do tenant retornam 401 ao tentar logar.
- Alterar `auto_close_days` via console → valor persistido em `tenant_settings`.
- Cada alteração de config → log em `audit_logs`.

### Testes E2E

- Super-admin cria tenant → admin do novo tenant loga → vê sistema zerado com dados padrão.
- Admin acessa console → navega por Usuários → cria técnico → técnico aparece na lista.
- Admin edita política de SLA → log aparece em Auditoria.

## Riscos Técnicos

- **Console vira módulo-deus:** mitigar mantendo P18 estritamente como orquestrador de UI. Se encontrar lógica duplicada, mover para o módulo de origem.
- **Provisionamento de tenant em transação:** o seed envolve múltiplas tabelas. Garantir rollback completo se qualquer etapa falhar.
- **Super-admin e multi-tenancy:** o papel `system_admin` é uma exceção ao modelo de tenant-per-request. Isolar bem essa lógica para não criar brecha de bypass do `BaseRepository` nos endpoints normais.

## Complexidade

**Média** — sem lógica própria complexa, mas requer coordenação com quase todos os módulos e o cuidado com o super-admin.

## Prioridade

**Alta**

## Branch

`feature/018-administracao`
