import { Navigate } from "react-router";
import { useAuth } from "@/shared/hooks/useAuth";
import { hasMinRole, hasPermission, Permissions } from "@/utils/permissions";

export function DashboardRedirect() {
  const { session } = useAuth();

  if (!session) return <Navigate to="/login" replace />;

  let target: string;
  if (hasPermission(session, Permissions.DASHBOARD_MANAGEMENT)) {
    target = "/dashboard/management";
  } else if (hasMinRole(session.roles, "supervisor")) {
    target = "/dashboard/supervisor";
  } else {
    target = "/dashboard/technician";
  }

  return <Navigate to={target} replace />;
}
