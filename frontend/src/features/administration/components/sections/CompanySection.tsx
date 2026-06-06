import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/shared/api/client";

interface TenantSettingsResponse {
  id: string;
  auto_close_days: number;
  updated_at: string;
}

function useAdminSettings() {
  return useQuery({
    queryKey: ["admin", "settings"],
    queryFn: async () => {
      const { data } = await apiClient.get<TenantSettingsResponse>("/admin/settings");
      return data;
    },
  });
}

function useUpdateAdminSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { auto_close_days: number }) => {
      const { data } = await apiClient.patch<TenantSettingsResponse>("/admin/settings", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["admin", "settings"] });
    },
  });
}

export function CompanySection() {
  const { data, isLoading } = useAdminSettings();
  const update = useUpdateAdminSettings();
  const [days, setDays] = useState<number | "">("");
  const [saved, setSaved] = useState(false);

  const currentDays = data?.auto_close_days ?? 5;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const value = typeof days === "number" ? days : currentDays;
    update.mutate(
      { auto_close_days: value },
      {
        onSuccess: () => {
          setSaved(true);
          setDays("");
          setTimeout(() => setSaved(false), 3000);
        },
      },
    );
  }

  return (
    <div className="p-6 max-w-lg space-y-6">
      <h2 className="text-xl font-semibold">Configurações da Empresa</h2>

      {isLoading ? (
        <div className="h-24 bg-gray-100 rounded animate-pulse" />
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dias para auto-fechamento de chamados validados
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Chamados solucionados são fechados automaticamente após este prazo sem resposta do
              solicitante. Valor atual: <strong>{currentDays} dias</strong>.
            </p>
            <input
              type="number"
              min={1}
              max={90}
              className="border rounded px-3 py-2 w-32 text-sm"
              value={days}
              onChange={(e) => setDays(e.target.value === "" ? "" : Number(e.target.value))}
              placeholder={String(currentDays)}
            />
          </div>

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={update.isPending || days === ""}
              className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {update.isPending ? "Salvando..." : "Salvar"}
            </button>
            {saved && <span className="text-sm text-green-600">Configurações salvas.</span>}
            {update.isError && (
              <span className="text-sm text-red-600">Erro ao salvar. Tente novamente.</span>
            )}
          </div>
        </form>
      )}
    </div>
  );
}
