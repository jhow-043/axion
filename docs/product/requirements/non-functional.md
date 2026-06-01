# Requisitos Não-Funcionais

> Requisitos transversais que afetam todo o sistema. Não pertencem a uma spec única —
> são verificados em todo PR e considerados em toda decisão arquitetural.

---

## RNF-SEG — Segurança

| ID | Requisito | Verificação |
|----|-----------|-------------|
| RNF-SEG-001 | Isolamento total de dados entre tenants — nenhum dado de um tenant pode ser acessado por outro | Testes de isolamento obrigatórios por módulo (INV-01) |
| RNF-SEG-002 | Senhas armazenadas com Argon2 — nunca em texto claro ou MD5/SHA1 | Code review + teste unitário de hashing |
| RNF-SEG-003 | JWT com expiração curta (access: 15 min) e rotação de refresh token | Teste de expiração e rotação |
| RNF-SEG-004 | Refresh token revogado invalida todos os tokens do usuário | Teste de detecção de roubo |
| RNF-SEG-005 | Nenhum segredo em código, variáveis de ambiente ou valores padrão fixos | Hook pre-commit + ruff |
| RNF-SEG-006 | Stack trace não exposto em produção (mensagem genérica em 500) | Teste de erro não tratado |
| RNF-SEG-007 | Rate limiting em endpoints de autenticação (configurável) | Evolução v1.1 |
| RNF-SEG-008 | CORS configurável por ambiente — origens explícitas, sem wildcard em produção | Config revisada por ambiente |
| RNF-SEG-009 | Acesso cross-tenant retorna 404, nunca 403 (INV-02) | Testes de isolamento |
| RNF-SEG-010 | Arquivos armazenados no MinIO com URLs assinadas de curta duração | Teste de URL expirada |

---

## RNF-PERF — Performance

| ID | Requisito | Verificação |
|----|-----------|-------------|
| RNF-PERF-001 | P95 de listagem de chamados com filtros padrão < 500ms | Índice em `(tenant_id, status_id)`, `(tenant_id, assignee_id)` |
| RNF-PERF-002 | Todo modelo de domínio tem índice em `tenant_id` | Code review + migration review |
| RNF-PERF-003 | Paginação máxima de 100 itens por requisição | Validação de `page_size` em `BaseRepository` |
| RNF-PERF-004 | Jobs SLA rodam a cada 5 minutos; não devem acumular backlog | Celery Beat com idempotência |
| RNF-PERF-005 | Papéis e permissões carregados por requisição (não do token) para consistência | Potencial cache Redis em v1.1 |

---

## RNF-DISP — Disponibilidade e Resiliência

| ID | Requisito | Verificação |
|----|-----------|-------------|
| RNF-DISP-001 | `GET /health` reflete estado real do banco e retorna 200 quando saudável | Teste de healthcheck com banco down |
| RNF-DISP-002 | Workers Celery reiniciam automaticamente em caso de falha | Docker Compose restart policy |
| RNF-DISP-003 | E-mail: retry automático com backoff exponencial (3 tentativas) em caso de falha SMTP | Teste de retry com SMTP mockado |
| RNF-DISP-004 | Falha de envio de e-mail não afeta persistência da notificação in-app | Teste de isolamento de canal |
| RNF-DISP-005 | Jobs Celery idempotentes: rodar duas vezes não duplica efeitos | Testes unitários de idempotência |

---

## RNF-MANUT — Manutenibilidade

| ID | Requisito | Verificação |
|----|-----------|-------------|
| RNF-MANUT-001 | `ruff check .` e `ruff format --check .` passam em todo PR | CI obrigatório |
| RNF-MANUT-002 | `pytest -q` passa em todo PR sem erros | CI obrigatório |
| RNF-MANUT-003 | Estrutura de módulo padrão seguida em todo novo módulo | Code review + spec-reviewer |
| RNF-MANUT-004 | Migrations Alembic acompanham todo PR que altera schema | Checklist de PR |
| RNF-MANUT-005 | Sem comentários óbvios — apenas o "porquê" | Code review |
| RNF-MANUT-006 | Sem arquivos > 500 linhas (alerta para refatoração) | Code review |

---

## RNF-OBS — Observabilidade

| ID | Requisito | Verificação |
|----|-----------|-------------|
| RNF-OBS-001 | Logging estruturado (JSON) em todas as requisições HTTP | Middleware de logging em P00 |
| RNF-OBS-002 | Logs incluem `tenant_id`, `user_id`, `request_id` quando disponíveis | Middleware de contexto |
| RNF-OBS-003 | Erros não tratados logados com stack trace completo (nunca exposto ao cliente) | Handler global de exceções |
| RNF-OBS-004 | Jobs Celery logam início, fim e resultado de cada execução | Padrão de log por task |

---

## RNF-INT — Integração e Deploy

| ID | Requisito | Verificação |
|----|-----------|-------------|
| RNF-INT-001 | Deploy via Docker Compose on-premise sem dependência de cloud | `docker compose up -d` funcional |
| RNF-INT-002 | Variáveis de ambiente documentadas em `.env.example` | Presente no repositório |
| RNF-INT-003 | Migrations executadas automaticamente no startup (ou manual documentado) | Documentado em `environments.md` |
| RNF-INT-004 | MinIO configurado como storage local S3-compatível — sem dependência de AWS | Docker Compose inclui MinIO |
| RNF-INT-005 | Redis como broker Celery e pub/sub para WebSocket multi-instância | Docker Compose inclui Redis |

---

## RNF-A11Y — Acessibilidade (Frontend)

| ID | Requisito | Verificação |
|----|-----------|-------------|
| RNF-A11Y-001 | Contraste de texto conforme WCAG AA (4.5:1 para texto normal) | Revisão visual + ferramentas de contraste |
| RNF-A11Y-002 | Navegação por teclado funcional em formulários e modais | Teste manual |
| RNF-A11Y-003 | Atributos ARIA em componentes interativos não cobertos pelo shadcn/ui | Code review |
| RNF-A11Y-004 | Mensagens de erro associadas ao campo via `aria-describedby` | Code review |

---

## RNF-I18N — Internacionalização

| ID | Requisito | Verificação |
|----|-----------|-------------|
| RNF-I18N-001 | Interface em pt-BR | — |
| RNF-I18N-002 | Timestamps em UTC no banco; conversão para timezone do tenant apenas na exibição | Padrão de SLA (P12) |
| RNF-I18N-003 | Datas exibidas no formato `dd/mm/yyyy` e `dd/mm/yyyy HH:mm` | Componente de data compartilhado |

---

## RNF-DADOS — Integridade e Retenção

| ID | Requisito | Verificação |
|----|-----------|-------------|
| RNF-DADOS-001 | Soft delete para entidades de domínio referenciadas — nunca hard delete | Modelos com `is_active` ou `deleted_at` |
| RNF-DADOS-002 | UUID v4 como chave primária em todas as entidades | Padrão de model |
| RNF-DADOS-003 | `created_at` e `updated_at` em todas as entidades de domínio | TenantMixin ou BaseModel |
| RNF-DADOS-004 | Backup diário do PostgreSQL documentado nos procedimentos de deploy | `environments.md` |
