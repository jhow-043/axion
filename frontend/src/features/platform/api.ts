import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/shared/api/client";
import type {
  GlobalDashboardResponse,
  TenantCreate,
  TenantListResponse,
  TenantResponse,
  TenantUpdate,
} from "./types";

const platformKeys = {
  all: ["platform"] as const,
  dashboard: (page: number, pageSize: number) =>
    [...platformKeys.all, "dashboard", page, pageSize] as const,
  tenants: ["platform", "tenants"] as const,
  tenantList: (page: number, pageSize: number) =>
    [...platformKeys.tenants, "list", page, pageSize] as const,
  tenantDetail: (id: string) => [...platformKeys.tenants, "detail", id] as const,
};

export function useGlobalDashboard(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: platformKeys.dashboard(page, pageSize),
    queryFn: async () => {
      const { data } = await apiClient.get<GlobalDashboardResponse>(
        `/admin/tenants/dashboard?page=${page}&page_size=${pageSize}`,
      );
      return data;
    },
  });
}

export function usePlatformTenants(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: platformKeys.tenantList(page, pageSize),
    queryFn: async () => {
      const { data } = await apiClient.get<TenantListResponse>(
        `/admin/tenants?page=${page}&page_size=${pageSize}`,
      );
      return data;
    },
  });
}

export function usePlatformTenant(id: string) {
  return useQuery({
    queryKey: platformKeys.tenantDetail(id),
    queryFn: async () => {
      const { data } = await apiClient.get<TenantResponse>(`/admin/tenants/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useProvisionCompany() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TenantCreate) => {
      const { data } = await apiClient.post<TenantResponse>("/admin/tenants", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: platformKeys.all });
    },
  });
}

export function useUpdateCompany(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TenantUpdate) => {
      const { data } = await apiClient.patch<TenantResponse>(`/admin/tenants/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: platformKeys.all });
    },
  });
}

export function useActivateCompany() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<TenantResponse>(`/admin/tenants/${id}/activate`);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: platformKeys.all });
    },
  });
}

export function useSuspendCompany() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<TenantResponse>(
        `/admin/tenants/${id}/deactivate`,
      );
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: platformKeys.all });
    },
  });
}

export function useDeleteCompany() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/admin/tenants/${id}`);
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: platformKeys.all });
    },
  });
}
