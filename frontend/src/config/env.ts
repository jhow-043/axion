function requireEnv(key: string): string {
  const value = import.meta.env[key];
  if (!value) throw new Error(`Variável de ambiente obrigatória não definida: ${key}`);
  return value as string;
}

export const env = {
  apiBaseUrl: (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? "http://localhost:8000",
  wsBaseUrl: (import.meta.env["VITE_WS_BASE_URL"] as string | undefined) ?? "ws://localhost:8000",
} as const;

export { requireEnv };
