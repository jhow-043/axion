export interface TicketResponse {
  id: string;
  tenant_id: string;
  type: string;
  title: string;
  description: string;
  priority_id: string;
  status_id: string;
  category_id: string | null;
  equipment_id: string | null;
  location_id: string | null;
  team_id: string | null;
  requester_id: string;
  assignee_id: string | null;
  assigned_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketListResponse {
  total: number;
  page: number;
  page_size: number;
  items: TicketResponse[];
}

export interface TicketFilters {
  page?: number;
  page_size?: number;
  type?: string;
  status_code?: string;
  search?: string;
  priority_id?: string;
  category_id?: string;
  team_id?: string;
  assignee_id?: string;
  requester_id?: string;
  equipment_id?: string;
  location_id?: string;
  sector_id?: string;
  created_from?: string;
  created_to?: string;
}

export interface TicketCreate {
  type: "industrial" | "predial";
  title: string;
  description: string;
  priority_id: string;
  category_id?: string;
  equipment_id?: string;
  location_id?: string;
  team_id?: string;
}

export interface TicketTransition {
  to_status: "in_progress" | "pending" | "resolved" | "closed";
  pending_reason_id?: string;
  solution_description?: string;
}

export interface TicketCommentCreate {
  content: string;
}

export interface TicketCommentResponse {
  id: string;
  ticket_id: string;
  author_id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface TicketCommentListResponse {
  total: number;
  page: number;
  page_size: number;
  items: TicketCommentResponse[];
}
