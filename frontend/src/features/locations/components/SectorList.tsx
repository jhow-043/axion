import { useState } from "react";

import { useAuth } from "@/shared/hooks/useAuth";
import { hasPermission, Permissions } from "@/utils/permissions";
import { useDeactivateSector, useReactivateSector, useSectors } from "../api";
import type { EntityFilters } from "../types";
import { SectorForm } from "./SectorForm";

export function SectorList() {
  const { session } = useAuth();
  const canManage = hasPermission(session, Permissions.ADMIN_CONFIG);

  const [filters, setFilters] = useState<EntityFilters>({ page: 1, page_size: 20 });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [confirmDeactivate, setConfirmDeactivate] = useState<string | null>(null);

  const { data, isLoading, error } = useSectors(filters);
  const deactivate = useDeactivateSector();
  const reactivate = useReactivateSector();

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
    return <div className="p-6 text-red-600">Erro ao carregar setores. Tente novamente.</div>;
  }

  if (creating) {
    return (
      <div className="p-6 max-w-lg">
        <h2 className="text-xl font-semibold mb-4">Novo Setor</h2>
        <SectorForm onSuccess={() => setCreating(false)} onCancel={() => setCreating(false)} />
      </div>
    );
  }

  if (editingId) {
    return (
      <div className="p-6 max-w-lg">
        <h2 className="text-xl font-semibold mb-4">Editar Setor</h2>
        <SectorForm
          sectorId={editingId}
          onSuccess={() => setEditingId(null)}
          onCancel={() => setEditingId(null)}
        />
      </div>
    );
  }

  const totalPages = Math.ceil((data?.total ?? 0) / (filters.page_size ?? 20));

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Setores</h1>
        {canManage && (
          <button
            onClick={() => setCreating(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm"
          >
            Novo setor
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
          <option value="true">Ativo</option>
          <option value="false">Inativo</option>
        </select>
      </div>

      {!data || data.items.length === 0 ? (
        <div className="text-center text-gray-500 py-8">Nenhum setor encontrado.</div>
      ) : (
        <div className="overflow-x-auto rounded border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-4 py-3 font-medium">Nome</th>
                <th className="px-4 py-3 font-medium">Descrição</th>
                <th className="px-4 py-3 font-medium">Status</th>
                {canManage && <th className="px-4 py-3 font-medium">Ações</th>}
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.items.map((sector) => (
                <tr key={sector.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{sector.name}</td>
                  <td className="px-4 py-3 text-gray-600">{sector.description ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                        sector.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {sector.is_active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  {canManage && (
                    <td className="px-4 py-3 space-x-3">
                      <button
                        onClick={() => setEditingId(sector.id)}
                        className="text-blue-600 hover:underline text-xs"
                      >
                        Editar
                      </button>
                      {sector.is_active ? (
                        confirmDeactivate === sector.id ? (
                          <span className="inline-flex gap-1 text-xs">
                            <button
                              onClick={() => {
                                deactivate.mutate(sector.id);
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
                            onClick={() => setConfirmDeactivate(sector.id)}
                            className="text-red-500 hover:underline text-xs"
                          >
                            Desativar
                          </button>
                        )
                      ) : (
                        <button
                          onClick={() => reactivate.mutate(sector.id)}
                          className="text-green-600 hover:underline text-xs"
                        >
                          Reativar
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            {data?.total} setores — página {filters.page} de {totalPages}
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
