import { Navigate } from "react-router";
import { useAuth } from "@/shared/hooks/useAuth";
import { hasMinRole } from "@/utils/permissions";

export function DashboardRedirect() {
  const { session } = useAuth();

  if (!session) return <Navigate to="/login" replace />;

  const target = hasMinRole(session.roles, "supervisor")
    ? "/dashboard/supervisor"
    : "/dashboard/technician";

  return <Navigate to={target} replace />;
}
