import { useRef, useState } from "react";

import {
  ALLOWED_MIME_TYPES,
  isImageMime,
  isVideoMime,
  MAX_IMAGE_BYTES,
  MAX_VIDEO_BYTES,
} from "../types";
import { useUploadAttachment } from "../api";

interface AttachmentUploadProps {
  ticketId: string;
}

function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024).toFixed(0)} KB`;
}

function validateFile(file: File): string | null {
  const allowed = ALLOWED_MIME_TYPES as readonly string[];
  if (!allowed.includes(file.type)) {
    return `Tipo de arquivo não permitido. Use imagens (JPEG, PNG, WebP) ou vídeos (MP4, MOV).`;
  }
  if (isImageMime(file.type) && file.size > MAX_IMAGE_BYTES) {
    return `Imagem muito grande (máximo ${formatBytes(MAX_IMAGE_BYTES)}).`;
  }
  if (isVideoMime(file.type) && file.size > MAX_VIDEO_BYTES) {
    return `Vídeo muito grande (máximo ${formatBytes(MAX_VIDEO_BYTES)}).`;
  }
  return null;
}

export function AttachmentUpload({ ticketId }: AttachmentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const upload = useUploadAttachment(ticketId);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setError(null);

    for (const file of Array.from(files)) {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
    }

    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        await upload.mutateAsync(file);
      }
    } catch {
      setError("Falha no upload. Verifique sua conexão e tente novamente.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="space-y-2">
      <div
        role="button"
        tabIndex={0}
        aria-label="Área de upload de arquivos"
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${dragOver ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}
          ${uploading ? "opacity-50 pointer-events-none" : ""}`}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          void handleFiles(e.dataTransfer.files);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          multiple
          accept={ALLOWED_MIME_TYPES.join(",")}
          onChange={(e) => void handleFiles(e.target.files)}
        />
        {uploading ? (
          <div className="space-y-2">
            <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-primary animate-pulse w-1/2 rounded-full" />
            </div>
            <p className="text-sm text-muted-foreground">Enviando...</p>
          </div>
        ) : (
          <>
            <p className="text-sm font-medium">
              Arraste arquivos aqui ou{" "}
              <span className="text-primary underline">clique para selecionar</span>
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Imagens (JPEG, PNG, WebP) até 10 MB · Vídeos (MP4, MOV) até 200 MB
            </p>
          </>
        )}
      </div>

      {error && (
        <p className="text-xs text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
