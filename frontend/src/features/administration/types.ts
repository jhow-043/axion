export interface TenantResponse {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
}

export interface TenantListResponse {
  total: number;
  page: number;
  page_size: number;
  items: TenantResponse[];
}

export interface TenantCreate {
  name: string;
  slug: string;
  admin_name: string;
  admin_email: string;
  admin_password: string;
}

export interface TenantUpdate {
  name?: string;
  slug?: string;
  is_active?: boolean;
}
