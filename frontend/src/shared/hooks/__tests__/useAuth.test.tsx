import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, it, expect } from "vitest";
import { AuthProvider } from "@/app/providers/AuthProvider";
import { useAuth } from "@/shared/hooks/useAuth";
import { server } from "@/test/mocks/server";
import type { ReactNode } from "react";

const BASE = "http://localhost:8000/api/v1";

function TestConsumer() {
  const { session, login, logout, isLoading } = useAuth();
  if (isLoading) return <div>loading</div>;
  return (
    <div>
      <span data-testid="name">{session?.full_name ?? "anon"}</span>
      <button onClick={() => void login("user@test.com", "secret")}>login</button>
      <button onClick={() => void logout()}>logout</button>
    </div>
  );
}

function Wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe("AuthProvider", () => {
  it("inicia carregando e depois exibe usuário anônimo quando refresh falha", async () => {
    render(<TestConsumer />, { wrapper: Wrapper });
    expect(screen.getByText("loading")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("name")).toHaveTextContent("anon"));
  });

  it("login bem-sucedido atualiza a sessão", async () => {
    server.use(
      http.post(`${BASE}/auth/login`, () =>
        HttpResponse.json({ access_token: "tok", token_type: "bearer" }),
      ),
      http.get(`${BASE}/auth/me`, () =>
        HttpResponse.json({
          id: "1",
          email: "user@test.com",
          full_name: "Fulano",
          role: "admin",
          tenant_id: "t1",
        }),
      ),
    );

    render(<TestConsumer />, { wrapper: Wrapper });
    await waitFor(() => expect(screen.queryByText("loading")).not.toBeInTheDocument());

    await userEvent.click(screen.getByText("login"));
    await waitFor(() => expect(screen.getByTestId("name")).toHaveTextContent("Fulano"));
  });

  it("logout limpa a sessão", async () => {
    server.use(
      http.post(`${BASE}/auth/login`, () =>
        HttpResponse.json({ access_token: "tok", token_type: "bearer" }),
      ),
      http.get(`${BASE}/auth/me`, () =>
        HttpResponse.json({
          id: "1",
          email: "user@test.com",
          full_name: "Fulano",
          role: "admin",
          tenant_id: "t1",
        }),
      ),
    );

    render(<TestConsumer />, { wrapper: Wrapper });
    await waitFor(() => expect(screen.queryByText("loading")).not.toBeInTheDocument());

    await userEvent.click(screen.getByText("login"));
    await waitFor(() => expect(screen.getByTestId("name")).toHaveTextContent("Fulano"));

    await userEvent.click(screen.getByText("logout"));
    await waitFor(() => expect(screen.getByTestId("name")).toHaveTextContent("anon"));
  });

  it("disparo de auth:logout força logout", async () => {
    server.use(
      http.post(`${BASE}/auth/refresh`, () =>
        HttpResponse.json({ access_token: "tok", token_type: "bearer" }),
      ),
      http.get(`${BASE}/auth/me`, () =>
        HttpResponse.json({
          id: "1",
          email: "user@test.com",
          full_name: "Auto",
          role: "technician",
          tenant_id: "t1",
        }),
      ),
    );

    render(<TestConsumer />, { wrapper: Wrapper });
    await waitFor(() => expect(screen.getByTestId("name")).toHaveTextContent("Auto"));

    act(() => window.dispatchEvent(new Event("auth:logout")));
    await waitFor(() => expect(screen.getByTestId("name")).toHaveTextContent("anon"));
  });
});
