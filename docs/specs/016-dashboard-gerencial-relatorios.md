---
id: P16
slug: dashboard-gerencial-relatorios
status: approved
version: 1.0.0
owner: jhowworks
depends_on: [P01, P04, P09, P12, P15]
satisfies: [RF-160, RF-161, RNF-PERF-001]
adrs: [ADR-0001, ADR-0002]
branch: feature/016-dashboard-gerencial-relatorios
last_updated: 2026-06-01
---

# P16 — Dashboard Gerencial & Relatórios

## Objetivo

Fornecer aos gestores indicadores estratégicos sobre o desempenho da manutenção, cumprimento de SLA, equipamentos mais problemáticos e desempenho por equipe, além de relatórios exportáveis em CSV.

## Escopo

- Dashboard gerencial com indicadores: volume de chamados, tempos médios, cumprimento de SLA, chamados por tipo/prioridade/status.
- Ranking de equipamentos com mais chamados e maior índice de criticidade.
- Desempenho por equipe: volume, SLA, tempo médio de resolução.
- Filtros por período, tipo, prioridade e equipe.
- Relatórios exportáveis em CSV: chamados, SLA, equipamentos, desempenho de equipes.

## Fora do Escopo

- Dashboard operacional diário (P15).
- Agendamento automático de relatórios por e-mail (futuro).
- Integração com BI externo / Power BI / Metabase (futuro).
- Alertas proativos gerenciais (futuro).

## Dependências

- **P01** (Multi-Tenancy).
- **P04** (Usuários e Permissões) — `require_permission("dashboard:management")`.
- **P05** (Equipes).
- **P08** (Equipamentos).
- **P09** (Chamados).
- **P12** (SLA) — `sla_trackers` para métricas de cumprimento.

## Entidades Impactadas

Nenhuma nova entidade. Leitura agregada de `tickets`, `sla_trackers`, `equipments`, `teams`, `users`.

## APIs Necessárias

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/v1/dashboards/management` | Indicadores gerenciais | `dashboard:management` |
| GET | `/api/v1/reports/tickets` | Relatório de chamados (CSV ou JSON) | `dashboard:management` |
| GET | `/api/v1/reports/sla` | Relatório de SLA | `dashboard:management` |
| GET | `/api/v1/reports/equipments` | Relatório de equipamentos | `dashboard:management` |
| GET | `/api/v1/reports/teams` | Relatório de desempenho de equipes | `dashboard:management` |

### Parâmetros comuns (query string)
- `date_from`, `date_to` (obrigatórios para relatórios).
- `team_id`, `priority_id`, `ticket_type` (opcionais).
- `format` = `json` (padrão) ou `csv`.

### Resposta de `GET /dashboards/management`
```json
{
  "period": { "from": "2024-01-01", "to": "2024-01-31" },
  "summary": {
    "total_tickets": 120,
    "open": 35,
    "closed": 85,
    "by_type": { "industrial": 78, "predial": 42 },
    "by_priority": { "critical": 8, "high": 25, "medium": 62, "low": 25 },
    "avg_resolution_hours": 14.5
  },
  "sla": {
    "attendance_compliance_pct": 94,
    "resolution_compliance_pct": 81,
    "breached_count": 23
  },
  "top_problematic_equipments": [
    { "equipment_id": "uuid", "name": "Bomba B-01", "ticket_count": 12, "critical_count": 3 }
  ],
  "team_performance": [
    {
      "team_id": "uuid",
      "name": "Elétrica",
      "total": 38,
      "sla_compliance_pct": 85,
      "avg_resolution_hours": 10.2
    }
  ]
}
```

### Exportação CSV

Para `format=csv`, o backend retorna o arquivo com `Content-Type: text/csv` e `Content-Disposition: attachment; filename="relatorio.csv"`. Não é necessário pré-gerar o arquivo — geração sob demanda (streaming de linhas CSV).

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Dashboard Gerencial | Cartões de KPIs, gráficos de barra/linha (Recharts), ranking de equipamentos, tabela de desempenho por equipe |
| Relatórios | Filtros de período e tipo; botão de exportar CSV; tabela preview dos dados |

### Gráficos sugeridos (Recharts)
- Evolução de chamados abertos/fechados por semana (LineChart).
- Distribuição por prioridade (BarChart ou PieChart).
- Cumprimento de SLA ao longo do tempo (LineChart com linha de meta).
- Ranking de equipamentos (BarChart horizontal).

## Regras de Negócio

1. **Filtro de período obrigatório nos relatórios:** evitar geração de relatórios sem limite de data (custo de query).
2. **Limite de período:** máximo de 12 meses por exportação (configurável em `core/config.py`).
3. **Cumprimento de SLA:** `compliance_pct = sla_met / (sla_met + sla_breached) × 100`. Chamados sem SLA aplicável (sem política configurada) são excluídos do cálculo.
4. **Equipamento mais problemático:** ranking por total de chamados no período, com sub-ranking por criticidade (chamados com prioridade Alta ou Crítica).
5. **Desempenho de equipe:** inclui apenas chamados fechados no período (para calcular tempo médio de resolução real).
6. **Acesso:** apenas usuários com papel Admin ou Supervisor (com permissão `dashboard:management`).

## Critérios de Aceite

- [ ] `GET /dashboards/management` retorna indicadores corretos para o período informado.
- [ ] Ranking de equipamentos bate com os dados de chamados semeados.
- [ ] `GET /reports/tickets?format=csv` retorna arquivo CSV com cabeçalho e dados corretos.
- [ ] `GET /reports/tickets` sem `date_from`/`date_to` → 422.
- [ ] Período maior que 12 meses → 422.
- [ ] Usuário com papel Técnico → 403 ao acessar dashboard gerencial.
- [ ] Gráficos renderizados corretamente no frontend com dados reais.

## Estratégia de Testes

### Testes Unitários

- Cálculo de `compliance_pct` com diferentes combinações (met=0, breached=0, mix).
- Cálculo de `avg_resolution_hours` com datas mockadas.
- Montagem do CSV: cabeçalho e linhas corretos.

### Testes de Integração

- `GET /dashboards/management` com dataset conhecido → todos os indicadores corretos.
- `GET /reports/tickets?format=csv` → resposta com Content-Type e dados corretos.
- Período inválido → 422.
- Acesso sem permissão → 403.

### Testes E2E

- Gestor acessa dashboard → gráficos renderizados com dados não-vazios.
- Gestor aplica filtro de período e equipe → dados filtrados.
- Gestor exporta CSV de chamados → arquivo baixado com colunas corretas.

## Riscos Técnicos

- **Desempenho de queries analíticas:** agregações com JOINs em múltiplas tabelas grandes. Estratégia: índices compostos + limitar período obrigatoriamente + avaliar views materializadas ou tabelas de resumo se a performance não for satisfatória.
- **Precisão de métricas de SLA com pausas:** o tempo real de resolução deve descontar os períodos em Pendente (usar `sla_trackers.total_paused_minutes`).
- **Geração de CSV sob demanda:** para relatórios grandes, usar streaming (generator) para evitar timeout e consumo de memória excessivo.

## Complexidade

**Média**

## Prioridade

**Média**

## Branch

`feature/016-dashboard-gerencial-relatorios`
