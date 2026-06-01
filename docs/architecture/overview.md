# Visão Arquitetural (C4 — Contexto e Contêineres)

## Nível 1 — Contexto

```
┌─────────────────────────────────────────────────────────────────┐
│                        EMPRESA (Tenant)                          │
│                                                                   │
│  [Solicitante]  [Técnico]  [Supervisor]  [Admin]                 │
│       │              │           │           │                   │
│       └──────────────┴───────────┴───────────┘                   │
│                          │ HTTPS                                  │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                ┌──────────▼──────────┐
                │   Plataforma de      │
                │   Manutenção         │
                │   (este sistema)     │
                └──────────┬──────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         [E-mail]    [PostgreSQL]   [MinIO]
         SMTP         (dados)      (arquivos)
```

---

## Nível 2 — Contêineres

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Docker Compose (on-premise)                      │
│                                                                           │
│  ┌─────────────┐    ┌──────────────────────────────────────────────┐    │
│  │   Nginx      │    │              API (FastAPI)                    │    │
│  │  (reverse   ├───►│  Python 3.12 + Uvicorn                       │    │
│  │   proxy)    │    │  Porta: 8000                                  │    │
│  └─────────────┘    │  Módulos: auth, users, teams, tickets,       │    │
│                      │           sla, notifications, dashboards...  │    │
│                      └────────┬───────────────────┬────────────────┘    │
│                               │                   │                      │
│                    ┌──────────▼──────┐   ┌────────▼──────────┐         │
│                    │   PostgreSQL 16  │   │      Redis         │         │
│                    │   Porta: 5432    │   │      Porta: 6379   │         │
│                    │   Dados de       │   │   Broker Celery    │         │
│                    │   domínio        │   │   + Pub/Sub WS     │         │
│                    └─────────────────┘   └────────────────────┘         │
│                                                                           │
│  ┌─────────────────────────────────────────────┐                        │
│  │              Celery Workers                  │                        │
│  │  Tarefas: e-mail, SLA alerts, auto-close    │                        │
│  └─────────────────────────────────────────────┘                        │
│                                                                           │
│  ┌─────────────────────┐   ┌─────────────────────┐                     │
│  │   Celery Beat        │   │       MinIO          │                     │
│  │   Scheduler          │   │   S3-compatível      │                     │
│  │   Jobs periódicos    │   │   Porta: 9000        │                     │
│  └─────────────────────┘   └─────────────────────┘                     │
│                                                                           │
│  ┌─────────────────────┐                                                 │
│  │   Frontend (Vite)    │                                                 │
│  │   React + TypeScript │                                                 │
│  │   Porta: 3000        │                                                 │
│  └─────────────────────┘                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Fluxo de requisição autenticada (happy path)

```
Browser → Nginx → API (FastAPI)
                    │
                    ├─ Middleware: extrai JWT Bearer
                    ├─ get_current_user(): valida token, configura ContextVar(tenant_id)
                    ├─ require_permission("xxx"): verifica RBAC
                    ├─ Router → Service → Repository
                    │                       │
                    │                       └─ BaseRepository: WHERE tenant_id = :ctx
                    │                                           ↕
                    │                                      PostgreSQL
                    └─ Resposta JSON paginada com envelope padrão
```

---

## Fluxo de WebSocket (notificações em tempo real)

```
Browser ──WS──► API (FastAPI /ws/notifications)
                    │
                    ├─ Valida JWT na abertura da conexão
                    ├─ Registra conexão por user_id em memória local
                    │
API (outro worker) ─► Redis PUBLISH channel:user:{id}
                    │
API (todos workers) ◄─ Redis SUBSCRIBE → envia para conexões locais
                    │
Browser ◄──WS──────┘
```

---

## Fluxo de job Celery (SLA, e-mail, auto-close)

```
Celery Beat → Enfileira task com {tenant_id, ...payload}
                    │
Celery Worker ──────┘
    │
    ├─ Configura ContextVar(tenant_id) a partir do payload
    ├─ Executa lógica com BaseRepository (tenant isolado)
    ├─ Emite notificação se necessário
    └─ Commit + log de resultado
```

---

## Decisões arquiteturais

Ver `decisions/` para os ADRs que justificam as escolhas acima.

| Decisão | ADR |
|---------|-----|
| BaseRepository como único acesso a dados de domínio | ADR-0001 |
| Cross-tenant retorna 404 | ADR-0002 |
| Status.code como âncora da state machine | ADR-0003 |
| tenant_id explícito em Celery | ADR-0004 |
