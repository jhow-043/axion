import { useParams } from "react-router";

import { AttachmentGallery } from "@/features/attachments/components/AttachmentGallery";
import { AttachmentUpload } from "@/features/attachments/components/AttachmentUpload";
import { TicketTimeline } from "@/features/timeline/components/TicketTimeline";
import { useAuth } from "@/shared/hooks/useAuth";
import { hasMinRole } from "@/utils/permissions";

export function TicketDetail() {
  const { id } = useParams<{ id: string }>();
  const { session } = useAuth();

  if (!id) return null;

  const isAdmin = hasMinRole(session?.roles ?? [], "admin");

  return (
    <div className="p-6 max-w-3xl space-y-8">
      <h1 className="text-2xl font-semibold">Chamado</h1>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Anexos</h2>
        <AttachmentUpload ticketId={id} />
        <AttachmentGallery
          ticketId={id}
          currentUserId={session?.id}
          isAdmin={isAdmin}
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Timeline</h2>
        <TicketTimeline ticketId={id} />
      </section>
    </div>
  );
}
