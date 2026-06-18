import { useNavigate } from "react-router";
import { Wrench } from "lucide-react";
import { useAuth } from "@/shared/hooks/useAuth";
import { MODULE_REGISTRY, type ModuleDefinition } from "@/config/modules";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  Wrench,
};

function ModuleCard({ mod }: { mod: ModuleDefinition }) {
  const navigate = useNavigate();
  const Icon = ICON_MAP[mod.icon];

  return (
    <div className="flex flex-col gap-4 rounded-xl border bg-card p-6 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-center gap-3">
        {Icon && <Icon className="h-7 w-7 text-primary" />}
        <h2 className="text-lg font-semibold">{mod.label}</h2>
      </div>
      <p className="flex-1 text-sm text-muted-foreground">{mod.description}</p>
      <button
        type="button"
        onClick={() => navigate(mod.homeRoute)}
        className="mt-auto self-start rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
      >
        Acessar
      </button>
    </div>
  );
}

export function HubHome() {
  const { session, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  const enabledModules = session?.enabled_modules ?? [];
  const visibleModules = MODULE_REGISTRY.filter((m) => enabledModules.includes(m.code));

  if (visibleModules.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
        <p className="text-lg font-medium text-foreground">Nenhum módulo disponível.</p>
        <p className="text-sm text-muted-foreground">
          Entre em contato com o administrador para liberar o acesso.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Bem-vindo ao HUB</h1>
        <p className="text-sm text-muted-foreground">Selecione um módulo para começar.</p>
      </div>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {visibleModules.map((mod) => (
          <ModuleCard key={mod.code} mod={mod} />
        ))}
      </div>
    </div>
  );
}
