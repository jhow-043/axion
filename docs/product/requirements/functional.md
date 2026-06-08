# Requisitos Funcionais

> Catálogo numerado de requisitos funcionais. Cada RF é realizado por uma ou mais specs.
> O detalhe completo (regras, APIs, telas, critérios de aceite) vive na spec, não aqui.
> Esta lista serve como índice de rastreabilidade e referência rápida.

---

## Infraestrutura e Plataforma

| ID | Requisito | Spec |
|----|-----------|------|
| RF-001 | O sistema deve ter um servidor HTTP com healthcheck (`/health`, `/ping`) | P00 |
| RF-002 | Erros devem retornar envelope padronizado com `error`, `message`, `detail`, `timestamp` | P00 |
| RF-003 | Paginação via `page` e `page_size` deve ser padrão em todas as listagens | P00 |
| RF-004 | Configuração carregada exclusivamente via variáveis de ambiente | P00 |

## Multi-Tenancy

| ID | Requisito | Spec |
|----|-----------|------|
| RF-010 | Cada empresa (tenant) opera com dados completamente isolados das demais | P01 |
| RF-011 | O isolamento de tenant é aplicado automaticamente por `BaseRepository` sem esforço por módulo | P01 |
| RF-012 | Acesso cross-tenant retorna 404, nunca revela a existência do recurso | P01 |
| RF-013 | O `tenant_id` do usuário autenticado é extraído do JWT e propagado via ContextVar | P01 |

## Autenticação

| ID | Requisito | Spec |
|----|-----------|------|
| RF-020 | Login por email e senha com emissão de `access_token` (JWT) e `refresh_token` | P03 |
| RF-021 | Renovação de tokens com rotação automática do `refresh_token` | P03 |
| RF-022 | Logout invalida o `refresh_token` | P03 |
| RF-023 | Senhas armazenadas com hash Argon2 | P03 |
| RF-024 | Resposta de login inválido é genérica (sem revelar se o email existe) | P03 |
| RF-025 | Token revogado detectado invalida todos os tokens do usuário (detecção de roubo) | P03 |
| RF-026 | Endpoint `GET /auth/me` retorna dados do usuário autenticado incluindo papéis | P03 |

## Usuários e Permissões

| ID | Requisito | Spec |
|----|-----------|------|
| RF-030 | CRUD de usuários por tenant com isolamento automático | P04 |
| RF-031 | Controle de acesso por papéis (RBAC): Admin, Supervisor, Técnico, Solicitante | P04 |
| RF-032 | Papéis padrão provisionados automaticamente em cada novo tenant | P04 |
| RF-033 | Permissões são a união de todos os papéis do usuário | P04 |
| RF-034 | Admin não pode remover o próprio papel de Admin se for o único | P04 |
| RF-035 | Usuário inativo não consegue autenticar | P04 |
| RF-036 | Email único por tenant (mesmo email pode existir em tenants diferentes) | P04 |

## Equipes

| ID | Requisito | Spec |
|----|-----------|------|
| RF-040 | CRUD de equipes de manutenção por tenant | P05 |
| RF-041 | Chamados podem ser direcionados a uma equipe | P05, P09 |
| RF-042 | Técnicos são membros de equipes | P05 |

## Setores e Locais

| ID | Requisito | Spec |
|----|-----------|------|
| RF-050 | CRUD de setores (agrupamentos organizacionais) por tenant | P06 |
| RF-051 | CRUD de locais prediais vinculados a setores | P06 |
| RF-052 | Locais ativos podem ser vinculados a chamados prediais | P06, P09 |

## Catálogos Configuráveis

| ID | Requisito | Spec |
|----|-----------|------|
| RF-060 | Catálogo de prioridades configurável (código invariante, rótulo editável) | P07 |
| RF-061 | Catálogo de status de chamado configurável (código invariante, rótulo editável) | P07 |
| RF-062 | Catálogo de categorias de chamado configurável | P07 |
| RF-063 | Catálogo de motivos de pendência configurável | P07 |
| RF-064 | Remoção de item de catálogo em uso deve ser bloqueada | P07 |

## Equipamentos

| ID | Requisito | Spec |
|----|-----------|------|
| RF-070 | CRUD de equipamentos por tenant com vinculação a local e equipe | P08 |
| RF-071 | Equipamentos ativos podem ser vinculados a chamados industriais | P08, P09 |

## Chamados — Núcleo e Workflow

