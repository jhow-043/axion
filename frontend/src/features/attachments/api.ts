import axios from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/shared/api/client";
import type {
  AttachmentConfirmRequest,
  AttachmentDownloadUrlResponse,
  AttachmentListResponse,
  AttachmentResponse,
  AttachmentUploadRequest,
  AttachmentUploadUrlResponse,
} from "./types";

const attachmentKeys = {
  all: ["attachments"] as const,
  ticket: (ticketId: string) => [...attachmentKeys.all, "ticket", ticketId] as const,
  downloadUrl: (id: string) => [...attachmentKeys.all, "download", id] as const,
};

export function useTicketAttachments(ticketId: string) {
  return useQuery({
    queryKey: attachmentKeys.ticket(ticketId),
    queryFn: async () => {
      const { data } = await apiClient.get<AttachmentListResponse>(
        `/tickets/${ticketId}/attachments`,
      );
      return data;
    },
    enabled: Boolean(ticketId),
  });
}

export function useAttachmentDownloadUrl(attachmentId: string, enabled = false) {
  return useQuery({
    queryKey: attachmentKeys.downloadUrl(attachmentId),
    queryFn: async () => {
      const { data } = await apiClient.get<AttachmentDownloadUrlResponse>(
        `/attachments/${attachmentId}/download-url`,
      );
      return data;
    },
    enabled,
    staleTime: 55 * 60 * 1000, // slightly under the 60-min expiry
  });
}

export function useUploadAttachment(ticketId: string) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (file: File): Promise<AttachmentResponse> => {
      // Step 1: request presigned upload URL from backend
      const uploadReq: AttachmentUploadRequest = {
        filename: file.name,
        mime_type: file.type,
        size_bytes: file.size,
      };
      const { data: urlData } = await apiClient.post<AttachmentUploadUrlResponse>(
        `/tickets/${ticketId}/attachments/upload-url`,
        uploadReq,
      );

      // Step 2: PUT file directly to MinIO (no auth header — presigned URL is self-contained)
      await axios.put(urlData.upload_url, file, {
        headers: { "Content-Type": file.type },
        onUploadProgress: () => {
          // progress events are exposed via onUploadProgress if needed
        },
      });

      // Step 3: confirm the upload with the backend
      const confirmReq: AttachmentConfirmRequest = {
        storage_key: urlData.storage_key,
        filename: file.name,
        mime_type: file.type,
        size_bytes: file.size,
      };
      const { data: attachment } = await apiClient.post<AttachmentResponse>(
        `/tickets/${ticketId}/attachments/confirm`,
        confirmReq,
      );
      return attachment;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: attachmentKeys.ticket(ticketId) });
    },
  });
}

export function useDeleteAttachment(ticketId: string) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (attachmentId: string) => {
      await apiClient.delete(`/attachments/${attachmentId}`);
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: attachmentKeys.ticket(ticketId) });
    },
  });
}
