import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/shared/api/client";
import type {
  BoardFilters,
  BoardResponse,
  ManagementDashboardResponse,
  ManagementFilters,
  ReportFilters,
  SupervisorDashboardResponse,
  SupervisorFilters,
  TechnicianDashboardResponse,
} from "./types";

export const dashboardKeys = {
  technician: () => ["dashboards", "technician"] as const,
  supervisor: (filters: SupervisorFilters) =>
    ["dashboards", "supervisor", filters] as const,
  board: (filters: BoardFilters) => ["dashboards", "board", filters] as const,
  management: (filters: ManagementFilters) =>
    ["dashboards", "management", filters] as const,
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

export function useManagementDashboard(filters: ManagementFilters = {}) {
  return useQuery({
    queryKey: dashboardKeys.management(filters),
    queryFn: async () => {
      const { data } = await apiClient.get<ManagementDashboardResponse>(
        "/dashboards/management",
        { params: filters },
      );
      return data;
    },
    staleTime: 120_000,
    refetchInterval: 300_000,
  });
}

export function buildReportUrl(
  reportType: "tickets" | "sla" | "equipments" | "teams",
  filters: ReportFilters,
): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== "") params.set(k, String(v));
  });
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  return `${base}/api/v1/reports/${reportType}?${params.toString()}`;
}

export async function transitionTicket(
  ticketId: string,
  toStatus: string,
): Promise<void> {
  await apiClient.post(`/tickets/${ticketId}/transition`, {
    to_status: toStatus,
  });
}
