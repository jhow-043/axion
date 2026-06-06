import { NavLink, Outlet } from "react-router";
import { Building2, Users, Users2, MapPin, BookOpen, ShieldCheck, Bell, ClipboardList, Server } from "lucide-react";
import { cn } from "@/utils/cn";
import { useAuth } from "@/shared/hooks/useAuth";
import { hasPermission, Permissions } from "@/utils/permissions";

const ADMIN_SECTIONS = [
  { to: "/administracao/empresa", label: "Empresa", icon: Building2 },
  { to: "/administracao/usuarios", label: "Usuários", icon: Users },
  { to: "/administracao/equipes", label: "Equipes", icon: Users2 },
  { to: "/administracao/setores", label: "Setores", icon: MapPin },
  { to: "/administracao/catalogos", label: "Catálogos", icon: BookOpen },
  { to: "/administracao/sla", label: "SLA", icon: ShieldCheck },
  { to: "/administracao/notificacoes", label: "Notificações", icon: Bell },
  { to: "/administracao/auditoria", label: "Auditoria", icon: ClipboardList },
] as const;

const SUPER_ADMIN_SECTION = { to: "/administracao/tenants", label: "Empresas (sistema)", icon: Server };

export function AdminConsole() {
  const { session } = useAuth();
  const isSuperAdmin = hasPermission(session, Permissions.SYSTEM_ADMIN);

  const sections = isSuperAdmin
    ? [...ADMIN_SECTIONS, SUPER_ADMIN_SECTION]
    : ADMIN_SECTIONS;

  return (
    <div className="flex h-full min-h-0">
      {/* Secondary sidebar */}
      <aside className="w-48 shrink-0 border-r bg-muted/30 py-4 overflow-y-auto">
        <p className="px-4 pb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Administração
        </p>
        <nav>
          {sections.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2 px-4 py-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground",
                  isActive && "bg-accent text-accent-foreground font-medium",
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto">
        <Outlet />
      </div>
    </div>
  );
}
