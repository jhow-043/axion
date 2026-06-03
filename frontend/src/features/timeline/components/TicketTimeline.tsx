import { formatDateTime } from "@/utils/dates";
import { useTicketTimeline } from "../api";
import type { TicketEvent } from "../types";

const EVENT_LABELS: Record<string, string> = {
  ticket_created: "Chamado aberto",
  ticket_assigned: "Chamado assumido",
  status_changed: "Status alterado",
  comment_added: "Comentário adicionado",
  attachment_added: "Anexo adicionado",
  assignee_changed: "Responsável alterado",
  team_changed: "Equipe alterada",
  pending_started: "Pendência iniciada",
  solution_recorded: "Solução registrada",
  validation_requested: "Validação solicitada",
  validation_approved: "Validação aprovada",
  validation_rejected: "Validação rejeitada",
  ticket_closed: "Chamado encerrado",
  sla_attendance_breached: "SLA de atendimento violado",
  sla_resolution_breached: "SLA de resolução violado",
};

function eventLabel(type: string): string {
  return EVENT_LABELS[type] ?? type;
}

function EventItem({ event }: { event: TicketEvent }) {
  const actor = event.actor?.name ?? "Sistema";
  return (
    <li className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className="h-2.5 w-2.5 mt-1 rounded-full bg-primary flex-shrink-0" />
        <div className="flex-1 w-px bg-border mt-1" />
      </div>
      <div className="pb-4 min-w-0">
        <p className="text-sm font-medium text-foreground">{eventLabel(event.type)}</p>
        <p className="text-xs text-muted-foreground">
          {actor} · {formatDateTime(event.created_at)}
        </p>
        {event.payload && (
          <PayloadDetails type={event.type} payload={event.payload} />
        )}
      </div>
    </li>
  );
}

function PayloadDetails({
  type,
  payload,
}: {
  type: string;
  payload: Record<string, unknown>;
}) {
  if (type === "status_changed") {
    return (
      <p className="text-xs text-muted-foreground mt-0.5">
        {String(payload.from_status)} → {String(payload.to_status)}
      </p>
    );
  }
  if (type === "ticket_closed") {
    return (
      <p className="text-xs text-muted-foreground mt-0.5">
        Método: {payload.method === "auto" ? "automático" : "manual"}
      </p>
    );
  }
  return null;
}

interface TicketTimelineProps {
  ticketId: string;
}

export function TicketTimeline({ ticketId }: TicketTimelineProps) {
  const { data, isLoading, error, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useTicketTimeline(ticketId);

  if (isLoading) {
    return (
      <div className="space-y-3 animate-pulse">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-10 bg-muted rounded" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-sm text-destructive">
        Erro ao carregar a timeline. Tente novamente.
      </p>
    );
  }

  const allEvents = data?.pages.flatMap((p) => p.items) ?? [];

  if (allEvents.length === 0) {
    return <p className="text-sm text-muted-foreground">Nenhum evento registrado.</p>;
  }

  return (
    <div>
      <ul className="list-none p-0 m-0">
        {allEvents.map((event) => (
          <EventItem key={event.id} event={event} />
        ))}
      </ul>
      {hasNextPage && (
        <button
          onClick={() => void fetchNextPage()}
          disabled={isFetchingNextPage}
          className="mt-2 text-xs text-primary hover:underline disabled:opacity-50"
        >
          {isFetchingNextPage ? "Carregando..." : "Carregar mais"}
        </button>
      )}
    </div>
  );
}
