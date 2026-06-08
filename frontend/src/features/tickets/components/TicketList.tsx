import { useMemo, useState } from "react";
import { useNavigate } from "react-router";

import { usePriorities, useStatuses } from "@/features/catalog/api";
import { useSectors } from "@/features/locations/api";
import { useAuth } from "@/shared/hooks/useAuth";
import { hasPermission, Permissions } from "@/utils/permissions";
import { useTickets } from "../api";
import type { TicketFilters } from "../types";

const TYPE_LABELS: Record<string, string> = {
  industrial: "Industrial",
  predial: "Predial",
};

const STATUS_COLORS: Record<string, string> = {
  new: "bg-blue-100 text-blue-700",
  in_progress: "bg-yellow-100 text-yellow-700",
  pending: "bg-orange-100 text-orange-700",
  resolved: "bg-green-100 text-green-700",
  closed: "bg-gray-100 text-gray-600",
};

export function TicketList() {
  const navigate = useNavigate();
  const { session } = useAuth();
  const canCreate = hasPermission(session, Permissions.TICKET_CREATE);
  const [filters, setFilters] = useState<TicketFilters>({ page: 1, page_size: 20 });

  const { data, isLoading, error } = useTickets(filters);
  const { data: prioritiesData } = usePriorities(false);
  const { data: statusesData } = useStatuses(false);
  const { data: sectorsData } = useSectors({ is_active: true, page_size: 100 });

  const priorityMap = useMemo(() => {
    const m: Record<string, { name: string; color: string | null }> = {};
    for (const p of prioritiesData?.items ?? []) m[p.id] = { name: p.name, color: p.color };
    return m;
  }, [prioritiesData]);

  const statusMap = useMemo(() => {
    const m: Record<string, { name: string; code: string }> = {};
    for (const s of statusesData?.items ?? []) m[s.id] = { name: s.name, code: s.code };
    return m;
  }, [statusesData]);

  const sectors = sectorsData?.items ?? [];

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
    return <div className="p-6 text-red-600">Erro ao carregar chamados. Tente novamente.</div>;
  }

  const totalPages = Math.ceil((data?.total ?? 0) / (filters.page_size ?? 20));

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Chamados</h1>
        {canCreate && (
          <button
            onClick={() => void navigate("/tickets/new")}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm"
          >
            Novo chamado
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Buscar por título..."
          className="border rounded px-3 py-1.5 text-sm w-64"
          value={filters.search ?? ""}
          onChange={(e) =>
            setFilters((f) => ({ ...f, search: e.target.value || undefined, page: 1 }))
          }
        />
        <select
          className="border rounded px-3 py-1.5 text-sm"
          value={filters.type ?? ""}
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              type: e.target.value || undefined,
              // Clear sector filter when switching to predial (sectors apply to industrial only)
              sector_id: e.target.value === "predial" ? undefined : f.sector_id,
              page: 1,
            }))
          }
        >
          <option value="">Todos os tipos</option>
          <option value="industrial">Industrial</option>
          <option value="predial">Predial</option>
        </select>
        <select
          className="border rounded px-3 py-1.5 text-sm"
          value={filters.status_code ?? ""}
          onChange={(e) =>
            setFilters((f) => ({ ...f, status_code: e.target.value || undefined, page: 1 }))
          }
        >
          <option value="">Todos os status</option>
          {statusesData?.items.map((s) => (
            <option key={s.id} value={s.code}>
              {s.name}
            </option>
          ))}
        </select>
        <select
          className="border rounded px-3 py-1.5 text-sm"
          value={filters.priority_id ?? ""}
          onChange={(e) =>
            setFilters((f) => ({ ...f, priority_id: e.target.value || undefined, page: 1 }))
          }
        >
          <option value="">Todas as prioridades</option>
          {prioritiesData?.items.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        {/* Sector filter — only meaningful for industrial tickets */}
        {(filters.type === "industrial" || !filters.type) && sectors.length > 0 && (
          <select
            className="border rounded px-3 py-1.5 text-sm"
            value={filters.sector_id ?? ""}
            onChange={(e) =>
              setFilters((f) => ({ ...f, sector_id: e.target.value || undefined, page: 1 }))
            }
          >
            <option value="">Todos os setores</option>
            {sectors.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {!data || data.items.length === 0 ? (
        <div className="text-center text-gray-500 py-8">Nenhum chamado encontrado.</div>
      ) : (
        <div className="overflow-x-auto rounded border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-4 py-3 font-medium">Título</th>
                <th className="px-4 py-3 font-medium">Tipo</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Prioridade</th>
                <th className="px-4 py-3 font-medium">Aberto em</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.items.map((ticket) => {
                const status = ticket.status_id ? statusMap[ticket.status_id] : null;
                const priority = ticket.priority_id ? priorityMap[ticket.priority_id] : null;
                return (
                  <tr
                    key={ticket.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => void navigate(`/tickets/${ticket.id}`)}
                  >
                    <td className="px-4 py-3 font-medium max-w-xs truncate">{ticket.title}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {TYPE_LABELS[ticket.type] ?? ticket.type}
                    </td>
                    <td className="px-4 py-3">
                      {status && (
                        <span
                          className={`px-2 py-0.5 text-xs font-medium rounded-full ${STATUS_COLORS[status.code] ?? "bg-gray-100 text-gray-600"}`}
                        >
                          {status.name}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {priority && (
                        <span
                          className="px-2 py-0.5 text-xs font-medium rounded-full"
                          style={
                            priority.color
                              ? {
                                  backgroundColor: `${priority.color}20`,
                                  color: priority.color,
                                }
                              : { backgroundColor: "#f3f4f6", color: "#374151" }
                          }
                        >
                          {priority.name}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {new Date(ticket.created_at).toLocaleDateString("pt-BR")}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            {data?.total} chamados — página {filters.page} de {totalPages}
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
