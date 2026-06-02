import { useState } from "react";
import { useNavigate } from "react-router";

import { useAuth } from "@/shared/hooks/useAuth";
import { hasPermission, Permissions } from "@/utils/permissions";
import { useDeactivateTeam, useTeams } from "../api";
import type { TeamFilters } from "../types";

export function TeamList() {
  const { session } = useAuth();
  const navigate = useNavigate();
  const canManage = hasPermission(session, Permissions.TEAM_MANAGE);

  const [filters, setFilters] = useState<TeamFilters>({ page: 1, page_size: 20 });
  const { data, isLoading, error } = useTeams(filters);
  const deactivate = useDeactivateTeam();

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
    return <div className="p-6 text-red-600">Erro ao carregar equipes. Tente novamente.</div>;
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="p-6 text-center text-gray-500">
        Nenhuma equipe encontrada.
        {canManage && (
          <button
            onClick={() => void navigate("/teams/new")}
            className="ml-2 text-blue-600 underline"
          >
            Criar equipe
          </button>
        )}
      </div>
    );
  }

  const totalPages = Math.ceil(data.total / (filters.page_size ?? 20));

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Equipes</h1>
        {canManage && (
          <button
            onClick={() => void navigate("/teams/new")}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Nova equipe
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-3">
        <select
          className="border rounded px-3 py-1.5 text-sm"
          value={filters.is_active === undefined ? "" : String(filters.is_active)}
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              is_active: e.target.value === "" ? undefined : e.target.value === "true",
              page: 1,
            }))
          }
        >
          <option value="">Todos os status</option>
          <option value="true">Ativa</option>
          <option value="false">Inativa</option>
        </select>
      </div>

      <div className="overflow-x-auto rounded border">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th className="px-4 py-3 font-medium">Nome</th>
              <th className="px-4 py-3 font-medium">Membros</th>
              <th className="px-4 py-3 font-medium">Status</th>
              {canManage && <th className="px-4 py-3 font-medium">Ações</th>}
            </tr>
          </thead>
          <tbody className="divide-y">
            {data.items.map((team) => (
              <tr
                key={team.id}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => void navigate(`/teams/${team.id}`)}
              >
                <td className="px-4 py-3 font-medium">{team.name}</td>
                <td className="px-4 py-3 text-gray-600">{team.member_count}</td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                      team.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {team.is_active ? "Ativa" : "Inativa"}
                  </span>
                </td>
                {canManage && (
                  <td className="px-4 py-3 space-x-3" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => void navigate(`/teams/${team.id}`)}
                      className="text-blue-600 hover:underline text-xs"
                    >
                      Editar
                    </button>
                    {team.is_active && (
                      <button
                        onClick={() => {
                          if (confirm(`Desativar equipe "${team.name}"?`)) {
                            deactivate.mutate(team.id);
                          }
                        }}
                        className="text-red-500 hover:underline text-xs"
                      >
                        Desativar
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            {data.total} equipes — página {filters.page} de {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              disabled={(filters.page ?? 1) <= 1}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
              className="px-3 py-1 border rounded disabled:opacity-40"
            >
              Anterior
            </button>
            <button
              disabled={(filters.page ?? 1) >= totalPages}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
              className="px-3 py-1 border rounded disabled:opacity-40"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
