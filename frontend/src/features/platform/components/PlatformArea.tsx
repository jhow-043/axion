import { NavLink, Outlet } from "react-router";
import { LayoutDashboard, Building2 } from "lucide-react";
import { cn } from "@/utils/cn";

const PLATFORM_SECTIONS = [
  { to: "/plataforma", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/plataforma/empresas", label: "Empresas", icon: Building2, end: false },
] as const;

export function PlatformArea() {
  return (
    <div className="flex h-full min-h-0">
      <aside className="w-48 shrink-0 border-r bg-muted/30 py-4 overflow-y-auto">
        <p className="px-4 pb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Plataforma
        </p>
        <nav>
          {PLATFORM_SECTIONS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
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
      <div className="flex-1 overflow-y-auto">
        <Outlet />
      </div>
    </div>
  );
}
