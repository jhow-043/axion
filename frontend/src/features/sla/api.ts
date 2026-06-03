import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/shared/api/client";
import type { SlaPolicy, SlaPolicyCreate, TicketSla } from "./types";

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
  return useQuery<{ items: SlaPolicy[]; total: number }>({
    queryKey: slaKeys.policies(),
    queryFn: () =>
      apiClient.get("/sla/policies").then((r) => r.data),
  });
}
