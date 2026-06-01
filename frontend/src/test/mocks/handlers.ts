import { http, HttpResponse } from "msw";

const BASE = "http://localhost:8000/api/v1";

export const handlers = [
  http.get(`${BASE}/ping`, () => {
    return HttpResponse.json({ status: "ok" });
  }),

  http.post(`${BASE}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string };
    if (body.email === "user@test.com" && body.password === "secret") {
      return HttpResponse.json({ access_token: "mock-access-token", token_type: "bearer" });
    }
    return HttpResponse.json({ detail: "Credenciais inválidas" }, { status: 401 });
  }),

  http.post(`${BASE}/auth/refresh`, () => {
    return HttpResponse.json({ detail: "Token inválido" }, { status: 401 });
  }),

  http.post(`${BASE}/auth/logout`, () => {
    return HttpResponse.json({ detail: "Sessão encerrada" });
  }),

  http.get(`${BASE}/auth/me`, () => {
    return HttpResponse.json({ detail: "Não autorizado" }, { status: 401 });
  }),
];
