export interface ActorSummary {
  id: string;
  name: string;
}

export interface TicketEvent {
  id: string;
  type: string;
  actor: ActorSummary | null;
  payload: Record<string, unknown> | null;
  created_at: string; // ISO 8601 UTC
}

export interface TicketTimelineResponse {
  total: number;
  page: number;
  page_size: number;
  items: TicketEvent[];
}

export interface TimelineFilters {
  page?: number;
  page_size?: number;
}
