import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/shared/api/client";

interface ActorSummary {
  id: string;
  name: string;
}

interface AuditLogResponse {
  id: string;
  actor: ActorSummary | null;
  action: string;
  entity_type: string;
  entity_id: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  created_at: string;
}

interface AuditLogListResponse {
  total: number;
  page: number;
  page_size: number;
  items: AuditLogResponse[];
}

function useAuditLogs(page: number, pageSize: number, filters: Record<string, string>) {
  return useQuery({
    queryKey: ["audit", "logs", page, pageSize, filters],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
      if (filters.entity_type) params.set("entity_type", filters.entity_type);
      if (filters.action) params.set("action", filters.action);
      const { data } = await apiClient.get<AuditLogListResponse>(`/audit?${params.toString()}`);
      return data;
    },
  });
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("pt-BR");
}

export function AuditSection() {
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [filters, setFilters] = useState<Record<string, string>>({});

  const { data, isLoading, error } = useAuditLogs(page, pageSize, filters);

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-xl font-semibold">Log de Auditoria</h2>

      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Tipo de entidade (ex: User)"
          className="border rounded px-3 py-1.5 text-sm"
          value={filters.entity_type ?? ""}
          onChange={(e) => {
            setFilters((f) => ({ ...f, entity_type: e.target.value }));
            setPage(1);
          }}
        />
        <input
          type="text"
          placeholder="Ação (ex: user.created)"
          className="border rounded px-3 py-1.5 text-sm"
          value={filters.action ?? ""}
          onChange={(e) => {
            setFilters((f) => ({ ...f, action: e.target.value }));
            setPage(1);
          }}
        />
      </div>

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      )}

      {error && <p className="text-red-600 text-sm">Erro ao carregar logs de auditoria.</p>}

      {data && (
        <>
          <div className="overflow-x-auto rounded border text-sm">
            <table className="w-full">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-4 py-3 font-medium">Data</th>
                  <th className="px-4 py-3 font-medium">Ator</th>
                  <th className="px-4 py-3 font-medium">Ação</th>
                  <th className="px-4 py-3 font-medium">Entidade</th>
                  <th className="px-4 py-3 font-medium">Alterações</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-gray-500">
                      Nenhum registro encontrado.
                    </td>
                  </tr>
                )}
                {data.items.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 text-gray-500 whitespace-nowrap">
                      {formatDate(log.created_at)}
                    </td>
                    <td className="px-4 py-2">
                      {log.actor?.name ?? <span className="text-gray-400">sistema</span>}
                    </td>
                    <td className="px-4 py-2">
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-mono">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-gray-600">
                      {log.entity_type}
                    </td>
                    <td className="px-4 py-2 max-w-xs">
                      {log.after && (
                        <details className="text-xs">
                          <summary className="cursor-pointer text-gray-500">Ver alterações</summary>
                          <pre className="mt-1 p-2 bg-gray-50 rounded overflow-x-auto text-xs">
                            {JSON.stringify(log.after, null, 2)}
                          </pre>
                        </details>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>
                {data.total} registros — página {page} de {totalPages}
              </span>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-3 py-1 border rounded disabled:opacity-40"
                >
                  Anterior
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1 border rounded disabled:opacity-40"
                >
                  Próxima
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
