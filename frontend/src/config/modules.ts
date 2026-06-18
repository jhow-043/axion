export interface NavItem {
  to: string;
  label: string;
  icon: string;
}

export interface ModuleDefinition {
  code: string;
  label: string;
  description: string;
  icon: string;
  homeRoute: string;
  navItems: NavItem[];
}

export const MODULE_REGISTRY: ModuleDefinition[] = [
  {
    code: "manutencao",
    label: "Gestão de Manutenção",
    description: "Chamados, SLA, equipamentos e dashboards operacionais.",
    icon: "Wrench",
    homeRoute: "/dashboard",
    navItems: [
      { to: "/dashboard", label: "Dashboard", icon: "LayoutDashboard" },
      { to: "/tickets", label: "Chamados", icon: "Ticket" },
      { to: "/equipments", label: "Equipamentos", icon: "Wrench" },
      { to: "/setores", label: "Setores / Locais", icon: "MapPin" },
      { to: "/users", label: "Usuários", icon: "Users" },
      { to: "/relatorios", label: "Relatórios", icon: "BarChart2" },
      { to: "/administracao", label: "Administração", icon: "Settings" },
    ],
  },
];
