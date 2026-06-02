import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi } from "vitest";
import { RequireRole } from "@/shared/components/RequireRole";
import { AuthContext } from "@/app/providers/AuthProvider";
import type { UserRole, UserSession } from "@/types/api";

function makeSession(role: UserRole): UserSession {
  return { id: "1", email: "a@b.com", name: "A", roles: [role], is_active: true, tenant_id: "t1" };
}

function Wrapper({
  session,
  roles,
}: {
  session: UserSession | null;
  roles: UserRole[];
}) {
  return (
    <AuthContext.Provider value={{ session, isLoading: false, login: vi.fn(), logout: vi.fn() }}>
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <RequireRole roles={roles}>
                <span>conteúdo restrito</span>
              </RequireRole>
            }
          />
          <Route path="/sem-permissao" element={<span>sem permissão</span>} />
          <Route path="/login" element={<span>login</span>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("RequireRole", () => {
  it("renderiza filhos quando papel é permitido", async () => {
    render(<Wrapper session={makeSession("admin")} roles={["admin", "supervisor"]} />);
    await waitFor(() =>
      expect(screen.getByText("conteúdo restrito")).toBeInTheDocument(),
    );
  });

  it("redireciona para /sem-permissao quando papel insuficiente", async () => {
    render(<Wrapper session={makeSession("requester")} roles={["admin", "supervisor"]} />);
    await waitFor(() => expect(screen.getByText("sem permissão")).toBeInTheDocument());
  });

  it("redireciona para /login quando sem sessão", async () => {
    render(<Wrapper session={null} roles={["admin"]} />);
    await waitFor(() => expect(screen.getByText("login")).toBeInTheDocument());
  });

  it("exibe fallback quando papel insuficiente e fallback fornecido", async () => {
    render(
      <AuthContext.Provider
        value={{ session: makeSession("technician"), isLoading: false, login: vi.fn(), logout: vi.fn() }}
      >
        <MemoryRouter>
          <RequireRole roles={["admin"]} fallback={<span>acesso negado</span>}>
            <span>secreto</span>
          </RequireRole>
        </MemoryRouter>
      </AuthContext.Provider>,
    );
    await waitFor(() => expect(screen.getByText("acesso negado")).toBeInTheDocument());
    expect(screen.queryByText("secreto")).not.toBeInTheDocument();
  });
});
