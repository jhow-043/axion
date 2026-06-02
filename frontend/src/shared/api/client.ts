import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { env } from "@/config/env";
import { API_PREFIX } from "@/config/constants";

let accessToken: string | null = null;
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];
let refreshRejecters: Array<(err: unknown) => void> = [];

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

function subscribeTokenRefresh(
  resolve: (token: string) => void,
  reject: (err: unknown) => void,
): void {
  refreshSubscribers.push(resolve);
  refreshRejecters.push(reject);
}

function onTokenRefreshed(token: string): void {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
  refreshRejecters = [];
}

function onRefreshFailed(err: unknown): void {
  refreshRejecters.forEach((cb) => cb(err));
  refreshSubscribers = [];
  refreshRejecters = [];
}

export const apiClient = axios.create({
  baseURL: `${env.apiBaseUrl}${API_PREFIX}`,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (accessToken) {
    config.headers["Authorization"] = `Bearer ${accessToken}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        subscribeTokenRefresh(
          (token) => {
            original.headers["Authorization"] = `Bearer ${token}`;
            resolve(apiClient(original));
          },
          reject,
        );
      });
    }

    original._retry = true;
    isRefreshing = true;

    try {
      const { data } = await axios.post<{ access_token: string }>(
        `${env.apiBaseUrl}${API_PREFIX}/auth/refresh`,
        {},
        { withCredentials: true },
      );
      setAccessToken(data.access_token);
      onTokenRefreshed(data.access_token);
      original.headers["Authorization"] = `Bearer ${data.access_token}`;
      return apiClient(original);
    } catch (err) {
      onRefreshFailed(err);
      setAccessToken(null);
      // Notifica o AuthProvider para realizar logout
      window.dispatchEvent(new Event("auth:logout"));
      return Promise.reject(error);
    } finally {
      isRefreshing = false;
    }
  },
);
