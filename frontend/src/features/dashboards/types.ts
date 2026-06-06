export interface SlaRiskTicket {
  ticket_id: string;
  title: string;
  sla_type: "attendance" | "resolution";
  due_at: string;
}

export interface SlaBreachedTicket {
  ticket_id: string;
  title: string;
  sla_type: "attendance" | "resolution";
  breached_at: string;
}

export interface AssignedTicketsSummary {
  total: number;
  by_status: Record<string, number>;
}

export interface TechnicianDashboardResponse {
  assigned_tickets: AssignedTicketsSummary;
  sla_at_risk: SlaRiskTicket[];
  sla_breached: SlaBreachedTicket[];
}

export interface TeamSlaStats {
  team_id: string;
  team_name: string;
  total_open: number;
  sla_at_risk: number;
  sla_breached: number;
}

export interface SlaSummary {
  attendance_compliance_pct: number;
  resolution_compliance_pct: number;
}

export interface TicketsSummary {
  total_open: number;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
}

export interface SupervisorDashboardResponse {
  summary: TicketsSummary;
  teams: TeamSlaStats[];
  sla_summary: SlaSummary;
}

export interface BoardTicketItem {
  id: string;
  title: string;
  priority: string;
  assignee: string | null;
  sla_status: "running" | "met" | "breached" | null;
}

export interface BoardColumn {
  status_code: string;
  status_name: string;
  tickets: BoardTicketItem[];
}

export interface BoardResponse {
  columns: BoardColumn[];
}

export interface BoardFilters {
  team_id?: string;
  assignee_id?: string;
  priority_id?: string;
}

export interface SupervisorFilters {
  team_id?: string;
  priority_id?: string;
  date_from?: string;
  date_to?: string;
}

// ── P16 — Dashboard Gerencial ─────────────────────────────────────────────────

export interface ManagementPeriod {
  date_from: string;
  date_to: string;
}

export interface ManagementSummary {
  total_tickets: number;
  open: number;
  closed: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  avg_resolution_hours: number;
}

export interface ManagementSla {
  attendance_compliance_pct: number;
  resolution_compliance_pct: number;
  breached_count: number;
}

export interface TopProblematicEquipment {
  equipment_id: string;
  name: string;
  ticket_count: number;
  critical_count: number;
}

export interface TeamPerformance {
  team_id: string;
  name: string;
  total: number;
  sla_compliance_pct: number;
  avg_resolution_hours: number;
}

export interface ManagementDashboardResponse {
  period: ManagementPeriod;
  summary: ManagementSummary;
  sla: ManagementSla;
  top_problematic_equipments: TopProblematicEquipment[];
  team_performance: TeamPerformance[];
}

export interface ManagementFilters {
  date_from?: string;
  date_to?: string;
  team_id?: string;
  priority_id?: string;
  ticket_type?: string;
}

export interface ReportFilters {
  date_from: string;
  date_to: string;
  team_id?: string;
  priority_id?: string;
  ticket_type?: string;
  format?: "json" | "csv";
}
