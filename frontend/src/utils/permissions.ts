import type { UserRole } from "@/types/api";

const ROLE_HIERARCHY: Record<UserRole, number> = {
  admin: 4,
  supervisor: 3,
  technician: 2,
  requester: 1,
};

export function hasRole(userRole: UserRole, requiredRoles: UserRole[]): boolean {
  return requiredRoles.includes(userRole);
}

export function hasMinRole(userRole: UserRole, minRole: UserRole): boolean {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[minRole];
}
