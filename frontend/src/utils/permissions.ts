import type { UserRole, UserSession } from "@/types/api";

const ROLE_HIERARCHY: Record<UserRole, number> = {
  admin: 4,
  supervisor: 3,
  technician: 2,
  requester: 1,
};

export function hasRole(userRoles: string[], requiredRoles: UserRole[]): boolean {
  return requiredRoles.some((r) => userRoles.includes(r));
}

export function hasMinRole(userRoles: string[], minRole: UserRole): boolean {
  return userRoles.some((r) => (ROLE_HIERARCHY[r as UserRole] ?? 0) >= ROLE_HIERARCHY[minRole]);
}

export function hasPermission(session: UserSession | null, code: string): boolean {
  if (!session) return false;
  return session.permissions.includes(code);
}

// Permission code constants — mirror backend app/core/permissions.py
export const Permissions = {
  USER_READ: "user:read",
  USER_MANAGE: "user:manage",
  TEAM_MANAGE: "team:manage",
  TICKET_CREATE: "ticket:create",
  TICKET_READ: "ticket:read",
  TICKET_ASSIGN: "ticket:assign",
  TICKET_TRANSITION: "ticket:transition",
  TICKET_VALIDATE: "ticket:validate",
  DASHBOARD_OPERATIONAL: "dashboard:operational",
  DASHBOARD_MANAGEMENT: "dashboard:management",
  ADMIN_CONFIG: "admin:config",
  EQUIPMENT_READ: "equipment:read",
  EQUIPMENT_MANAGE: "equipment:manage",
  SYSTEM_ADMIN: "system_admin",
} as const;

export type PermissionCode = (typeof Permissions)[keyof typeof Permissions];
