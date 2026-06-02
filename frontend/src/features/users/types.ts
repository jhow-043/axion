export interface RoleResponse {
  id: string;
  name: string;
  code: string;
  is_default: boolean;
}

export interface PermissionResponse {
  id: string;
  code: string;
  name: string;
}

export interface UserResponse {
  id: string;
  tenant_id: string;
  name: string;
  email: string;
  is_active: boolean;
  roles: RoleResponse[];
}

export interface UserListResponse {
  total: number;
  page: number;
  page_size: number;
  items: UserResponse[];
}

export interface UserCreate {
  name: string;
  email: string;
  password: string;
}

export interface UserUpdate {
  name?: string;
  email?: string;
}

export interface RoleAssignRequest {
  role_id: string;
}

export interface UserFilters {
  name?: string;
  email?: string;
  is_active?: boolean;
  role_code?: string;
  page?: number;
  page_size?: number;
}
