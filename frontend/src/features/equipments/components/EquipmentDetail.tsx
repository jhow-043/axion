import { useState } from "react";
import { useNavigate, useParams } from "react-router";

import { useSector } from "@/features/locations/api";
import { useAuth } from "@/shared/hooks/useAuth";
import { formatDate, formatDateTime } from "@/utils/dates";
import { hasPermission, Permissions } from "@/utils/permissions";
import {
  useActivateEquipment,
  useDeactivateEquipment,
  useEquipment,
  useEquipmentTickets,
} from "../api";

export function EquipmentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { session } = useAuth();
  const canManage = hasPermission(session, Permissions.EQUIPMENT_MANAGE);

  const [ticketsPage, setTicketsPage] = useState(1);
  const [confirmAction, setConfirmAction] = useState<"deactivate" | "activate" | null>(null);

  const { data: equipment, isLoading, error } = useEquipment(id ?? "");
  const { data: sector } = useSector(equipment?.sector_id ?? "");
  const { data: tickets } = useEquipmentTickets(id ?? "", ticketsPage);
  const deactivate = useDeactivateEquipment();
  const activate = useActivateEquipment();

  if (isLoading) {
    return (
      <div className="p-6 space-y-3">
        <div className="h-8 w-64 bg-gray-100 rounded animate-pulse" />
        <div className="h-4 w-48 bg-gray-100 rounded animate-pulse" />
      </div>
    );
  }

  if (error || !equipment) {
    return <div className="p-6 text-red-600">Equipamento não encontrado.</div>;
  }

  const totalTicketPages = Math.ceil((tickets?.total ?? 0) / 20);

  return (
    <div className="p-6 max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold">{equipment.name}</h1>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                equipment.is_active
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-600"
              }`}
            >
              {equipment.is_active ? "Ativo" : "Inativo"}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1 font-mono">{equipment.code}</p>
        </div>
        {canManage && (
          <div className="flex gap-2">
            <button
              onClick={() => void navigate(`/equipments/${equipment.id}/edit`)}
              className="px-3 py-1.5 border rounded text-sm hover:bg-gray-50 transition"
            >
              Editar
            </button>
            {equipment.is_active ? (
              <button
                onClick={() => setConfirmAction("deactivate")}
                className="px-3 py-1.5 bg-red-50 border border-red-200 text-red-600 rounded text-sm hover:bg-red-100 transition"
              >
                Desativar
              </button>
            ) : (
              <button
                onClick={() => setConfirmAction("activate")}
                className="px-3 py-1.5 bg-green-50 border border-green-200 text-green-600 rounded text-sm hover:bg-green-100 transition"
              >
                Reativar
              </button>
            )}
          </div>
        )}
      </div>

      {/* Details */}
      <div className="grid grid-cols-2 gap-4 bg-gray-50 rounded-lg p-4">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Setor</p>
          <p className="mt-1 text-sm">{sector?.name ?? equipment.sector_id}</p>
        </div>
        {equipment.manufacturer && (
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Fabricante
            </p>
            <p className="mt-1 text-sm">{equipment.manufacturer}</p>
          </div>
        )}
        {equipment.model && (
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Modelo</p>
            <p className="mt-1 text-sm">{equipment.model}</p>
          </div>
        )}
        {equipment.serial_number && (
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Número de série
            </p>
            <p className="mt-1 text-sm font-mono">{equipment.serial_number}</p>
          </div>
        )}
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Cadastrado</p>
          <p className="mt-1 text-sm">{formatDate(equipment.created_at)}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Última atualização
          </p>
          <p className="mt-1 text-sm">{formatDateTime(equipment.updated_at)}</p>
        </div>
      </div>

      {equipment.notes && (
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
            Observações
          </p>
          <p className="text-sm text-gray-700 bg-gray-50 rounded p-3">{equipment.notes}</p>
        </div>
      )}

      {/* Ticket history */}
      <div>
        <h2 className="text-lg font-semibold mb-3">
          Histórico de chamados
          {tickets && (
            <span className="ml-2 text-sm font-normal text-gray-500">
              ({tickets.total} no total)
            </span>
          )}
        </h2>

        {!tickets || tickets.items.length === 0 ? (
          <p className="text-sm text-gray-500 py-4">Nenhum chamado vinculado a este equipamento.</p>
        ) : (
          <>
            <div className="overflow-x-auto rounded border">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Título</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Prioridade</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Abertura</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Responsável</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.items.map((t) => (
                    <tr key={t.id} className="border-b last:border-0 hover:bg-gray-50">
                      <td className="px-4 py-3">{t.title}</td>
                      <td className="px-4 py-3 capitalize">{t.status_code}</td>
                      <td className="px-4 py-3 capitalize">{t.priority_code}</td>
                      <td className="px-4 py-3">{formatDate(t.created_at)}</td>
                      <td className="px-4 py-3 text-gray-600">{t.assignee_name ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalTicketPages > 1 && (
              <div className="flex items-center gap-2 pt-2">
                <button
                  disabled={ticketsPage <= 1}
                  onClick={() => setTicketsPage((p) => p - 1)}
                  className="px-3 py-1.5 border rounded text-sm disabled:opacity-40 hover:bg-gray-50 transition"
                >
                  Anterior
                </button>
                <span className="text-sm text-gray-600">
                  Página {ticketsPage} de {totalTicketPages}
                </span>
                <button
                  disabled={ticketsPage >= totalTicketPages}
                  onClick={() => setTicketsPage((p) => p + 1)}
                  className="px-3 py-1.5 border rounded text-sm disabled:opacity-40 hover:bg-gray-50 transition"
                >
                  Próxima
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Confirmation modal */}
      {confirmAction && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 shadow-xl w-96">
            <h2 className="text-lg font-semibold mb-2">
              {confirmAction === "deactivate" ? "Desativar equipamento?" : "Reativar equipamento?"}
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              {confirmAction === "deactivate"
                ? "O equipamento não poderá ser alvo de novos chamados industriais enquanto estiver inativo."
                : "O equipamento voltará a estar disponível para novos chamados."}
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setConfirmAction(null)}
                className="px-4 py-2 border rounded text-sm hover:bg-gray-50 transition"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  if (confirmAction === "deactivate") {
                    deactivate.mutate(equipment.id);
                  } else {
                    activate.mutate(equipment.id);
                  }
                  setConfirmAction(null);
                }}
                disabled={deactivate.isPending || activate.isPending}
                className={`px-4 py-2 text-white rounded text-sm disabled:opacity-50 transition ${
                  confirmAction === "deactivate"
                    ? "bg-red-600 hover:bg-red-700"
                    : "bg-green-600 hover:bg-green-700"
                }`}
              >
                {confirmAction === "deactivate" ? "Desativar" : "Reativar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
