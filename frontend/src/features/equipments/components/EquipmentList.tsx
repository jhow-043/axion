import { useState } from "react";
import { useNavigate } from "react-router";

import { useSectors } from "@/features/locations/api";
import { useAuth } from "@/shared/hooks/useAuth";
import { hasPermission, Permissions } from "@/utils/permissions";
import { useDeactivateEquipment, useEquipments } from "../api";
import type { EquipmentFilters } from "../types";

export function EquipmentList() {
  const { session } = useAuth();
  const navigate = useNavigate();
  const canManage = hasPermission(session, Permissions.EQUIPMENT_MANAGE);

  const [filters, setFilters] = useState<EquipmentFilters>({ page: 1, page_size: 20 });
  const [searchInput, setSearchInput] = useState("");
  const [confirmDeactivate, setConfirmDeactivate] = useState<string | null>(null);

  const { data, isLoading, error } = useEquipments(filters);
  const { data: sectorsData } = useSectors({ is_active: true, page_size: 100 });
  const deactivate = useDeactivateEquipment();

  function applySearch() {
    setFilters((f) => ({ ...f, page: 1, search: searchInput || undefined }));
  }

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
      <div className="p-6 text-red-600">Erro ao carregar equipamentos. Tente novamente.</div>
    );
  }

  const totalPages = Math.ceil((data?.total ?? 0) / (filters.page_size ?? 20));
  const sectors = sectorsData?.items ?? [];

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Equipamentos</h1>
        {canManage && (
          <button
            onClick={() => void navigate("/equipments/new")}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Novo equipamento
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 pb-2">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Buscar por nome ou código..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && applySearch()}
            className="border rounded px-3 py-1.5 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={applySearch}
            className="px-3 py-1.5 bg-gray-100 rounded text-sm hover:bg-gray-200 transition"
          >
            Buscar
          </button>
        </div>

        <select
          value={filters.sector_id ?? ""}
          onChange={(e) =>
            setFilters((f) => ({ ...f, page: 1, sector_id: e.target.value || undefined }))
          }
          className="border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos os setores</option>
          {sectors.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>

        <select
          value={filters.is_active === undefined ? "" : String(filters.is_active)}
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              page: 1,
              is_active: e.target.value === "" ? undefined : e.target.value === "true",
            }))
          }
          className="border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos os status</option>
          <option value="true">Ativo</option>
          <option value="false">Inativo</option>
        </select>
      </div>

      {!data || data.items.length === 0 ? (
        <div className="text-center text-gray-500 py-10">
          Nenhum equipamento encontrado.
          {canManage && (
            <button
              onClick={() => void navigate("/equipments/new")}
              className="ml-2 text-blue-600 underline"
            >
              Cadastrar equipamento
            </button>
          )}
        </div>
      ) : (
        <div className="overflow-x-auto rounded border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Código</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Nome</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Setor</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Fabricante</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                {canManage && (
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Ações</th>
                )}
              </tr>
            </thead>
            <tbody>
              {data.items.map((eq) => {
                const sectorName =
                  sectors.find((s) => s.id === eq.sector_id)?.name ?? eq.sector_id;
                return (
                  <tr key={eq.id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs">{eq.code}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => void navigate(`/equipments/${eq.id}`)}
                        className="text-blue-600 hover:underline text-left"
                      >
                        {eq.name}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{sectorName}</td>
                    <td className="px-4 py-3 text-gray-600">{eq.manufacturer ?? "—"}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          eq.is_active
                            ? "bg-green-100 text-green-700"
                            : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {eq.is_active ? "Ativo" : "Inativo"}
                      </span>
                    </td>
                    {canManage && (
                      <td className="px-4 py-3 space-x-2">
                        <button
                          onClick={() => void navigate(`/equipments/${eq.id}/edit`)}
                          className="text-sm text-blue-600 hover:underline"
                        >
                          Editar
                        </button>
                        {eq.is_active && (
                          <button
                            onClick={() => setConfirmDeactivate(eq.id)}
                            className="text-sm text-red-600 hover:underline"
                          >
                            Desativar
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center gap-2 pt-2">
          <button
            disabled={!filters.page || filters.page <= 1}
            onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
            className="px-3 py-1.5 border rounded text-sm disabled:opacity-40 hover:bg-gray-50 transition"
          >
            Anterior
          </button>
          <span className="text-sm text-gray-600">
            Página {filters.page} de {totalPages}
          </span>
          <button
            disabled={(filters.page ?? 1) >= totalPages}
            onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
            className="px-3 py-1.5 border rounded text-sm disabled:opacity-40 hover:bg-gray-50 transition"
          >
            Próxima
          </button>
        </div>
      )}

      {/* Deactivation confirmation */}
      {confirmDeactivate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 shadow-xl w-96">
            <h2 className="text-lg font-semibold mb-2">Desativar equipamento?</h2>
            <p className="text-sm text-gray-600 mb-4">
              O equipamento não poderá ser alvo de novos chamados industriais enquanto
              estiver inativo.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setConfirmDeactivate(null)}
                className="px-4 py-2 border rounded text-sm hover:bg-gray-50 transition"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  deactivate.mutate(confirmDeactivate);
                  setConfirmDeactivate(null);
                }}
                disabled={deactivate.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:opacity-50 transition"
              >
                Desativar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