| ID | Requisito | Spec |
|----|-----------|------|
| RF-080 | Abertura de chamado industrial exige equipamento ativo do tenant | P09 |
| RF-081 | Abertura de chamado predial exige local ativo do tenant | P09 |
| RF-082 | Chamado inicia com status `new` | P09 |
| RF-083 | Técnico assume chamado: define responsável e move para `in_progress` | P09 |
| RF-084 | Transição para `pending` exige motivo de pendência obrigatório | P09 |
| RF-085 | Transição para `resolved` exige descrição de solução obrigatória | P09 |
| RF-086 | Chamado `closed` não pode ser transitado para nenhum status | P09 |
| RF-087 | Observadores podem comentar mas não realizar transições | P09 |
| RF-088 | Comentário editável apenas pelo autor dentro de janela de 15 minutos | P09 |
| RF-089 | Solicitante vê apenas chamados onde é requester ou observador | P09 |
| RF-090 | Técnico vê chamados da sua equipe e os atribuídos a ele | P09 |
| RF-091 | Supervisor e Admin veem todos os chamados do tenant | P09 |
| RF-092 | Listagem de chamados com filtros por tipo, status, prioridade, equipe, responsável, período | P09 |

## Timeline

| ID | Requisito | Spec |
|----|-----------|------|
| RF-100 | Cada ação no chamado gera um evento de timeline imutável | P10 |
| RF-101 | Timeline exibida em ordem cronológica no detalhe do chamado | P10 |

## Anexos e Evidências

| ID | Requisito | Spec |
|----|-----------|------|
| RF-110 | Upload de arquivos (imagens, documentos) vinculados a chamados | P11 |
| RF-111 | Arquivos armazenados em MinIO (S3-compatível) com acesso por URL assinada | P11 |
| RF-112 | Tamanho máximo e tipos permitidos configuráveis | P11 |

## SLA

| ID | Requisito | Spec |
|----|-----------|------|
| RF-120 | Política de SLA configurável por (tipo de chamado × prioridade × equipe) | P12 |
| RF-121 | SLA de Atendimento: prazo para assumir o chamado | P12 |
| RF-122 | SLA de Resolução: prazo para resolver após assumir | P12 |
| RF-123 | SLA de Resolução pausado automaticamente quando chamado entra em `pending` | P12 |
| RF-124 | Prazo de resolução recalculado com desconto do tempo pausado ao retomar | P12 |
| RF-125 | Alerta automático quando SLA atinge o limiar de risco configurado | P12 |
| RF-126 | Marcação automática de SLA vencido por job Celery idempotente | P12 |
| RF-127 | Indicador de SLA visível no detalhe do chamado | P12 |

## Encerramento e Validação

| ID | Requisito | Spec |
|----|-----------|------|
| RF-130 | Solicitante valida ou rejeita solução dentro do prazo | P13 |
| RF-131 | Rejeição da solução volta o chamado para `in_progress` | P13 |
| RF-132 | Auto-fechamento após decurso do prazo de validação sem resposta | P13 |

## Notificações

| ID | Requisito | Spec |
|----|-----------|------|
| RF-140 | Notificação in-app persistida para cada evento relevante | P14 |
| RF-141 | Push de notificação em tempo real via WebSocket para usuários conectados | P14 |
| RF-142 | E-mail assíncrono via Celery/SMTP para notificações importantes | P14 |
| RF-143 | Preferências de notificação por usuário (opt-out por tipo e canal) | P14 |
| RF-144 | Autor da ação não recebe notificação sobre ela | P14 |
| RF-145 | WebSocket de notificações funciona em ambientes multi-instância via Redis pub/sub | P14 |

## Dashboards Operacionais

| ID | Requisito | Spec |
|----|-----------|------|
| RF-150 | Dashboard do técnico: chamados atribuídos, SLA em risco, fila da equipe | P15 |
| RF-151 | Dashboard do supervisor: visão da equipe, SLA, chamados em aberto por status | P15 |

## Dashboard Gerencial e Relatórios

| ID | Requisito | Spec |
|----|-----------|------|
| RF-160 | Dashboard gerencial com métricas de volume, SLA, MTTR por período | P16 |
| RF-161 | Exportação de relatórios (CSV/Excel) com filtros por período, equipe, tipo | P16 |

## Auditoria

| ID | Requisito | Spec |
|----|-----------|------|
| RF-170 | Registro de auditoria de todas as alterações em entidades sensíveis | P17 |
| RF-171 | Log de auditoria imutável (append-only) com actor, ação, timestamp e dados anteriores | P17 |

## Administração

| ID | Requisito | Spec |
|----|-----------|------|
| RF-180 | Console de configuração para Admin: usuários, equipes, catálogos, SLA, notificações | P18 |
| RF-181 | Provisionamento de tenant com papéis e configurações padrão | P18 |
| RF-182 | Ativação/desativação de tenant pelo super-admin | P18 |

## Plataforma Super-Admin

| ID | Requisito | Spec |
|----|-----------|------|
| RF-190 | Dashboard global com métricas agregadas de todas as empresas (tenants) | P19 |
| RF-191 | Listagem paginada de companies com contadores de usuários e chamados | P19 |
| RF-192 | Provisionamento de novo tenant pelo super-admin via modal | P19 |
| RF-193 | Soft delete de tenant com ocultação automática em todas as queries | P19 |
| RF-194 | Tenant do sistema (`is_system`) protegido contra exclusão | P19 |
