import type { ReactNode } from "react";
import { Navigate } from "react-router";
import type { UserRole } from "@/types/api";
import { hasRole } from "@/utils/permissions";
import { useAuth } from "@/shared/hooks/useAuth";

interface RequireRoleProps {
  roles: UserRole[];
  children: ReactNode;
  fallback?: ReactNode;
}

export function RequireRole({ roles, children, fallback }: RequireRoleProps) {
  const { session } = useAuth();

  if (!session) return <Navigate to="/login" replace />;

  if (!hasRole(session.role, roles)) {
    if (fallback !== undefined) return <>{fallback}</>;
    return <Navigate to="/sem-permissao" replace />;
  }

  return <>{children}</>;
}
