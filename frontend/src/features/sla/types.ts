export type SlaStatus = "running" | "paused" | "met" | "breached";

export interface SlaAttendance {
  due_at: string | null;
  status: SlaStatus;
  met_at: string | null;
}

export interface SlaResolution {
  due_at: string | null;
  status: SlaStatus;
  met_at: string | null;
  elapsed_minutes: number | null;
  remaining_minutes: number | null;
  paused_minutes: number;
}

export interface TicketSla {
  policy_id: string;
  attendance: SlaAttendance;
  resolution: SlaResolution;
}

export interface SlaPolicy {
  id: string;
  tenant_id: string;
  ticket_type: "industrial" | "predial" | "all";
  priority_id: string;
  team_id: string | null;
  attendance_minutes: number;
  resolution_minutes: number;
  alert_threshold_pct: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SlaPolicyCreate {
  ticket_type: "industrial" | "predial" | "all";
  priority_id: string;
  team_id?: string;
  attendance_minutes: number;
  resolution_minutes: number;
  alert_threshold_pct?: number;
}

export interface SlaPolicyPatch {
  attendance_minutes?: number;
  resolution_minutes?: number;
  alert_threshold_pct?: number;
}

export interface SlaPolicyListResponse {
  total: number;
  page: number;
  page_size: number;
  items: SlaPolicy[];
}
