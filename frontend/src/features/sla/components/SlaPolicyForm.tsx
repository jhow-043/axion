import { useEffect, useState } from "react";

import { usePriorities } from "@/features/catalog/api";
import { useTeams } from "@/features/teams/api";
import { useCreateSlaPolicy, useUpdateSlaPolicy } from "../api";
import type { SlaPolicy, SlaPolicyCreate } from "../types";

interface SlaPolicyFormProps {
  existing?: SlaPolicy;
  onSuccess: () => void;
  onCancel: () => void;
}

const TICKET_TYPE_LABELS = {
  industrial: "Industrial",
  predial: "Predial",
  all: "Todos os tipos",
};

export function SlaPolicyForm({ existing, onSuccess, onCancel }: SlaPolicyFormProps) {
  const isEditing = Boolean(existing);
  const createPolicy = useCreateSlaPolicy();
  const updatePolicy = useUpdateSlaPolicy(existing?.id ?? "");

  const { data: prioritiesData } = usePriorities();
  const { data: teamsData } = useTeams({ is_active: true, page_size: 100 });

  const [ticketType, setTicketType] = useState<"industrial" | "predial" | "all">("all");
  const [priorityId, setPriorityId] = useState("");
  const [teamId, setTeamId] = useState("");
  const [attendanceMinutes, setAttendanceMinutes] = useState("");
  const [resolutionMinutes, setResolutionMinutes] = useState("");
  const [alertThreshold, setAlertThreshold] = useState("80");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (existing) {
      setTicketType(existing.ticket_type as "industrial" | "predial" | "all");
      setPriorityId(existing.priority_id);
      setTeamId(existing.team_id ?? "");
      setAttendanceMinutes(String(existing.attendance_minutes));
      setResolutionMinutes(String(existing.resolution_minutes));
      setAlertThreshold(String(existing.alert_threshold_pct));
    }
  }, [existing]);

  const priorities = prioritiesData?.items ?? [];
  const teams = teamsData?.items ?? [];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      if (isEditing) {
        await updatePolicy.mutateAsync({
          attendance_minutes: Number(attendanceMinutes),
          resolution_minutes: Number(resolutionMinutes),
          alert_threshold_pct: Number(alertThreshold),
        });
      } else {
        const payload: SlaPolicyCreate = {
          ticket_type: ticketType,
          priority_id: priorityId,
          team_id: teamId || undefined,
          attendance_minutes: Number(attendanceMinutes),
          resolution_minutes: Number(resolutionMinutes),
          alert_threshold_pct: Number(alertThreshold),
        };
        await createPolicy.mutateAsync(payload);
      }
      onSuccess();
    } catch {
      setError("Erro ao salvar política. Verifique os dados e tente novamente.");
    }
  }

  const isPending = createPolicy.isPending || updatePolicy.isPending;

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
      {!isEditing && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Tipo de chamado *</label>
              <select
                required
                value={ticketType}
                onChange={(e) =>
                  setTicketType(e.target.value as "industrial" | "predial" | "all")
                }
                className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {Object.entries(TICKET_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Prioridade *</label>
              <select
                required
                value={priorityId}
                onChange={(e) => setPriorityId(e.target.value)}
                className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Selecione a prioridade...</option>
                {priorities.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Equipe (opcional)</label>
            <select
              value={teamId}
              onChange={(e) => setTeamId(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Aplicar a todas as equipes</option>
              {teams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
        </>
      )}

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Atendimento (min) *</label>
          <input
            type="number"
            required
            min={1}
            value={attendanceMinutes}
            onChange={(e) => setAttendanceMinutes(e.target.value)}
            placeholder="Ex.: 60"
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Resolução (min) *</label>
          <input
            type="number"
            required
            min={1}
            value={resolutionMinutes}
            onChange={(e) => setResolutionMinutes(e.target.value)}
            placeholder="Ex.: 480"
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Alerta (%)</label>
          <input
            type="number"
            min={1}
            max={100}
            value={alertThreshold}
            onChange={(e) => setAlertThreshold(e.target.value)}
            placeholder="80"
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border rounded text-sm hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {isPending
            ? "Salvando…"
            : isEditing
              ? "Salvar alterações"
              : "Criar política"}
        </button>
      </div>
    </form>
  );
}
