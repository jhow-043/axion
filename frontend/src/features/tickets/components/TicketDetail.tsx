import { useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router";

import { useStatuses, usePriorities, useCategories } from "@/features/catalog/api";
import { useEquipment } from "@/features/equipments/api";
import { useLocations, useSector } from "@/features/locations/api";
import { useTeam } from "@/features/teams/api";
import { useUser } from "@/features/users/api";
import { AttachmentGallery } from "@/features/attachments/components/AttachmentGallery";
import { AttachmentUpload } from "@/features/attachments/components/AttachmentUpload";
import { TicketTimeline } from "@/features/timeline/components/TicketTimeline";
import { useAuth } from "@/shared/hooks/useAuth";
import { hasMinRole } from "@/utils/permissions";
import { useTicket, useTicketComments, useAddTicketComment } from "../api";

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

export function TicketDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { session } = useAuth();

  const { data: ticket, isLoading, error } = useTicket(id ?? "");
  const { data: prioritiesData } = usePriorities(false);
  const { data: statusesData } = useStatuses(false);
  const { data: categoriesData } = useCategories(false);
  const { data: locationsData } = useLocations({ page_size: 100 });

  // Load related entities by ID (only when ticket is loaded)
  const { data: equipment } = useEquipment(ticket?.equipment_id ?? "");
  const { data: sector } = useSector(equipment?.sector_id ?? "");
  const { data: team } = useTeam(ticket?.team_id ?? "");
  const { data: requester } = useUser(ticket?.requester_id ?? "");
  const { data: assignee } = useUser(ticket?.assignee_id ?? "");

  // Comments
  const { data: commentsData } = useTicketComments(id ?? "");
  const addComment = useAddTicketComment(id ?? "");
  const [commentText, setCommentText] = useState("");

  const priorityMap = useMemo(() => {
    const m: Record<string, { name: string; color: string | null }> = {};
    for (const p of prioritiesData?.items ?? []) m[p.id] = { name: p.name, color: p.color };
    return m;
  }, [prioritiesData]);

  const statusMap = useMemo(() => {
    const m: Record<string, { name: string; code: string; is_terminal: boolean }> = {};
    for (const s of statusesData?.items ?? [])
      m[s.id] = { name: s.name, code: s.code, is_terminal: s.is_terminal };
    return m;
  }, [statusesData]);

  const categoryMap = useMemo(() => {
    const m: Record<string, string> = {};
    for (const c of categoriesData?.items ?? []) m[c.id] = c.name;
    return m;
  }, [categoriesData]);

  const locationMap = useMemo(() => {
    const m: Record<string, string> = {};
    for (const loc of locationsData?.items ?? []) m[loc.id] = loc.name;
    return m;
  }, [locationsData]);

  if (!id) return null;

  const isAdmin = hasMinRole(session?.roles ?? [], "admin");

  if (isLoading) {
    return (
      <div className="p-6 space-y-3">
        <div className="h-8 w-64 bg-gray-100 rounded animate-pulse" />
        <div className="h-4 w-full bg-gray-100 rounded animate-pulse" />
        <div className="h-4 w-3/4 bg-gray-100 rounded animate-pulse" />
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="p-6 space-y-4">
        <p className="text-red-600">Chamado não encontrado ou sem permissão de acesso.</p>
        <button
          onClick={() => void navigate("/tickets")}
          className="px-3 py-1.5 border rounded text-sm hover:bg-gray-50"
        >
          Voltar
        </button>
      </div>
    );
  }

  const priority = ticket.priority_id ? priorityMap[ticket.priority_id] : null;
  const status = ticket.status_id ? statusMap[ticket.status_id] : null;
  const categoryName = ticket.category_id ? categoryMap[ticket.category_id] : null;
  const locationName = ticket.location_id ? locationMap[ticket.location_id] : null;

  async function handleAddComment(e: React.FormEvent) {
    e.preventDefault();
    if (!commentText.trim()) return;
    await addComment.mutateAsync({ content: commentText });
    setCommentText("");
  }

  return (
    <div className="p-6 max-w-3xl space-y-8">
      <div className="flex items-start gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-gray-500 mb-1">
            {TYPE_LABELS[ticket.type] ?? ticket.type} · aberto em{" "}
            {new Date(ticket.created_at).toLocaleDateString("pt-BR")}
          </p>
          <h1 className="text-2xl font-semibold leading-tight">{ticket.title}</h1>
        </div>
        <div className="flex flex-col items-end gap-2 shrink-0">
          {status && (
            <span
              className={`px-2.5 py-1 text-xs font-medium rounded-full ${STATUS_COLORS[status.code] ?? "bg-gray-100 text-gray-600"}`}
            >
              {status.name}
            </span>
          )}
          {priority && (
            <span
              className="px-2 py-0.5 text-xs font-medium rounded-full"
              style={
                priority.color
                  ? { backgroundColor: `${priority.color}20`, color: priority.color }
                  : undefined
              }
            >
              {priority.name}
            </span>
          )}
        </div>
      </div>

      <div className="bg-gray-50 rounded p-4 text-sm text-gray-700 whitespace-pre-wrap">
        {ticket.description}
      </div>

      <dl className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
        {requester && (
          <>
            <dt className="text-gray-500">Solicitante</dt>
            <dd>{requester.name}</dd>
          </>
        )}
        {assignee ? (
          <>
            <dt className="text-gray-500">Responsável</dt>
            <dd>{assignee.name}</dd>
          </>
        ) : (
          <>
            <dt className="text-gray-500">Responsável</dt>
            <dd className="text-gray-400 italic">Não atribuído</dd>
          </>
        )}
        {team && (
          <>
            <dt className="text-gray-500">Equipe</dt>
            <dd>{team.name}</dd>
          </>
        )}
        {categoryName && (
          <>
            <dt className="text-gray-500">Categoria</dt>
            <dd>{categoryName}</dd>
          </>
        )}
        {/* Industrial: equipamento + setor */}
        {ticket.type === "industrial" && equipment && (
          <>
            <dt className="text-gray-500">Equipamento</dt>
            <dd>
              {equipment.code} — {equipment.name}
            </dd>
            <dt className="text-gray-500">Setor</dt>
            <dd>{sector?.name ?? "—"}</dd>
          </>
        )}
        {/* Predial: local */}
        {ticket.type === "predial" && locationName && (
          <>
            <dt className="text-gray-500">Local</dt>
            <dd>{locationName}</dd>
          </>
        )}
        {ticket.assigned_at && (
          <>
            <dt className="text-gray-500">Assumido em</dt>
            <dd>{new Date(ticket.assigned_at).toLocaleDateString("pt-BR")}</dd>
          </>
        )}
        {ticket.resolved_at && (
          <>
            <dt className="text-gray-500">Resolvido em</dt>
            <dd>{new Date(ticket.resolved_at).toLocaleDateString("pt-BR")}</dd>
          </>
        )}
        {ticket.closed_at && (
          <>
            <dt className="text-gray-500">Fechado em</dt>
            <dd>{new Date(ticket.closed_at).toLocaleDateString("pt-BR")}</dd>
          </>
        )}
      </dl>

      <section className="space-y-3">
        <h2 className="text-base font-medium">Comentários</h2>
        {commentsData && commentsData.items.length > 0 ? (
          <div className="space-y-2">
            {commentsData.items.map((c) => (
              <div key={c.id} className="bg-gray-50 rounded p-3 text-sm">
                <p className="text-gray-700 whitespace-pre-wrap">{c.content}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(c.created_at).toLocaleString("pt-BR")}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">Nenhum comentário ainda.</p>
        )}
        <form onSubmit={(e) => void handleAddComment(e)} className="flex gap-2">
          <input
            type="text"
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            placeholder="Adicionar comentário..."
            className="flex-1 border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={!commentText.trim() || addComment.isPending}
            className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-40 transition"
          >
            Enviar
          </button>
        </form>
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-medium">Anexos</h2>
        <AttachmentUpload ticketId={id} />
        <AttachmentGallery ticketId={id} currentUserId={session?.id} isAdmin={isAdmin} />
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-medium">Timeline</h2>
        <TicketTimeline ticketId={id} />
      </section>
    </div>
  );
}
