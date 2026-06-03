export interface EquipmentResponse {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  sector_id: string;
  is_active: boolean;
  manufacturer: string | null;
  model: string | null;
  serial_number: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface EquipmentListResponse {
  total: number;
  page: number;
  page_size: number;
  items: EquipmentResponse[];
}

export interface EquipmentCreate {
  code: string;
  name: string;
  sector_id: string;
  manufacturer?: string | null;
  model?: string | null;
  serial_number?: string | null;
  notes?: string | null;
}

export interface EquipmentUpdate {
  code?: string;
  name?: string;
  sector_id?: string;
  manufacturer?: string | null;
  model?: string | null;
  serial_number?: string | null;
  notes?: string | null;
}

export interface TicketSummary {
  id: string;
  title: string;
  status_code: string;
  priority_code: string;
  created_at: string;
  assignee_name: string | null;
}

export interface EquipmentTicketsResponse {
  total: number;
  page: number;
  page_size: number;
  items: TicketSummary[];
}

export interface EquipmentFilters {
  page?: number;
  page_size?: number;
  search?: string;
  sector_id?: string;
  is_active?: boolean;
}
