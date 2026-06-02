import { describe, it, expect, beforeEach, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/mocks/server";
import { apiClient, setAccessToken, getAccessToken } from "@/shared/api/client";

const BASE = "http://localhost:8000/api/v1";

describe("apiClient — interceptor JWT", () => {
  beforeEach(() => {
    setAccessToken(null);
  });

  it("envia Authorization: Bearer quando há token", async () => {
    setAccessToken("meu-token");
    let capturedAuth: string | null = null;

    server.use(
      http.get(`${BASE}/ping`, ({ request }) => {
        capturedAuth = request.headers.get("Authorization");
        return HttpResponse.json({ status: "ok" });
      }),
    );

    await apiClient.get("/ping");
    expect(capturedAuth).toBe("Bearer meu-token");
  });

  it("não envia Authorization quando não há token", async () => {
    let capturedAuth: string | null = "presente";

    server.use(
      http.get(`${BASE}/ping`, ({ request }) => {
        capturedAuth = request.headers.get("Authorization");
        return HttpResponse.json({ status: "ok" });
      }),
    );

    await apiClient.get("/ping");
    expect(capturedAuth).toBeNull();
  });
});

describe("apiClient — interceptor refresh", () => {
  beforeEach(() => {
    setAccessToken("expired-token");
  });

  it("refresh bem-sucedido: repete request original com novo token", async () => {
    let attempts = 0;

    server.use(
      http.get(`${BASE}/protected`, () => {
        attempts++;
        if (attempts === 1) return HttpResponse.json({ detail: "Não autorizado" }, { status: 401 });
        return HttpResponse.json({ data: "ok" });
      }),
      http.post(`${BASE}/auth/refresh`, () =>
        HttpResponse.json({ access_token: "new-token", token_type: "bearer" }),
      ),
    );

    const res = await apiClient.get("/protected");
    expect(res.data).toEqual({ data: "ok" });
    expect(getAccessToken()).toBe("new-token");
  });

  it("refresh falho: dispara auth:logout e rejeita a promise", async () => {
    const logoutListener = vi.fn();
    window.addEventListener("auth:logout", logoutListener);

    server.use(
      http.get(`${BASE}/protected`, () =>
        HttpResponse.json({ detail: "Não autorizado" }, { status: 401 }),
      ),
      http.post(`${BASE}/auth/refresh`, () =>
        HttpResponse.json({ detail: "Token expirado" }, { status: 401 }),
      ),
    );

    await expect(apiClient.get("/protected")).rejects.toBeDefined();
    expect(logoutListener).toHaveBeenCalledOnce();
    expect(getAccessToken()).toBeNull();

    window.removeEventListener("auth:logout", logoutListener);
  });

  it("requisições enfileiradas durante refresh falho são todas rejeitadas", async () => {
    let refreshCalls = 0;

    server.use(
      http.get(`${BASE}/protected`, () =>
        HttpResponse.json({ detail: "Não autorizado" }, { status: 401 }),
      ),
      http.post(`${BASE}/auth/refresh`, () => {
        refreshCalls++;
        return HttpResponse.json({ detail: "Token expirado" }, { status: 401 });
      }),
    );

    const results = await Promise.allSettled([
      apiClient.get("/protected"),
      apiClient.get("/protected"),
      apiClient.get("/protected"),
    ]);

    // todas as 3 promises devem ser rejeitadas, não pendentes
    expect(results.every((r) => r.status === "rejected")).toBe(true);
    // o refresh deve ter sido chamado apenas 1 vez (as demais enfileiraram)
    expect(refreshCalls).toBe(1);
  });
});
