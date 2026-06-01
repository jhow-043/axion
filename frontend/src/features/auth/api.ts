import { apiClient } from "@/shared/api/client";
import type { AuthTokens, UserSession } from "@/types/api";

export async function login(email: string, password: string): Promise<AuthTokens> {
  const { data } = await apiClient.post<AuthTokens>("/auth/login", { email, password });
  return data;
}

export async function refresh(): Promise<AuthTokens> {
  const { data } = await apiClient.post<AuthTokens>("/auth/refresh");
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout");
}

export async function getMe(): Promise<UserSession> {
  const { data } = await apiClient.get<UserSession>("/auth/me");
  return data;
}
