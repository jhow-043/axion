import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/shared/api/client";
import type {
  EntityFilters,
  LocationCreate,
  LocationListResponse,
  LocationResponse,
  LocationUpdate,
  SectorCreate,
  SectorListResponse,
  SectorResponse,
  SectorUpdate,
} from "./types";

// ── Sector query keys ─────────────────────────────────────────────────────────

const sectorKeys = {
  all: ["sectors"] as const,
  list: (filters: EntityFilters) => [...sectorKeys.all, "list", filters] as const,
  detail: (id: string) => [...sectorKeys.all, "detail", id] as const,
};

// ── Sector hooks ──────────────────────────────────────────────────────────────

export function useSectors(filters: EntityFilters = {}) {
  return useQuery({
    queryKey: sectorKeys.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.page) params.set("page", String(filters.page));
      if (filters.page_size) params.set("page_size", String(filters.page_size));
      if (filters.is_active !== undefined) params.set("is_active", String(filters.is_active));
      const { data } = await apiClient.get<SectorListResponse>(`/sectors?${params.toString()}`);
      return data;
    },
  });
}

export function useSector(id: string) {
  return useQuery({
    queryKey: sectorKeys.detail(id),
    queryFn: async () => {
      const { data } = await apiClient.get<SectorResponse>(`/sectors/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useCreateSector() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: SectorCreate) => {
      const { data } = await apiClient.post<SectorResponse>("/sectors", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: sectorKeys.all });
    },
  });
}

export function useUpdateSector(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: SectorUpdate) => {
      const { data } = await apiClient.patch<SectorResponse>(`/sectors/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: sectorKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: sectorKeys.all });
    },
  });
}

export function useDeactivateSector() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<SectorResponse>(`/sectors/${id}/deactivate`);
      return data;
    },
    onSuccess: (_data, id) => {
      void qc.invalidateQueries({ queryKey: sectorKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: sectorKeys.all });
    },
  });
}

export function useReactivateSector() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<SectorResponse>(`/sectors/${id}/reactivate`);
      return data;
    },
    onSuccess: (_data, id) => {
      void qc.invalidateQueries({ queryKey: sectorKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: sectorKeys.all });
    },
  });
}

// ── Location query keys ───────────────────────────────────────────────────────

const locationKeys = {
  all: ["locations"] as const,
  list: (filters: EntityFilters) => [...locationKeys.all, "list", filters] as const,
  detail: (id: string) => [...locationKeys.all, "detail", id] as const,
};

// ── Location hooks ────────────────────────────────────────────────────────────

export function useLocations(filters: EntityFilters = {}) {
  return useQuery({
    queryKey: locationKeys.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.page) params.set("page", String(filters.page));
      if (filters.page_size) params.set("page_size", String(filters.page_size));
      if (filters.is_active !== undefined) params.set("is_active", String(filters.is_active));
      const { data } = await apiClient.get<LocationListResponse>(
        `/locations?${params.toString()}`,
      );
      return data;
    },
  });
}

export function useLocation(id: string) {
  return useQuery({
    queryKey: locationKeys.detail(id),
    queryFn: async () => {
      const { data } = await apiClient.get<LocationResponse>(`/locations/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useCreateLocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: LocationCreate) => {
      const { data } = await apiClient.post<LocationResponse>("/locations", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: locationKeys.all });
    },
  });
}

export function useUpdateLocation(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: LocationUpdate) => {
      const { data } = await apiClient.patch<LocationResponse>(`/locations/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: locationKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: locationKeys.all });
    },
  });
}

export function useDeactivateLocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<LocationResponse>(`/locations/${id}/deactivate`);
      return data;
    },
    onSuccess: (_data, id) => {
      void qc.invalidateQueries({ queryKey: locationKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: locationKeys.all });
    },
  });
}

export function useReactivateLocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<LocationResponse>(`/locations/${id}/reactivate`);
      return data;
    },
    onSuccess: (_data, id) => {
      void qc.invalidateQueries({ queryKey: locationKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: locationKeys.all });
    },
  });
}
