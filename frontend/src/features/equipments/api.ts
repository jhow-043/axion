import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/shared/api/client";
import type {
  EquipmentCreate,
  EquipmentFilters,
  EquipmentListResponse,
  EquipmentResponse,
  EquipmentTicketsResponse,
  EquipmentUpdate,
} from "./types";

const equipmentKeys = {
  all: ["equipments"] as const,
  list: (filters: EquipmentFilters) => [...equipmentKeys.all, "list", filters] as const,
  detail: (id: string) => [...equipmentKeys.all, "detail", id] as const,
  tickets: (id: string, page: number) =>
    [...equipmentKeys.all, "tickets", id, page] as const,
};

export function useEquipments(filters: EquipmentFilters = {}) {
  return useQuery({
    queryKey: equipmentKeys.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.page) params.set("page", String(filters.page));
      if (filters.page_size) params.set("page_size", String(filters.page_size));
      if (filters.search) params.set("search", filters.search);
      if (filters.sector_id) params.set("sector_id", filters.sector_id);
      if (filters.is_active !== undefined)
        params.set("is_active", String(filters.is_active));
      const { data } = await apiClient.get<EquipmentListResponse>(
        `/equipments?${params.toString()}`
      );
      return data;
    },
  });
}

export function useEquipment(id: string) {
  return useQuery({
    queryKey: equipmentKeys.detail(id),
    queryFn: async () => {
      const { data } = await apiClient.get<EquipmentResponse>(`/equipments/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useEquipmentTickets(id: string, page = 1) {
  return useQuery({
    queryKey: equipmentKeys.tickets(id, page),
    queryFn: async () => {
      const { data } = await apiClient.get<EquipmentTicketsResponse>(
        `/equipments/${id}/tickets?page=${page}`
      );
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useCreateEquipment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: EquipmentCreate) => {
      const { data } = await apiClient.post<EquipmentResponse>("/equipments", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: equipmentKeys.all });
    },
  });
}

export function useUpdateEquipment(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: EquipmentUpdate) => {
      const { data } = await apiClient.patch<EquipmentResponse>(
        `/equipments/${id}`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: equipmentKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: equipmentKeys.all });
    },
  });
}

export function useDeactivateEquipment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<EquipmentResponse>(
        `/equipments/${id}/deactivate`
      );
      return data;
    },
    onSuccess: (_data, id) => {
      void qc.invalidateQueries({ queryKey: equipmentKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: equipmentKeys.all });
    },
  });
}

export function useActivateEquipment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<EquipmentResponse>(
        `/equipments/${id}/activate`
      );
      return data;
    },
    onSuccess: (_data, id) => {
      void qc.invalidateQueries({ queryKey: equipmentKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: equipmentKeys.all });
    },
  });
}
