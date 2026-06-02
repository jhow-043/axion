import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/shared/api/client";
import type {
  MemberAddRequest,
  MemberResponse,
  TeamCreate,
  TeamDetailResponse,
  TeamFilters,
  TeamListResponse,
  TeamUpdate,
} from "./types";

const teamKeys = {
  all: ["teams"] as const,
  list: (filters: TeamFilters) => [...teamKeys.all, "list", filters] as const,
  detail: (id: string) => [...teamKeys.all, "detail", id] as const,
  members: (id: string) => [...teamKeys.all, "members", id] as const,
};

export function useTeams(filters: TeamFilters = {}) {
  return useQuery({
    queryKey: teamKeys.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.page) params.set("page", String(filters.page));
      if (filters.page_size) params.set("page_size", String(filters.page_size));
      if (filters.is_active !== undefined) params.set("is_active", String(filters.is_active));
      const { data } = await apiClient.get<TeamListResponse>(`/teams?${params.toString()}`);
      return data;
    },
  });
}

export function useTeam(id: string) {
  return useQuery({
    queryKey: teamKeys.detail(id),
    queryFn: async () => {
      const { data } = await apiClient.get<TeamDetailResponse>(`/teams/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useCreateTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TeamCreate) => {
      const { data } = await apiClient.post<TeamDetailResponse>("/teams", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: teamKeys.all });
    },
  });
}

export function useUpdateTeam(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TeamUpdate) => {
      const { data } = await apiClient.patch<TeamDetailResponse>(`/teams/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: teamKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: teamKeys.all });
    },
  });
}

export function useDeactivateTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<TeamDetailResponse>(`/teams/${id}/deactivate`);
      return data;
    },
    onSuccess: (_data, id) => {
      void qc.invalidateQueries({ queryKey: teamKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: teamKeys.all });
    },
  });
}

export function useTeamMembers(teamId: string) {
  return useQuery({
    queryKey: teamKeys.members(teamId),
    queryFn: async () => {
      const { data } = await apiClient.get<MemberResponse[]>(`/teams/${teamId}/members`);
      return data;
    },
    enabled: Boolean(teamId),
  });
}

export function useAddMember(teamId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: MemberAddRequest) => {
      const { data } = await apiClient.post<MemberResponse[]>(
        `/teams/${teamId}/members`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: teamKeys.members(teamId) });
      void qc.invalidateQueries({ queryKey: teamKeys.detail(teamId) });
    },
  });
}

export function useRemoveMember(teamId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => {
      await apiClient.delete(`/teams/${teamId}/members/${userId}`);
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: teamKeys.members(teamId) });
      void qc.invalidateQueries({ queryKey: teamKeys.detail(teamId) });
    },
  });
}
