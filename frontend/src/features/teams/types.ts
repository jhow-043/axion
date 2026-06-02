export interface MemberResponse {
  user_id: string;
  added_at: string;
}

export interface TeamResponse {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface TeamDetailResponse {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  members: MemberResponse[];
  created_at: string;
  updated_at: string;
}

export interface TeamListResponse {
  total: number;
  page: number;
  page_size: number;
  items: TeamResponse[];
}

export interface TeamCreate {
  name: string;
  description?: string;
}

export interface TeamUpdate {
  name?: string;
  description?: string;
}

export interface MemberAddRequest {
  user_id: string;
}

export interface TeamFilters {
  is_active?: boolean;
  page?: number;
  page_size?: number;
}
