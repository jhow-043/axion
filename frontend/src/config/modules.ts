export interface ModuleDefinition {
  code: string;
  label: string;
  description: string;
  icon: string;
  homeRoute: string;
}

export const MODULE_REGISTRY: ModuleDefinition[] = [
  {
    code: "manutencao",
    label: "Gestão de Manutenção",
    description: "Chamados, SLA, equipamentos e dashboards operacionais.",
    icon: "Wrench",
    homeRoute: "/dashboard",
  },
];
