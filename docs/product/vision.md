# Visão do Produto

## Problema

Empresas industriais e prediais gerenciam manutenções de forma fragmentada — via WhatsApp,
planilhas ou sistemas genéricos que não refletem o fluxo real de um chamado de manutenção.
Isso gera falta de visibilidade sobre SLAs, dificuldade de rastreamento e perda de histórico.

## Solução

Plataforma centralizada de **Gestão de Manutenção Industrial e Predial** que permite:
- Abertura estruturada de chamados (industrial por equipamento, predial por local).
- Workflow claro de status com responsabilidades definidas por papel.
- Controle de SLA configurável com alertas automáticos.
- Histórico completo via timeline e auditoria.
- Visibilidade operacional e gerencial em tempo real.

## Modelo de Negócio

**Multi-tenant SaaS on-premise** — cada empresa (tenant) opera de forma isolada na mesma
instância, com Deploy via Docker Compose na infraestrutura do cliente.

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

## Escopo da v1 (MVP)

As 19 specs (P00–P18) definem o escopo completo do MVP.
Funcionalidades fora do MVP (SSO, horário comercial, digest de e-mail, mobile) são registradas
como "evoluções" nas próprias specs.
