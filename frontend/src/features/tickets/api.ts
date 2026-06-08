import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/shared/api/client";
import type {
  TicketCommentCreate,
  TicketCommentListResponse,
  TicketCommentResponse,
  TicketCreate,
  TicketFilters,
  TicketListResponse,
  TicketResponse,
  TicketTransition,
} from "./types";

const ticketKeys = {
  all: ["tickets"] as const,
  list: (filters: TicketFilters) => [...ticketKeys.all, "list", filters] as const,
  detail: (id: string) => [...ticketKeys.all, "detail", id] as const,
  comments: (id: string) => [...ticketKeys.all, "comments", id] as const,
};

export function useCreateTicket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TicketCreate) => {
      const { data } = await apiClient.post<TicketResponse>("/tickets", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ticketKeys.all });
    },
  });
}

export function useTickets(filters: TicketFilters = {}) {
  return useQuery({
    queryKey: ticketKeys.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.page) params.set("page", String(filters.page));
      if (filters.page_size) params.set("page_size", String(filters.page_size));
      if (filters.type) params.set("type", filters.type);
      if (filters.status_code) params.set("status_code", filters.status_code);
      if (filters.search) params.set("search", filters.search);
      if (filters.priority_id) params.set("priority_id", filters.priority_id);
      if (filters.category_id) params.set("category_id", filters.category_id);
      if (filters.team_id) params.set("team_id", filters.team_id);
      if (filters.assignee_id) params.set("assignee_id", filters.assignee_id);
      if (filters.requester_id) params.set("requester_id", filters.requester_id);
      if (filters.equipment_id) params.set("equipment_id", filters.equipment_id);
      if (filters.location_id) params.set("location_id", filters.location_id);
      if (filters.sector_id) params.set("sector_id", filters.sector_id);
      if (filters.created_from) params.set("created_from", filters.created_from);
      if (filters.created_to) params.set("created_to", filters.created_to);
      const { data } = await apiClient.get<TicketListResponse>(`/tickets?${params.toString()}`);
      return data;
    },
  });
}

export function useTicket(id: string) {
  return useQuery({
    queryKey: ticketKeys.detail(id),
    queryFn: async () => {
      const { data } = await apiClient.get<TicketResponse>(`/tickets/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useAssignTicket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (ticketId: string) => {
      const { data } = await apiClient.post<TicketResponse>(`/tickets/${ticketId}/assign`);
      return data;
    },
    onSuccess: (_data, ticketId) => {
      void qc.invalidateQueries({ queryKey: ticketKeys.detail(ticketId) });
      void qc.invalidateQueries({ queryKey: ticketKeys.all });
    },
  });
}

export function useTransitionTicket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ ticketId, body }: { ticketId: string; body: TicketTransition }) => {
      const { data } = await apiClient.post<TicketResponse>(
        `/tickets/${ticketId}/transition`,
        body,
      );
      return data;
    },
    onSuccess: (_data, { ticketId }) => {
      void qc.invalidateQueries({ queryKey: ticketKeys.detail(ticketId) });
      void qc.invalidateQueries({ queryKey: ticketKeys.all });
    },
  });
}

export function useTicketComments(ticketId: string, page = 1) {
  return useQuery({
    queryKey: [...ticketKeys.comments(ticketId), page],
    queryFn: async () => {
      const { data } = await apiClient.get<TicketCommentListResponse>(
        `/tickets/${ticketId}/comments?page=${page}&page_size=50`,
      );
      return data;
    },
    enabled: Boolean(ticketId),
  });
}

export function useAddTicketComment(ticketId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TicketCommentCreate) => {
      const { data } = await apiClient.post<TicketCommentResponse>(
        `/tickets/${ticketId}/comments`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ticketKeys.comments(ticketId) });
    },
  });
}
