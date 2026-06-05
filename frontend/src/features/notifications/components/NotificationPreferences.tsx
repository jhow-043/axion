import { useState, useEffect } from "react";
import { useNotificationPreferences, useUpdateNotificationPreferences } from "../api";
import type { NotificationPreference } from "../types";
import { Button } from "@/shared/components/ui/button";

const EVENT_LABELS: Record<string, string> = {
  ticket_created: "Novo chamado aberto",
  ticket_assigned: "Chamado atribuído",
  ticket_status_changed: "Mudança de status",
  ticket_comment_added: "Novo comentário",
  ticket_resolved: "Chamado solucionado",
  ticket_validation_requested: "Validação solicitada",
  ticket_validation_approved: "Solução aprovada",
  ticket_validation_rejected: "Solução rejeitada",
  ticket_closed: "Chamado encerrado",
  ticket_auto_closed: "Encerramento automático",
  sla_attendance_at_risk: "SLA atendimento em risco",
  sla_attendance_breached: "SLA atendimento vencido",
  sla_resolution_at_risk: "SLA resolução em risco",
  sla_resolution_breached: "SLA resolução vencido",
};

const ALL_EVENTS = Object.keys(EVENT_LABELS);

export function NotificationPreferences() {
  const { data, isLoading } = useNotificationPreferences();
  const update = useUpdateNotificationPreferences();

  const [prefs, setPrefs] = useState<Record<string, NotificationPreference>>({});

  useEffect(() => {
    if (!data) return;
    const map: Record<string, NotificationPreference> = {};
    for (const p of data.preferences) {
      map[p.event_type] = p;
    }
    setPrefs(map);
  }, [data]);

  function getPref(event: string): NotificationPreference {
    return (
      prefs[event] ?? {
        event_type: event,
        in_app_enabled: true,
        email_enabled: true,
      }
    );
  }

  function toggle(event: string, channel: "in_app_enabled" | "email_enabled") {
    const current = getPref(event);
    setPrefs((prev) => ({
      ...prev,
      [event]: { ...current, [channel]: !current[channel] },
    }));
  }

  async function handleSave() {
    const preferences = ALL_EVENTS.map(getPref);
    await update.mutateAsync({ preferences });
  }

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Carregando preferências…</p>;
  }

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-2 text-left font-medium">Evento</th>
              <th className="px-4 py-2 text-center font-medium">In-App</th>
              <th className="px-4 py-2 text-center font-medium">E-mail</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {ALL_EVENTS.map((event) => {
              const p = getPref(event);
              return (
                <tr key={event} className="hover:bg-muted/30">
                  <td className="px-4 py-2">{EVENT_LABELS[event]}</td>
                  <td className="px-4 py-2 text-center">
                    <input
                      type="checkbox"
                      checked={p.in_app_enabled}
                      onChange={() => toggle(event, "in_app_enabled")}
                      className="h-4 w-4 cursor-pointer rounded"
                      aria-label={`In-app para ${EVENT_LABELS[event]}`}
                    />
                  </td>
                  <td className="px-4 py-2 text-center">
                    <input
                      type="checkbox"
                      checked={p.email_enabled}
                      onChange={() => toggle(event, "email_enabled")}
                      className="h-4 w-4 cursor-pointer rounded"
                      aria-label={`E-mail para ${EVENT_LABELS[event]}`}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <Button onClick={() => void handleSave()} disabled={update.isPending}>
        {update.isPending ? "Salvando…" : "Salvar preferências"}
      </Button>
    </div>
  );
}
