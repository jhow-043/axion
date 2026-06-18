# Visão do Produto

## Problema

Empresas industriais e prediais gerenciam manutenções de forma fragmentada — via WhatsApp,
planilhas ou sistemas genéricos que não refletem o fluxo real de um chamado de manutenção.
Isso gera falta de visibilidade sobre SLAs, dificuldade de rastreamento e perda de histórico.

## Solução

**HUB modular multi-tenant** que concentra a gestão operacional das empresas clientes.
Cada empresa acessa uma única plataforma e enxerga apenas os módulos/produtos liberados
para ela. O primeiro módulo disponível é **Gestão de Manutenção Industrial e Predial**:

- Abertura estruturada de chamados (industrial por equipamento, predial por local).
- Workflow claro de status com responsabilidades definidas por papel.
- Controle de SLA configurável com alertas automáticos.
- Histórico completo via timeline e auditoria.
- Visibilidade operacional e gerencial em tempo real.

Novos módulos (ex.: Controle de Estoque, Solicitações de Compra) serão integrados ao mesmo
HUB no futuro, sem exigir novo login ou nova instalação.

## Modelo de Negócio

**Multi-tenant SaaS on-premise** — cada empresa (tenant) opera de forma isolada na mesma
instância, com Deploy via Docker Compose na infraestrutura do cliente.

O super-administrador da plataforma controla quais módulos estão liberados para cada empresa.

## Personas

| Persona | Papel no sistema | Necessidade principal |
|---------|-----------------|----------------------|
| **Solicitante** | Abre chamados, valida soluções | Visibilidade do status do seu chamado |
| **Técnico** | Assume e executa chamados | Fila de trabalho clara e registro de solução |
| **Supervisor** | Gerencia equipe e chamados | Visão da equipe, SLA, escaladas |
| **Admin** | Configura o sistema | Configurar políticas, usuários, catálogos |

## Objetivos de negócio

1. Reduzir tempo médio de atendimento (MTTR) com SLA configurável e alertas.
2. Garantir rastreabilidade completa de cada chamado do início ao fim.
3. Permitir configuração autônoma pelos clientes (catálogos, equipes, SLA).
4. Suportar múltiplas empresas na mesma instalação com isolamento total.
5. Permitir que a plataforma cresça com novos módulos/produtos sem quebrar o que já existe.

## Escopo

### MVP — Gestão de Manutenção (P00–P19)

As specs P00–P19 definem o produto de manutenção completo, incluindo a área de plataforma
para o super-administrador (P19).

### HUB Modular (P20–P24)

As specs P20–P24 transformam a base em plataforma extensível:
- **P20** — Núcleo de módulos (backend): catálogo + vínculo por empresa + gating.
- **P21** — Gestão de módulos no super-admin: UI para liberar/revogar por empresa.
- **P22** — Home do HUB e sessão modular (frontend).
- **P23** — Menu e rotas modulares (Sidebar data-driven, guard por módulo).
- **P24** — Consolidação do módulo `manutencao` (apply gating nos routers existentes).

### Fora do escopo atual (evoluções futuras)

- Billing, planos e cotas por empresa.
- SSO / integração AD/LDAP.
- White-label por tenant.
- Aplicativo mobile.
- Novos módulos além de `manutencao` (definidos em specs futuras).
