export interface AttachmentResponse {
  id: string;
  tenant_id: string;
  ticket_id: string;
  uploaded_by: string;
  filename: string;
  storage_key: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
}

export interface AttachmentListResponse {
  total: number;
  page: number;
  page_size: number;
  items: AttachmentResponse[];
}

export interface AttachmentUploadRequest {
  filename: string;
  mime_type: string;
  size_bytes: number;
}

export interface AttachmentUploadUrlResponse {
  upload_url: string;
  storage_key: string;
  expires_in: number;
}

export interface AttachmentConfirmRequest {
  storage_key: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
}

export interface AttachmentDownloadUrlResponse {
  download_url: string;
  expires_in: number;
}

export const ALLOWED_MIME_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "video/mp4",
  "video/quicktime",
] as const;

export const MAX_IMAGE_BYTES = 10 * 1024 * 1024;  // 10 MB
export const MAX_VIDEO_BYTES = 200 * 1024 * 1024; // 200 MB

export function isImageMime(mime: string): boolean {
  return mime.startsWith("image/");
}

export function isVideoMime(mime: string): boolean {
  return mime.startsWith("video/");
}
