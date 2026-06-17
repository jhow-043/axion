export interface CompanyRow {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  is_system: boolean;
  created_at: string;
  user_count: number;
  ticket_count: number;
  plan: string | null;
}

export interface GlobalDashboardResponse {
  total_companies: number;
  active_companies: number;
  suspended_companies: number;
  total_users: number;
  total_tickets: number;
  companies: CompanyRow[];
  page: number;
  page_size: number;
  total_company_pages: number;
}

export interface TenantResponse {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  is_system: boolean;
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
}

export interface ModuleCatalogItem {
  id: string;
  code: string;
  name: string;
  icon: string | null;
  is_active: boolean;
}

export interface TenantEnabledModule {
  module_id: string;
  module_code: string;
  enabled_at: string;
}

export interface TenantModulesResponse {
  catalog: ModuleCatalogItem[];
  enabled: TenantEnabledModule[];
}
