import { useState } from "react";

import { useAttachmentDownloadUrl, useDeleteAttachment, useTicketAttachments } from "../api";
import { isImageMime, isVideoMime, type AttachmentResponse } from "../types";

interface AttachmentGalleryProps {
  ticketId: string;
  currentUserId?: string;
  isAdmin?: boolean;
}

function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024).toFixed(0)} KB`;
}

function DownloadLink({ attachment }: { attachment: AttachmentResponse }) {
  const [fetch, setFetch] = useState(false);
  const { data, isLoading } = useAttachmentDownloadUrl(attachment.id, fetch);

  if (data?.download_url) {
    return (
      <a
        href={data.download_url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs text-primary hover:underline"
      >
        Baixar
      </a>
    );
  }

  return (
    <button
      className="text-xs text-primary hover:underline disabled:opacity-50"
      disabled={isLoading}
      onClick={() => setFetch(true)}
    >
      {isLoading ? "..." : "Baixar"}
    </button>
  );
}

function AttachmentItem({
  attachment,
  canDelete,
  onDelete,
}: {
  attachment: AttachmentResponse;
  canDelete: boolean;
  onDelete: (id: string) => void;
}) {
  const isImage = isImageMime(attachment.mime_type);
  const isVideo = isVideoMime(attachment.mime_type);

  return (
    <div className="flex items-start gap-3 p-3 border rounded-lg bg-card">
      {/* Thumbnail placeholder for images */}
      <div className="w-12 h-12 flex-shrink-0 rounded bg-muted flex items-center justify-center text-lg">
        {isImage ? "🖼" : isVideo ? "🎬" : "📎"}
      </div>

      <div className="flex-1 min-w-0">
        <p
          className="text-sm font-medium truncate"
          title={attachment.filename}
        >
          {attachment.filename}
        </p>
        <p className="text-xs text-muted-foreground">
          {attachment.mime_type} · {formatBytes(attachment.size_bytes)}
        </p>
        <div className="mt-1">
          <DownloadLink attachment={attachment} />
        </div>
      </div>

      {canDelete && (
        <button
          className="text-xs text-destructive hover:underline flex-shrink-0"
          onClick={() => onDelete(attachment.id)}
          aria-label={`Excluir ${attachment.filename}`}
        >
          Excluir
        </button>
      )}
    </div>
  );
}

export function AttachmentGallery({
  ticketId,
  currentUserId,
  isAdmin = false,
}: AttachmentGalleryProps) {
  const { data, isLoading, error } = useTicketAttachments(ticketId);
  const deleteAttachment = useDeleteAttachment(ticketId);

  if (isLoading) {
    return (
      <div className="space-y-2 animate-pulse">
        {[...Array(2)].map((_, i) => (
          <div key={i} className="h-16 bg-muted rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-sm text-destructive">
        Erro ao carregar anexos. Tente novamente.
      </p>
    );
  }

  const items = data?.items ?? [];

  if (items.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Nenhum anexo adicionado ainda.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((attachment) => {
        const canDelete = isAdmin || attachment.uploaded_by === currentUserId;
        return (
          <AttachmentItem
            key={attachment.id}
            attachment={attachment}
            canDelete={canDelete}
            onDelete={(id) => void deleteAttachment.mutateAsync(id)}
          />
        );
      })}
    </div>
  );
}
