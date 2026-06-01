# Modelo de Dados Consolidado

> Visão unificada de todas as entidades das 19 specs.
> Fonte da verdade é o código (migrations Alembic) — este documento é referência de design.
> Atualizar junto com cada spec que cria/altera entidades.

---

## Convenções globais

- **PK:** UUID v4 em todas as entidades.
- **tenant_id:** presente em toda entidade de domínio (via `TenantMixin`), com índice.
- **Timestamps:** `created_at` e `updated_at` em todas as entidades.
- **Soft delete:** entidades referenciadas usam `is_active` ou `deleted_at` em vez de hard delete.
- **Nomenclatura:** tabelas em `snake_case` plural; colunas em `snake_case`.

---

## Módulo: Tenants (P01)

```
tenants
├── id              UUID, PK
├── name            String, NOT NULL
├── slug            String, UNIQUE, NOT NULL
├── is_active       Boolean, DEFAULT true
├── created_at      DateTime
└── updated_at      DateTime
```

---

## Módulo: Autenticação (P03)

```
refresh_tokens
├── id              UUID, PK
├── user_id         UUID, FK → users
├── token_hash      String, UNIQUE
├── expires_at      DateTime
├── revoked_at      DateTime, nullable
└── created_at      DateTime
```

---

## Módulo: Usuários e Permissões (P04)

```
users
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── name            String, NOT NULL
├── email           String, NOT NULL
│                   UNIQUE(tenant_id, email)
├── password_hash   String, NOT NULL
├── is_active       Boolean, DEFAULT true
├── created_at      DateTime
└── updated_at      DateTime

roles
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── name            String, NOT NULL
├── code            String, NOT NULL
│                   UNIQUE(tenant_id, code)
├── is_default      Boolean, DEFAULT false
├── created_at      DateTime
└── updated_at      DateTime

permissions
├── id              UUID, PK
├── code            String, UNIQUE        # "ticket:create", "user:manage"...
└── name            String, NOT NULL

user_roles
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── user_id         UUID, FK → users
├── role_id         UUID, FK → roles
│                   UNIQUE(user_id, role_id)
└── created_at      DateTime

role_permissions
├── id              UUID, PK
├── role_id         UUID, FK → roles
├── permission_id   UUID, FK → permissions
│                   UNIQUE(role_id, permission_id)
└── created_at      DateTime
```

---

## Módulo: Equipes (P05)

```
teams
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── name            String, NOT NULL
├── is_active       Boolean, DEFAULT true
├── created_at      DateTime
└── updated_at      DateTime

team_members
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── team_id         UUID, FK → teams
├── user_id         UUID, FK → users
│                   UNIQUE(team_id, user_id)
└── joined_at       DateTime
```

---

## Módulo: Setores e Locais (P06)

```
sectors
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── name            String, NOT NULL
├── is_active       Boolean, DEFAULT true
├── created_at      DateTime
└── updated_at      DateTime

locations
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── sector_id       UUID, FK → sectors
├── name            String, NOT NULL
├── is_active       Boolean, DEFAULT true
├── created_at      DateTime
└── updated_at      DateTime
```

---

## Módulo: Catálogos (P07)

```
priorities
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── name            String, NOT NULL
├── code            String, NOT NULL       # âncora invariante
│                   UNIQUE(tenant_id, code)
├── order           Integer
├── is_active       Boolean, DEFAULT true
├── created_at      DateTime
└── updated_at      DateTime

ticket_statuses
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── name            String, NOT NULL
├── code            String, NOT NULL       # "new", "in_progress", "pending", "resolved", "closed"
│                   UNIQUE(tenant_id, code)
├── order           Integer
├── is_visible      Boolean, DEFAULT true
├── created_at      DateTime
└── updated_at      DateTime

categories
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── name            String, NOT NULL
├── is_active       Boolean, DEFAULT true
├── created_at      DateTime
└── updated_at      DateTime

pending_reasons
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── name            String, NOT NULL
├── is_active       Boolean, DEFAULT true
├── created_at      DateTime
└── updated_at      DateTime
```

---

## Módulo: Equipamentos (P08)

```
equipments
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── location_id     UUID, FK → locations
├── team_id         UUID, FK → teams, nullable
├── name            String, NOT NULL
├── code            String, nullable       # código patrimonial
├── is_active       Boolean, DEFAULT true
├── created_at      DateTime
└── updated_at      DateTime
```

---

## Módulo: Chamados (P09)

