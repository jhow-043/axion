# Inventário de Specs — Status Real

> Status do **frontmatter** = o que foi declarado ao escrever a spec.
> Status **real** = avaliação da implementação atual (a preencher/confirmar na Fase A).

| ID | Slug | Status frontmatter | Status real | Objetivo | Dependências |
|----|------|--------------------|-------------|----------|--------------|
| P00 | fundacao-backend | done | ✅ Implementado | FastAPI skeleton, logging, healthcheck, paginação, test setup | Nenhuma |
| P01 | multitenancy | done | ⚠️ A verificar | Isolamento total por tenant: TenantMixin, BaseRepository, ContextVar | P00 |
| P02 | fundacao-frontend | done | ⚠️ A verificar | SPA React: router, AuthProvider, axios, layout shell, WebSocket base | P00, P03 |
| P03 | autenticacao | in-review | ⚠️ A verificar | Login/logout/refresh JWT, /auth/me, token rotation | P00, P01, P04 |
| P04 | usuarios-rbac | in-review | ⚠️ A verificar | CRUD usuários, RBAC, `require_permission()`, seed roles/permissions | P01, P03 |
| P05 | equipes | in-review | ⚠️ A verificar | CRUD equipes, gerenciamento de membros (técnicos) | P01, P04 |
| P06 | setores-locais | in-review | ⚠️ A verificar | CRUD setores e locais prediais, unicidade por tenant | P01, P04 |
| P07 | catalogos | in-review | ⚠️ A verificar | CRUD prioridades, status, categorias, motivos de pendência (seed + proteção) | P01, P04 |
| P08 | equipamentos | in-review | ⚠️ A verificar | CRUD equipamentos, histórico de chamados por equipamento | P01, P04, P06 |
| P09 | chamados-core | in-review | ⚠️ A verificar | Criação, state machine, atribuição, observadores, comentários | P01, P04, P05, P06, P07, P08 |
| P10 | timeline | done | ⚠️ A verificar | Registro imutável/cronológico de eventos do chamado | P01, P09 |
| P11 | anexos-minio | in-review | ⚠️ A verificar | Upload direto MinIO via presigned URL, confirmação, listagem, deleção | P01, P09, P10 |
| P12 | sla | in-review | ⚠️ A verificar | Políticas, motor SLA, pause/resume, jobs Celery de alerta/breach | P01, P04, P05, P07, P09 |
| P13 | encerramento-validacao | in-review | ⚠️ A verificar | Solução + validação do solicitante + auto-fechamento Celery | P01, P09, P12, P14 |
| P14 | notificacoes | done | ⚠️ A verificar | In-app + WebSocket + e-mail async, preferências por usuário | P01, P04, P09 |
| P15 | dashboards-operacionais | in-review | ⚠️ A verificar | Dashboard técnico, supervisor, Kanban (drag & drop) | P01, P04, P05, P09, P12 |
| P16 | dashboard-gerencial | done | ⚠️ A verificar | KPIs gerenciais, ranking equipamentos, performance equipes, CSV | P01, P09, P12 |
| P17 | auditoria | in-review | ⚠️ A verificar | Audit trail imutável para ações administrativas | P01, P04 |
| P18 | administracao | in-review | ⚠️ A verificar | Console admin centralizado (usuários, equipes, catálogos, SLA, notificações, auditoria) | P04–P07, P12, P14, P17 |
| P19 | gestao-plataforma | in-progress | ⚠️ A verificar | Super-admin: dashboard global, provisioning, soft delete de tenants | P01, P04, P18 |

---

## Legenda de status real

| Símbolo | Significado |
|---------|-------------|
| ✅ Implementado | Código completo, testes passando, fluxo validado na UI |
| ⚠️ A verificar | Código existe mas fluxo funcional não foi validado |
| 🔴 Quebrado | Problemas confirmados que impedem uso básico |
| 🟡 Parcial | Parcialmente funcional; algum critério de aceite não atendido |
| ❌ Não implementado | Código ausente ou skeleton |

---

## Specs marcadas como `done` no frontmatter (prioridade de verificação)

Estas specs foram declaradas prontas mas ainda precisam de validação funcional completa:

- **P00** — fundação; baixo risco de regressão.
- **P01** — multitenancy; crítico; qualquer falha aqui afeta tudo.
- **P02** — fundação frontend; risco em guardas de rota e AuthProvider.
- **P10** — timeline; verificar se é gravado corretamente pelas transições do P09.
- **P14** — notificações; alto risco (WebSocket, async, preferências).
- **P16** — dashboard gerencial; verificar agregações e exportação CSV.

---

*Atualizado na Fase A conforme diagnóstico de cada subplano.*
