import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "@/shared/hooks/useAuth";

export function RequireAuth() {
  const { session, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return null;

  if (!session) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}
