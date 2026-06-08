import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/shared/api/client";
import type {
  SlaPolicy,
  SlaPolicyCreate,
  SlaPolicyListResponse,
  SlaPolicyPatch,
  TicketSla,
} from "./types";

const slaKeys = {
  ticketSla: (ticketId: string) => ["sla", "ticket", ticketId] as const,
  policies: () => ["sla", "policies"] as const,
};

export function useTicketSla(ticketId: string) {
  return useQuery<TicketSla>({
    queryKey: slaKeys.ticketSla(ticketId),
    queryFn: () =>
      apiClient.get<TicketSla>(`/tickets/${ticketId}/sla`).then((r) => r.data),
    retry: false,
  });
}

export function useSlaPolices() {
  return useQuery<SlaPolicyListResponse>({
    queryKey: slaKeys.policies(),
    queryFn: () => apiClient.get("/sla/policies").then((r) => r.data),
  });
}

export function useCreateSlaPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: SlaPolicyCreate) => {
      const { data } = await apiClient.post<SlaPolicy>("/sla/policies", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: slaKeys.policies() });
    },
  });
}

export function useUpdateSlaPolicy(policyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: SlaPolicyPatch) => {
      const { data } = await apiClient.patch<SlaPolicy>(
        `/sla/policies/${policyId}`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: slaKeys.policies() });
    },
  });
}

export function useDeactivateSlaPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (policyId: string) => {
      const { data } = await apiClient.post<SlaPolicy>(
        `/sla/policies/${policyId}/deactivate`,
      );
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: slaKeys.policies() });
    },
  });
}
