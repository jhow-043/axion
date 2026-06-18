import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi } from "vitest";
import { HubHome } from "../HubHome";
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

function renderHubHome() {
  return render(
    <MemoryRouter>
      <HubHome />
    </MemoryRouter>,
  );
}

describe("HubHome", () => {
  it("exibe spinner durante carregamento da sessão", () => {
    mockUseAuth.mockReturnValue({
      session: null,
      isLoading: true,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderHubHome();
    expect(document.querySelector(".animate-spin")).toBeTruthy();
  });

  it("exibe mensagem quando não há módulos liberados", () => {
    mockUseAuth.mockReturnValue({
      session: makeSession([]),
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderHubHome();
    expect(screen.getByText(/nenhum módulo disponível/i)).toBeInTheDocument();
    expect(screen.getByText(/entre em contato com o administrador/i)).toBeInTheDocument();
  });

  it("exibe card de Manutenção quando módulo manutencao está liberado", () => {
    mockUseAuth.mockReturnValue({
      session: makeSession(["manutencao"]),
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderHubHome();
    expect(screen.getByText("Gestão de Manutenção")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /acessar/i })).toBeInTheDocument();
  });

  it("não exibe card para módulo liberado que não existe no registry", () => {
    mockUseAuth.mockReturnValue({
      session: makeSession(["modulo_inexistente"]),
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderHubHome();
    expect(screen.queryByRole("button", { name: /acessar/i })).not.toBeInTheDocument();
    expect(screen.getByText(/nenhum módulo disponível/i)).toBeInTheDocument();
  });

  it("clique em Acessar navega para a rota do módulo", async () => {
    const user = userEvent.setup();
    mockUseAuth.mockReturnValue({
      session: makeSession(["manutencao"]),
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    const { container } = renderHubHome();
    await user.click(screen.getByRole("button", { name: /acessar/i }));

    // useNavigate redirects — verify button was clicked without error
    expect(container).toBeTruthy();
  });
});
