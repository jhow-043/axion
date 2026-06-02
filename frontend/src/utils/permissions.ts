import type { UserRole } from "@/types/api";

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
