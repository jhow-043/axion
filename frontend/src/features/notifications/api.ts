import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/shared/api/client";
import type {
  NotificationListResponse,
  NotificationPreferencesPatch,
  NotificationPreferencesResponse,
  Notification,
} from "./types";

const notificationKeys = {
  all: ["notifications"] as const,
  list: (isRead?: boolean | null) =>
    [...notificationKeys.all, "list", isRead] as const,
  unreadCount: () => [...notificationKeys.all, "unread-count"] as const,
  preferences: () => [...notificationKeys.all, "preferences"] as const,
};

export function useNotifications(isRead?: boolean | null, page = 1) {
  return useQuery({
    queryKey: notificationKeys.list(isRead),
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: 20 };
      if (isRead !== undefined && isRead !== null) {
        params.is_read = isRead ? "true" : "false";
      }
      const { data } = await apiClient.get<NotificationListResponse>(
        "/notifications",
        { params },
      );
      return data;
    },
    staleTime: 30_000,
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<Notification>(
        `/notifications/${id}/read`,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post<{ marked_read: number }>(
        "/notifications/read-all",
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

export function useNotificationPreferences() {
  return useQuery({
    queryKey: notificationKeys.preferences(),
    queryFn: async () => {
      const { data } =
        await apiClient.get<NotificationPreferencesResponse>(
          "/notifications/preferences",
        );
      return data;
    },
    staleTime: 60_000,
  });
}

export function useUpdateNotificationPreferences() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: NotificationPreferencesPatch) => {
      const { data } =
        await apiClient.patch<NotificationPreferencesResponse>(
          "/notifications/preferences",
          body,
        );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: notificationKeys.preferences() });
    },
  });
}
