import { useState } from "react";

import { useAssignRole, useRemoveRole, useRoles } from "../api";
import type { RoleResponse } from "../types";

interface RoleAssignmentProps {
  userId: string;
  currentRoles: RoleResponse[];
}

export function RoleAssignment({ userId, currentRoles }: RoleAssignmentProps) {
  const [selectedRoleId, setSelectedRoleId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: allRoles } = useRoles();
  const assignRole = useAssignRole(userId);
  const removeRole = useRemoveRole(userId);

  const assignedIds = new Set(currentRoles.map((r) => r.id));
  const availableRoles = allRoles?.filter((r) => !assignedIds.has(r.id)) ?? [];

  async function handleAssign() {
    if (!selectedRoleId) return;
    setError(null);
    try {
      await assignRole.mutateAsync({ role_id: selectedRoleId });
      setSelectedRoleId("");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        "Erro ao atribuir papel.";
      setError(msg);
    }
  }

  async function handleRemove(roleId: string) {
    setError(null);
    try {
      await removeRole.mutateAsync(roleId);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        "Erro ao remover papel.";
      setError(msg);
    }
  }

  return (
    <div className="space-y-3">
      <h3 className="font-medium text-sm">Papéis atribuídos</h3>

      {error && (
        <div className="p-2 bg-red-50 border border-red-200 rounded text-red-700 text-xs">
          {error}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {currentRoles.map((role) => (
          <span
            key={role.id}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-blue-100 text-blue-700 rounded-full text-xs"
          >
            {role.name}
            <button
              onClick={() => void handleRemove(role.id)}
              className="hover:text-red-600 font-bold"
              title="Remover papel"
            >
              ×
            </button>
          </span>
        ))}
        {currentRoles.length === 0 && (
          <span className="text-sm text-gray-400">Nenhum papel atribuído.</span>
        )}
      </div>

      {availableRoles.length > 0 && (
        <div className="flex gap-2 items-center">
          <select
            value={selectedRoleId}
            onChange={(e) => setSelectedRoleId(e.target.value)}
            className="border rounded px-2 py-1.5 text-sm flex-1"
          >
            <option value="">Selecionar papel para adicionar...</option>
            {availableRoles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
          <button
            onClick={() => void handleAssign()}
            disabled={!selectedRoleId || assignRole.isPending}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition"
          >
            Adicionar
          </button>
        </div>
      )}
    </div>
  );
}