```
tickets
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── type            Enum('industrial','predial'), NOT NULL
├── title           String, NOT NULL
├── description     Text, NOT NULL
├── priority_id     UUID, FK → priorities, NOT NULL
├── status_id       UUID, FK → ticket_statuses, NOT NULL
├── category_id     UUID, FK → categories, nullable
├── equipment_id    UUID, FK → equipments, nullable
├── location_id     UUID, FK → locations, nullable
├── team_id         UUID, FK → teams, nullable
├── requester_id    UUID, FK → users, NOT NULL
├── assignee_id     UUID, FK → users, nullable
├── assigned_at     DateTime, nullable
├── resolved_at     DateTime, nullable
├── closed_at       DateTime, nullable
├── created_at      DateTime
├── updated_at      DateTime
│   INDEX(tenant_id, status_id)
│   INDEX(tenant_id, assignee_id)
│   INDEX(tenant_id, team_id)
└── INDEX(tenant_id, equipment_id)

ticket_observers
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── ticket_id       UUID, FK → tickets
├── user_id         UUID, FK → users
│                   UNIQUE(ticket_id, user_id)
└── added_at        DateTime

ticket_comments
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── ticket_id       UUID, FK → tickets
├── author_id       UUID, FK → users
├── content         Text, NOT NULL
├── created_at      DateTime
└── updated_at      DateTime

solutions
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── ticket_id       UUID, FK → tickets, UNIQUE
├── description     Text, NOT NULL
├── resolved_by     UUID, FK → users
└── resolved_at     DateTime
```

---

## Módulo: Timeline (P10)

```
ticket_events
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── ticket_id       UUID, FK → tickets, INDEX
├── actor_id        UUID, FK → users, nullable    # null = sistema
├── event_type      String, NOT NULL              # "ticket_created", "status_changed"...
├── payload         JSONB                         # dados específicos do evento
└── created_at      DateTime, INDEX
```

---

## Módulo: Anexos (P11)

```
attachments
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── ticket_id       UUID, FK → tickets, INDEX
├── uploader_id     UUID, FK → users
├── filename        String, NOT NULL
├── content_type    String, NOT NULL
├── size_bytes      Integer, NOT NULL
├── storage_key     String, NOT NULL              # path no MinIO
├── created_at      DateTime
└── updated_at      DateTime
```

---

## Módulo: SLA (P12)

```
sla_policies
├── id                    UUID, PK
├── tenant_id             UUID, FK → tenants, INDEX
├── ticket_type           Enum('industrial','predial','all'), NOT NULL
├── priority_id           UUID, FK → priorities, NOT NULL
├── team_id               UUID, FK → teams, nullable
├── attendance_minutes    Integer, NOT NULL
├── resolution_minutes    Integer, NOT NULL
├── alert_threshold_pct   Integer, DEFAULT 80
├── is_active             Boolean, DEFAULT true
│                          UNIQUE(tenant_id, ticket_type, priority_id, team_id)
├── created_at            DateTime
└── updated_at            DateTime

sla_trackers
├── id                         UUID, PK
├── tenant_id                  UUID, FK → tenants, INDEX
├── ticket_id                  UUID, FK → tickets, UNIQUE
├── policy_id                  UUID, FK → sla_policies
├── attendance_due_at          DateTime, nullable
├── attendance_status          Enum('running','met','breached'), DEFAULT 'running'
├── attendance_met_at          DateTime, nullable
├── attendance_alert_sent      Boolean, DEFAULT false
├── resolution_due_at          DateTime, nullable
├── resolution_status          Enum('running','paused','met','breached'), DEFAULT 'running'
├── resolution_met_at          DateTime, nullable
├── resolution_alert_sent      Boolean, DEFAULT false
├── total_paused_minutes       Integer, DEFAULT 0
├── created_at                 DateTime
└── updated_at                 DateTime

sla_pauses
├── id          UUID, PK
├── tenant_id   UUID, FK → tenants, INDEX
├── tracker_id  UUID, FK → sla_trackers, INDEX
├── paused_at   DateTime, NOT NULL
├── resumed_at  DateTime, nullable
└── minutes     Integer, nullable
```

---

## Módulo: Notificações (P14)

```
notifications
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── recipient_id    UUID, FK → users, INDEX
├── ticket_id       UUID, FK → tickets, nullable, INDEX
├── event_type      String, NOT NULL
├── title           String, NOT NULL
├── body            String, NOT NULL
├── is_read         Boolean, DEFAULT false
├── read_at         DateTime, nullable
├── email_sent      Boolean, DEFAULT false
├── email_sent_at   DateTime, nullable
└── created_at      DateTime, INDEX

notification_preferences
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── user_id         UUID, FK → users
├── event_type      String, NOT NULL
│                   UNIQUE(tenant_id, user_id, event_type)
├── in_app_enabled  Boolean, DEFAULT true
└── email_enabled   Boolean, DEFAULT true
```

---

## Módulo: Auditoria (P17)

```
audit_logs
├── id              UUID, PK
├── tenant_id       UUID, FK → tenants, INDEX
├── actor_id        UUID, FK → users, nullable    # null = sistema
├── entity_type     String, NOT NULL              # "ticket", "user", "sla_policy"...
├── entity_id       UUID, NOT NULL
├── action          String, NOT NULL              # "create", "update", "delete", "transition"
├── before          JSONB, nullable               # estado anterior
├── after           JSONB, nullable               # estado após
└── created_at      DateTime, INDEX
```
