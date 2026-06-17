import { useState } from "react";
import { X } from "lucide-react";
import { useTenantModules, useEnableModule, useRevokeModule } from "../api";

interface Props {
  tenantId: string;
  tenantName: string;
  onClose: () => void;
}

export function CompanyModulesModal({ tenantId, tenantName, onClose }: Props) {
  const { data, isLoading, error } = useTenantModules(tenantId);
  const [confirmRevokeId, setConfirmRevokeId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(
    null,
  );

  const enable = useEnableModule(tenantId);
  const revoke = useRevokeModule(tenantId);

  const enabledIds = new Set(data?.enabled.map((e) => e.module_id) ?? []);

  async function handleEnable(moduleId: string, moduleName: string) {
    setFeedback(null);
    try {
      await enable.mutateAsync(moduleId);
      setFeedback({ type: "success", text: `"${moduleName}" habilitado com sucesso.` });
    } catch {
      setFeedback({ type: "error", text: `Erro ao habilitar "${moduleName}".` });
    }
  }

  async function handleRevoke() {
    if (!confirmRevokeId || !data) return;
    const mod = data.catalog.find((m) => m.id === confirmRevokeId);
    setFeedback(null);
    try {
      await revoke.mutateAsync(confirmRevokeId);
      setFeedback({ type: "success", text: `"${mod?.name ?? "Módulo"}" revogado com sucesso.` });
    } catch {
      setFeedback({ type: "error", text: `Erro ao revogar "${mod?.name ?? "módulo"}".` });
    } finally {
      setConfirmRevokeId(null);
    }
  }

  const isPending = enable.isPending || revoke.isPending;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h3 className="text-base font-semibold">Módulos da empresa</h3>
            <p className="text-xs text-muted-foreground mt-0.5">{tenantName}</p>
          </div>
          <button onClick={onClose}>
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>

        <div className="p-6 space-y-3 max-h-96 overflow-y-auto">
          {isLoading && (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-10 bg-muted rounded animate-pulse" />
              ))}
            </div>
          )}

          {error && <p className="text-sm text-red-600">Erro ao carregar módulos.</p>}

          {data?.catalog.map((module) => {
            const isEnabled = enabledIds.has(module.id);
            return (
              <div
                key={module.id}
                className="flex items-center justify-between px-3 py-2.5 rounded border bg-muted/20"
              >
                <div>
                  <p className="text-sm font-medium">{module.name}</p>
                  <p className="text-xs text-muted-foreground font-mono">{module.code}</p>
                </div>
                <button
                  disabled={isPending}
                  onClick={() => {
                    if (isEnabled) {
                      setConfirmRevokeId(module.id);
                    } else {
                      void handleEnable(module.id, module.name);
                    }
                  }}
                  className={`px-3 py-1 rounded text-xs font-medium transition disabled:opacity-50 ${
                    isEnabled
                      ? "bg-green-100 text-green-700 hover:bg-red-100 hover:text-red-700"
                      : "bg-muted text-muted-foreground hover:bg-blue-100 hover:text-blue-700"
                  }`}
                >
                  {isEnabled ? "Habilitado" : "Desabilitado"}
                </button>
              </div>
            );
          })}
        </div>

        {feedback && (
          <div
            className={`mx-6 mb-4 px-3 py-2 rounded text-xs ${
              feedback.type === "success"
                ? "bg-green-50 text-green-700"
                : "bg-red-50 text-red-700"
            }`}
          >
            {feedback.text}
          </div>
        )}

        <div className="px-6 py-3 border-t flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded text-sm hover:bg-muted"
          >
            Fechar
          </button>
        </div>
      </div>

      {confirmRevokeId && data && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/20">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm space-y-4">
            <h3 className="text-base font-semibold">Revogar módulo</h3>
            <p className="text-sm text-muted-foreground">
              Tem certeza que deseja revogar{" "}
              <span className="font-medium text-foreground">
                {data.catalog.find((m) => m.id === confirmRevokeId)?.name ?? "este módulo"}
              </span>{" "}
              desta empresa? Os usuários perderão o acesso imediatamente.
            </p>
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => void handleRevoke()}
                disabled={revoke.isPending}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:opacity-50"
              >
                {revoke.isPending ? "Revogando..." : "Revogar"}
              </button>
              <button
                onClick={() => setConfirmRevokeId(null)}
                className="px-4 py-2 border rounded text-sm hover:bg-muted"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
