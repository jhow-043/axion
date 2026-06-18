import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router";
import { describe, it, expect, vi } from "vitest";
import { RequireModule } from "../RequireModule";
import type { UserSession } from "@/types/api";

const makeSession = (modules: string[]): UserSession => ({
  id: "1",
  name: "Test",
  email: "test@test.com",
  tenant_id: "t1",
  roles: ["admin"],
  permissions: [],
  is_active: true,
  enabled_modules: modules,
});

vi.mock("@/shared/hooks/useAuth");
import { useAuth } from "@/shared/hooks/useAuth";
const mockUseAuth = vi.mocked(useAuth);

function renderWithRouter(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/" element={<div>Home</div>} />
        <Route element={<RequireModule code="manutencao" />}>
          <Route path="/tickets" element={<div>Tickets</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("RequireModule", () => {
  it("renderiza Outlet quando módulo está liberado", () => {
    mockUseAuth.mockReturnValue({
      session: makeSession(["manutencao"]),
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderWithRouter("/tickets");
    expect(screen.getByText("Tickets")).toBeInTheDocument();
  });

  it("redireciona para / quando módulo não está liberado", () => {
    mockUseAuth.mockReturnValue({
      session: makeSession([]),
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderWithRouter("/tickets");
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.queryByText("Tickets")).not.toBeInTheDocument();
  });

  it("redireciona para / quando sessão é nula", () => {
    mockUseAuth.mockReturnValue({
      session: null,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderWithRouter("/tickets");
    expect(screen.getByText("Home")).toBeInTheDocument();
  });

  it("não renderiza nada enquanto sessão carrega", () => {
    mockUseAuth.mockReturnValue({
      session: null,
      isLoading: true,
      login: vi.fn(),
      logout: vi.fn(),
    });

    const { container } = renderWithRouter("/tickets");
    expect(container.firstChild).toBeNull();
  });
});
