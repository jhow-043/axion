import { formatDistanceToNow } from "@/utils/dates";
import type { SlaAttendance, SlaResolution, SlaStatus } from "../types";
import { useTicketSla } from "../api";

const STATUS_LABEL: Record<SlaStatus, string> = {
  running: "Em andamento",
  paused: "Pausado",
  met: "Cumprido",
  breached: "Vencido",
};

const STATUS_CLASS: Record<SlaStatus, string> = {
  running: "bg-blue-100 text-blue-800",
  paused: "bg-yellow-100 text-yellow-800",
  met: "bg-green-100 text-green-800",
  breached: "bg-red-100 text-red-800",
};

function SlaBadge({ status }: { status: SlaStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_CLASS[status]}`}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}

function SlaProgressBar({ pct, status }: { pct: number; status: SlaStatus }) {
  const barClass =
    status === "breached"
      ? "bg-red-500"
      : status === "met"
        ? "bg-green-500"
        : pct >= 80
          ? "bg-orange-400"
          : "bg-blue-500";

  return (
    <div className="mt-1 h-1.5 w-full rounded-full bg-gray-200">
      <div
        className={`h-1.5 rounded-full ${barClass}`}
        style={{ width: `${Math.min(100, pct)}%` }}
      />
    </div>
  );
}

function AttendanceSla({ att }: { att: SlaAttendance }) {
  const dueAt = att.due_at ? new Date(att.due_at) : null;

  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-gray-700">Atendimento</span>
        <SlaBadge status={att.status} />
      </div>
      {dueAt && att.status !== "met" && att.status !== "breached" && (
        <p className="mt-0.5 text-xs text-gray-500">
          Prazo: {formatDistanceToNow(dueAt)}
        </p>
      )}
    </div>
  );
}

function ResolutionSla({ res }: { res: SlaResolution }) {
  const dueAt = res.due_at ? new Date(res.due_at) : null;
  const totalMinutes =
    res.elapsed_minutes != null && res.remaining_minutes != null
      ? res.elapsed_minutes + res.remaining_minutes
      : null;
  const pct =
    totalMinutes && totalMinutes > 0
      ? (res.elapsed_minutes! / totalMinutes) * 100
      : 0;

  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-gray-700">Resolução</span>
        <SlaBadge status={res.status} />
      </div>
      {res.status === "running" && dueAt && (
        <>
          <SlaProgressBar pct={pct} status={res.status} />
          <p className="mt-0.5 text-xs text-gray-500">
            {res.remaining_minutes != null
              ? `${res.remaining_minutes} min restantes`
              : formatDistanceToNow(dueAt)}
          </p>
        </>
      )}
      {res.status === "paused" && (
        <p className="mt-0.5 text-xs text-yellow-700">
          Pausado · {res.paused_minutes} min acumulados
        </p>
      )}
    </div>
  );
}

interface SlaIndicatorProps {
  ticketId: string;
}

export function SlaIndicator({ ticketId }: SlaIndicatorProps) {
  const { data, isLoading, isError } = useTicketSla(ticketId);

  if (isLoading) {
    return <div className="h-16 animate-pulse rounded-lg bg-gray-100" />;
  }

  if (isError || !data) {
    return null;
  }

  return (
    <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-3">
      <AttendanceSla att={data.attendance} />
      {data.resolution.due_at !== null || data.resolution.status !== "running" ? (
        <ResolutionSla res={data.resolution} />
      ) : null}
    </div>
  );
}
