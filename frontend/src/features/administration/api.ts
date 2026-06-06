import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/shared/api/client";
import type {
  TenantCreate,
  TenantListResponse,
  TenantResponse,
  TenantUpdate,
} from "./types";

const tenantKeys = {
  all: ["admin", "tenants"] as const,
  list: (page: number, pageSize: number) =>
    [...tenantKeys.all, "list", page, pageSize] as const,
  detail: (id: string) => [...tenantKeys.all, "detail", id] as const,
};

export function useTenants(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: tenantKeys.list(page, pageSize),
    queryFn: async () => {
      const { data } = await apiClient.get<TenantListResponse>(
        `/admin/tenants?page=${page}&page_size=${pageSize}`,
      );
      return data;
    },
  });
}

export function useTenant(id: string) {
  return useQuery({
    queryKey: tenantKeys.detail(id),
    queryFn: async () => {
      const { data } = await apiClient.get<TenantResponse>(`/admin/tenants/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useProvisionTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TenantCreate) => {
      const { data } = await apiClient.post<TenantResponse>("/admin/tenants", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: tenantKeys.all });
    },
  });
}

export function useUpdateTenant(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TenantUpdate) => {
      const { data } = await apiClient.patch<TenantResponse>(`/admin/tenants/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: tenantKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: tenantKeys.all });
    },
  });
}

export function useActivateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<TenantResponse>(`/admin/tenants/${id}/activate`);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: tenantKeys.all });
    },
  });
}

export function useDeactivateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<TenantResponse>(`/admin/tenants/${id}/deactivate`);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: tenantKeys.all });
    },
  });
}
