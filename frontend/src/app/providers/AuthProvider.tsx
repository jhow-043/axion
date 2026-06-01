import { createContext, useCallback, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { apiClient, setAccessToken } from "@/shared/api/client";
import type { AuthTokens, UserSession } from "@/types/api";

interface AuthContextValue {
  session: UserSession | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [session, setSession] = useState<UserSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const logoutRef = useRef<() => Promise<void>>();

  const logout = useCallback(async () => {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      // ignora erros no logout — limpa sessão de qualquer forma
    } finally {
      setAccessToken(null);
      setSession(null);
    }
  }, []);

  logoutRef.current = logout;

  useEffect(() => {
    const handleForceLogout = () => void logoutRef.current?.();
    window.addEventListener("auth:logout", handleForceLogout);
    return () => window.removeEventListener("auth:logout", handleForceLogout);
  }, []);

  useEffect(() => {
    // Tenta restaurar sessão via refresh token (cookie httpOnly)
    async function restoreSession() {
      try {
        const { data } = await apiClient.post<AuthTokens>("/auth/refresh");
        setAccessToken(data.access_token);
        const { data: me } = await apiClient.get<UserSession>("/auth/me");
        setSession(me);
      } catch {
        setSession(null);
      } finally {
        setIsLoading(false);
      }
    }
    void restoreSession();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await apiClient.post<AuthTokens>("/auth/login", { email, password });
    setAccessToken(data.access_token);
    const { data: me } = await apiClient.get<UserSession>("/auth/me");
    setSession(me);
  }, []);

  return (
    <AuthContext.Provider value={{ session, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
