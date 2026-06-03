import { useInfiniteQuery } from "@tanstack/react-query";

import { apiClient } from "@/shared/api/client";
import type { TicketTimelineResponse } from "./types";

const timelineKeys = {
  all: ["timeline"] as const,
  ticket: (ticketId: string) => [...timelineKeys.all, "ticket", ticketId] as const,
};

export function useTicketTimeline(ticketId: string) {
  return useInfiniteQuery({
    queryKey: timelineKeys.ticket(ticketId),
    queryFn: async ({ pageParam = 1 }) => {
      const { data } = await apiClient.get<TicketTimelineResponse>(
        `/tickets/${ticketId}/timeline?page=${pageParam}&page_size=50`,
      );
      return data;
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const loaded = (lastPage.page - 1) * lastPage.page_size + lastPage.items.length;
      return loaded < lastPage.total ? lastPage.page + 1 : undefined;
    },
    enabled: Boolean(ticketId),
  });
}
