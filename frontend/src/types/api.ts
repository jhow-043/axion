export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiError {
  detail: string | { msg: string; type: string }[];
}

export type UserRole = "admin" | "supervisor" | "technician" | "requester";

export interface TokenPayload {
  sub: string;
  tenant_id: string;
  roles: string[];
  exp: number;
  iat: number;
}

export interface AuthTokens {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface UserSession {
  id: string;
  name: string;
  email: string;
  tenant_id: string;
  roles: string[];
  is_active: boolean;
}
