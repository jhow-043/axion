import { useState } from "react";

import { usePriorities } from "@/features/catalog/api";
import { useAuth } from "@/shared/hooks/useAuth";
import { hasPermission, Permissions } from "@/utils/permissions";
import { useDeactivateSlaPolicy, useSlaPolices } from "../api";
import type { SlaPolicy } from "../types";
import { SlaPolicyForm } from "./SlaPolicyForm";

const TICKET_TYPE_LABELS: Record<string, string> = {
  industrial: "Industrial",
  predial: "Predial",
  all: "Todos",
};

function minutesToLabel(minutes: number): string {
  if (minutes < 60) return `${minutes}min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}min` : `${h}h`;
}

export function SlaPolicyList() {
  const { session } = useAuth();
  const canManage = hasPermission(session, Permissions.ADMIN_CONFIG);

  const [creating, setCreating] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<SlaPolicy | null>(null);
  const [confirmDeactivate, setConfirmDeactivate] = useState<string | null>(null);

  const { data, isLoading, error } = useSlaPolices();
  const { data: prioritiesData } = usePriorities();
  const deactivate = useDeactivateSlaPolicy();

  const priorityMap = new Map(prioritiesData?.items.map((p) => [p.id, p.name]) ?? []);

  if (isLoading) {
    return (
      <div className="p-6 space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-red-600">Erro ao carregar políticas de SLA. Tente novamente.</div>
    );
  }

  if (creating) {
    return (
      <div className="p-6 max-w-2xl">
        <h2 className="text-xl font-semibold mb-4">Nova política de SLA</h2>
        <SlaPolicyForm onSuccess={() => setCreating(false)} onCancel={() => setCreating(false)} />
      </div>
    );
  }

  if (editingPolicy) {
    return (
      <div className="p-6 max-w-2xl">
        <h2 className="text-xl font-semibold mb-4">Editar política de SLA</h2>
        <SlaPolicyForm
          existing={editingPolicy}
          onSuccess={() => setEditingPolicy(null)}
          onCancel={() => setEditingPolicy(null)}
        />
      </div>
    );
  }

  const policies = data?.items ?? [];

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Políticas de SLA</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Defina os tempos de atendimento e resolução por tipo e prioridade.
          </p>
        </div>
        {canManage && (
          <button
            onClick={() => setCreating(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm"
          >
            Nova política
          </button>
        )}
      </div>

      {policies.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          Nenhuma política de SLA cadastrada.
        </div>
      ) : (
        <div className="overflow-x-auto rounded border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-4 py-3 font-medium">Tipo</th>
                <th className="px-4 py-3 font-medium">Prioridade</th>
                <th className="px-4 py-3 font-medium">Atendimento</th>
                <th className="px-4 py-3 font-medium">Resolução</th>
                <th className="px-4 py-3 font-medium">Alerta</th>
                <th className="px-4 py-3 font-medium">Status</th>
                {canManage && <th className="px-4 py-3 font-medium">Ações</th>}
              </tr>
            </thead>
            <tbody className="divide-y">
              {policies.map((policy) => (
                <tr key={policy.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    {TICKET_TYPE_LABELS[policy.ticket_type] ?? policy.ticket_type}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {priorityMap.get(policy.priority_id) ?? policy.priority_id}
                  </td>
                  <td className="px-4 py-3">{minutesToLabel(policy.attendance_minutes)}</td>
                  <td className="px-4 py-3">{minutesToLabel(policy.resolution_minutes)}</td>
                  <td className="px-4 py-3">{policy.alert_threshold_pct}%</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                        policy.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {policy.is_active ? "Ativa" : "Inativa"}
                    </span>
                  </td>
                  {canManage && (
                    <td className="px-4 py-3 space-x-3">
                      <button
                        onClick={() => setEditingPolicy(policy)}
                        className="text-blue-600 hover:underline text-xs"
                      >
                        Editar
                      </button>
                      {policy.is_active &&
                        (confirmDeactivate === policy.id ? (
                          <span className="inline-flex gap-1 text-xs">
                            <button
                              onClick={() => {
                                deactivate.mutate(policy.id);
                                setConfirmDeactivate(null);
                              }}
                              className="text-red-600 font-medium hover:underline"
                            >
                              Confirmar
                            </button>
                            <button
                              onClick={() => setConfirmDeactivate(null)}
                              className="text-gray-500 hover:underline"
                            >
                              Cancelar
                            </button>
                          </span>
                        ) : (
                          <button
                            onClick={() => setConfirmDeactivate(policy.id)}
                            className="text-red-500 hover:underline text-xs"
                          >
                            Desativar
                          </button>
                        ))}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.total > (data.page_size ?? 20) && (
        <p className="text-sm text-gray-500">{data.total} políticas no total.</p>
      )}
    </div>
  );
}
