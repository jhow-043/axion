import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/shared/api/client";

export interface Priority {
  id: string;
  name: string;
  code: string;
  color: string | null;
  order: number;
  is_default: boolean;
  is_active: boolean;
}

export interface Status {
  id: string;
  name: string;
  code: string;
  order: number;
  requires_reason: boolean;
  requires_solution: boolean;
  is_terminal: boolean;
  is_default: boolean;
  is_active: boolean;
}

export interface Category {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
}

export interface PendingReason {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
}

const catalogKeys = {
  priorities: (activeOnly: boolean) => ["catalog", "priorities", activeOnly] as const,
  statuses: (activeOnly: boolean) => ["catalog", "statuses", activeOnly] as const,
  categories: (activeOnly: boolean) => ["catalog", "categories", activeOnly] as const,
  pendingReasons: (activeOnly: boolean) => ["catalog", "pending-reasons", activeOnly] as const,
};

export function usePriorities(activeOnly = true) {
  return useQuery<{ items: Priority[]; total: number }>({
    queryKey: catalogKeys.priorities(activeOnly),
    queryFn: () =>
      apiClient
        .get("/catalog/priorities", {
          params: activeOnly ? { is_active: true, page_size: 100 } : { page_size: 100 },
        })
        .then((r) => r.data),
  });
}

export function useStatuses(activeOnly = true) {
  return useQuery<{ items: Status[]; total: number }>({
    queryKey: catalogKeys.statuses(activeOnly),
    queryFn: () =>
      apiClient
        .get("/catalog/statuses", {
          params: activeOnly ? { is_active: true, page_size: 100 } : { page_size: 100 },
        })
        .then((r) => r.data),
  });
}

export function useCategories(activeOnly = true) {
  return useQuery<{ items: Category[]; total: number }>({
    queryKey: catalogKeys.categories(activeOnly),
    queryFn: () =>
      apiClient
        .get("/catalog/categories", {
          params: activeOnly ? { is_active: true, page_size: 100 } : { page_size: 100 },
        })
        .then((r) => r.data),
  });
}

export function usePendingReasons(activeOnly = true) {
  return useQuery<{ items: PendingReason[]; total: number }>({
    queryKey: catalogKeys.pendingReasons(activeOnly),
    queryFn: () =>
      apiClient
        .get("/catalog/pending-reasons", {
          params: activeOnly ? { is_active: true, page_size: 100 } : { page_size: 100 },
        })
        .then((r) => r.data),
  });
}

export function useCreateCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string; description?: string | null }) =>
      apiClient.post<Category>("/catalog/categories", payload).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalog", "categories"] }),
  });
}

export function useUpdateCategory(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name?: string; description?: string | null }) =>
      apiClient.patch<Category>(`/catalog/categories/${id}`, payload).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalog", "categories"] }),
  });
}

export function useDeactivateCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.post<Category>(`/catalog/categories/${id}/deactivate`).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalog", "categories"] }),
  });
}

export function useCreatePriority() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      name: string;
      code: string;
      color?: string | null;
      order: number;
    }) => apiClient.post<Priority>("/catalog/priorities", payload).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalog", "priorities"] }),
  });
}

export function useUpdatePriority(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name?: string; color?: string | null; order?: number }) =>
      apiClient.patch<Priority>(`/catalog/priorities/${id}`, payload).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalog", "priorities"] }),
  });
}

export function useDeactivatePriority() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.post<Priority>(`/catalog/priorities/${id}/deactivate`).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalog", "priorities"] }),
  });
}

export function useCreatePendingReason() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string; description?: string | null }) =>
      apiClient.post<PendingReason>("/catalog/pending-reasons", payload).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalog", "pending-reasons"] }),
  });
}

export function useUpdatePendingReason(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name?: string; description?: string | null }) =>
      apiClient
        .patch<PendingReason>(`/catalog/pending-reasons/${id}`, payload)
        .then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalog", "pending-reasons"] }),
  });
}

export function useDeactivatePendingReason() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient
        .post<PendingReason>(`/catalog/pending-reasons/${id}/deactivate`)
        .then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalog", "pending-reasons"] }),
  });
}

export function useUpdateStatus(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name?: string; order?: number }) =>
      apiClient.patch<Status>(`/catalog/statuses/${id}`, payload).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalog", "statuses"] }),
  });
}
