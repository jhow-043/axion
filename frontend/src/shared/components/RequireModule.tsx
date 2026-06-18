import { Navigate, Outlet } from "react-router";
import { useAuth } from "@/shared/hooks/useAuth";
import { hasModule } from "@/utils/permissions";

interface RequireModuleProps {
  code: string;
}

export function RequireModule({ code }: RequireModuleProps) {
  const { session, isLoading } = useAuth();

  if (isLoading) return null;

  if (!hasModule(session, code)) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
