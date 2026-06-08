import { NavLink } from "react-router";
import {
  LayoutDashboard,
  Ticket,
  Users,
  Settings,
  Wrench,
  MapPin,
  BarChart2,
  Server,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { useAuth } from "@/shared/hooks/useAuth";
import { hasPermission, Permissions } from "@/utils/permissions";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/tickets", label: "Chamados", icon: Ticket },
  { to: "/equipments", label: "Equipamentos", icon: Wrench },
  { to: "/setores", label: "Setores / Locais", icon: MapPin },
  { to: "/users", label: "Usuários", icon: Users },
  { to: "/relatorios", label: "Relatórios", icon: BarChart2 },
  { to: "/administracao", label: "Administração", icon: Settings },
] as const;

const PLATFORM_ITEM = { to: "/plataforma", label: "Plataforma", icon: Server };

interface SidebarProps {
  open: boolean;
  onToggle: () => void;
}

export function Sidebar({ open }: SidebarProps) {
  const { session } = useAuth();
  const isSaasAdmin = hasPermission(session, Permissions.SYSTEM_ADMIN);

  return (
    <aside
      className={cn(
        "flex flex-col bg-sidebar text-sidebar-foreground transition-all duration-300",
        open ? "w-56" : "w-14",
      )}
    >
      <div className="flex h-14 items-center justify-center border-b border-sidebar-border px-4">
        {open ? (
          <span className="text-sm font-semibold tracking-wide">Manutenção</span>
        ) : (
          <Wrench className="h-5 w-5" />
        )}
      </div>

      <nav className="flex-1 overflow-y-auto py-4">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-4 py-2.5 text-sm transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                isActive && "bg-sidebar-accent text-sidebar-accent-foreground font-medium",
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {open && <span>{label}</span>}
          </NavLink>
        ))}

        {isSaasAdmin && (
          <NavLink
            to={PLATFORM_ITEM.to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-4 py-2.5 text-sm transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                isActive && "bg-sidebar-accent text-sidebar-accent-foreground font-medium",
              )
            }
          >
            <PLATFORM_ITEM.icon className="h-4 w-4 shrink-0" />
            {open && <span>{PLATFORM_ITEM.label}</span>}
          </NavLink>
        )}
      </nav>
    </aside>
  );
}
