import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/shared/api/client";
import type {
  BoardFilters,
  BoardResponse,
  SupervisorDashboardResponse,
  SupervisorFilters,
  TechnicianDashboardResponse,
} from "./types";

export const dashboardKeys = {
  technician: () => ["dashboards", "technician"] as const,
  supervisor: (filters: SupervisorFilters) =>
    ["dashboards", "supervisor", filters] as const,
  board: (filters: BoardFilters) => ["dashboards", "board", filters] as const,
};

export function useTechnicianDashboard() {
  return useQuery({
    queryKey: dashboardKeys.technician(),
    queryFn: async () => {
      const { data } = await apiClient.get<TechnicianDashboardResponse>(
        "/dashboards/technician",
      );
      return data;
    },
    staleTime: 55_000,
    refetchInterval: 60_000,
  });
}

export function useSupervisorDashboard(filters: SupervisorFilters = {}) {
  return useQuery({
    queryKey: dashboardKeys.supervisor(filters),
    queryFn: async () => {
      const { data } = await apiClient.get<SupervisorDashboardResponse>(
        "/dashboards/supervisor",
        { params: filters },
      );
      return data;
    },
    staleTime: 55_000,
    refetchInterval: 60_000,
  });
}

export function useBoardData(filters: BoardFilters = {}) {
  return useQuery({
    queryKey: dashboardKeys.board(filters),
    queryFn: async () => {
      const { data } = await apiClient.get<BoardResponse>("/dashboards/board", {
        params: filters,
      });
      return data;
    },
    staleTime: 55_000,
    refetchInterval: 60_000,
  });
}

export async function transitionTicket(
  ticketId: string,
  toStatus: string,
): Promise<void> {
  await apiClient.post(`/tickets/${ticketId}/transition`, {
    to_status: toStatus,
  });
}
