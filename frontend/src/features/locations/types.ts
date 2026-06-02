export interface SectorResponse {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SectorListResponse {
  total: number;
  page: number;
  page_size: number;
  items: SectorResponse[];
}

export interface SectorCreate {
  name: string;
  description?: string | null;
}

export interface SectorUpdate {
  name?: string;
  description?: string | null;
}

export interface LocationResponse {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LocationListResponse {
  total: number;
  page: number;
  page_size: number;
  items: LocationResponse[];
}

export interface LocationCreate {
  name: string;
  description?: string | null;
}

export interface LocationUpdate {
  name?: string;
  description?: string | null;
}

export interface EntityFilters {
  is_active?: boolean;
  page?: number;
  page_size?: number;
}
