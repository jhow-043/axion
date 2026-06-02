from __future__ import annotations

# Central registry of all permission codes.
# Every module that calls require_permission() must use constants from this file.
# Adding a new permission here is the only place it needs to be defined.

USER_READ = "user:read"
USER_MANAGE = "user:manage"

TEAM_MANAGE = "team:manage"

TICKET_CREATE = "ticket:create"
TICKET_READ = "ticket:read"
TICKET_ASSIGN = "ticket:assign"
TICKET_TRANSITION = "ticket:transition"
TICKET_VALIDATE = "ticket:validate"

DASHBOARD_OPERATIONAL = "dashboard:operational"
DASHBOARD_MANAGEMENT = "dashboard:management"

ADMIN_CONFIG = "admin:config"

EQUIPMENT_READ = "equipment:read"
EQUIPMENT_MANAGE = "equipment:manage"

# Full catalogue as a list — used by seed to populate the permissions table.
ALL_PERMISSIONS: list[tuple[str, str]] = [
    (USER_READ, "Visualizar usuários"),
    (USER_MANAGE, "Gerenciar usuários"),
    (TEAM_MANAGE, "Gerenciar equipes"),
    (TICKET_CREATE, "Criar chamado"),
    (TICKET_READ, "Listar e ver chamados"),
    (TICKET_ASSIGN, "Assumir chamado"),
    (TICKET_TRANSITION, "Transicionar chamado"),
    (TICKET_VALIDATE, "Validar solução"),
    (DASHBOARD_OPERATIONAL, "Ver dashboards operacionais"),
    (DASHBOARD_MANAGEMENT, "Ver dashboard gerencial"),
    (ADMIN_CONFIG, "Gerenciar configurações"),
    (EQUIPMENT_READ, "Ver equipamentos"),
    (EQUIPMENT_MANAGE, "Gerenciar equipamentos"),
]
