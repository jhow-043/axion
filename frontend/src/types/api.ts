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
  role: UserRole;
  exp: number;
  iat: number;
}

export interface AuthTokens {
  access_token: string;
  token_type: "bearer";
}

export interface UserSession {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  tenant_id: string;
}
