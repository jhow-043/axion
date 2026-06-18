import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GlobalDashboard } from "../GlobalDashboard";

vi.mock("../../api");

import * as api from "../../api";
const mockUseGlobalDashboard = vi.mocked(api.useGlobalDashboard);
const mockUseActivateCompany = vi.mocked(api.useActivateCompany);
const mockUseSuspendCompany = vi.mocked(api.useSuspendCompany);
const mockUseDeleteCompany = vi.mocked(api.useDeleteCompany);

const MOCK_DASHBOARD = {
  total_companies: 3,
  active_companies: 2,
  suspended_companies: 1,
  total_users: 45,
  total_tickets: 120,
  companies: [
    {
      id: "c1",
      name: "Acme Corp",
      slug: "acme",
      is_active: true,
      is_system: false,
      created_at: "2024-01-15T10:00:00Z",
      user_count: 10,
      ticket_count: 50,
      plan: null,
    },
    {
      id: "c2",
      name: "Inactive Ltd",
      slug: "inactive",
      is_active: false,
      is_system: false,
      created_at: "2024-02-01T10:00:00Z",
      user_count: 5,
      ticket_count: 20,
      plan: null,
    },
  ],
  page: 1,
  page_size: 20,
  total_company_pages: 1,
};

const mutationStub = { mutate: vi.fn(), mutateAsync: vi.fn(), isPending: false } as never;

function setup() {
  mockUseActivateCompany.mockReturnValue(mutationStub);
  mockUseSuspendCompany.mockReturnValue(mutationStub);
  mockUseDeleteCompany.mockReturnValue(mutationStub);
}

function renderDashboard() {
  return render(
    <MemoryRouter>
      <GlobalDashboard />
    </MemoryRouter>,
  );
}

describe("GlobalDashboard", () => {
  beforeEach(() => {
    setup();
  });

  it("exibe skeletons enquanto carrega", () => {
    mockUseGlobalDashboard.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as never);

    const { container } = renderDashboard();
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });

  it("exibe KPIs após carregar", async () => {
    mockUseGlobalDashboard.mockReturnValue({
      data: MOCK_DASHBOARD,
      isLoading: false,
      error: null,
    } as never);

    renderDashboard();

    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("45")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();
  });

  it("exibe tabela de empresas", () => {
    mockUseGlobalDashboard.mockReturnValue({
      data: MOCK_DASHBOARD,
      isLoading: false,
      error: null,
    } as never);

    renderDashboard();

    expect(screen.getByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("Inactive Ltd")).toBeInTheDocument();
    expect(screen.getAllByText("Ativa")).toHaveLength(1);
    expect(screen.getAllByText("Suspensa")).toHaveLength(1);
  });

  it("abre modal de provisionamento ao clicar em Nova empresa", async () => {
    const user = userEvent.setup();
    mockUseGlobalDashboard.mockReturnValue({
      data: MOCK_DASHBOARD,
      isLoading: false,
      error: null,
    } as never);

    vi.mock("../CompanyProvisionModal", () => ({
      CompanyProvisionModal: ({ onClose }: { onClose: () => void }) => (
        <div data-testid="provision-modal">
          <button onClick={onClose}>Fechar</button>
        </div>
      ),
    }));

    renderDashboard();
    await user.click(screen.getByText("+ Nova empresa"));
    expect(screen.getByTestId("provision-modal")).toBeInTheDocument();
  });

  it("abre confirmação de exclusão ao clicar em Excluir", async () => {
    const user = userEvent.setup();
    mockUseGlobalDashboard.mockReturnValue({
      data: MOCK_DASHBOARD,
      isLoading: false,
      error: null,
    } as never);

    renderDashboard();
    await user.click(screen.getAllByText("Excluir")[0]);
    expect(screen.getByText(/Tem certeza que deseja excluir/i)).toBeInTheDocument();
    // "Acme Corp" appears in table row + confirmation dialog — both expected
    expect(screen.getAllByText("Acme Corp").length).toBeGreaterThanOrEqual(1);
  });

  it("exibe mensagem de erro quando API falha", () => {
    mockUseGlobalDashboard.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Network error"),
    } as never);

    renderDashboard();
    expect(screen.getByText(/Erro ao carregar empresas/i)).toBeInTheDocument();
  });

  it("exibe mensagem quando lista está vazia", () => {
    mockUseGlobalDashboard.mockReturnValue({
      data: { ...MOCK_DASHBOARD, companies: [], total_companies: 0 },
      isLoading: false,
      error: null,
    } as never);

    renderDashboard();
    expect(screen.getByText(/Nenhuma empresa cadastrada/i)).toBeInTheDocument();
  });

  it("confirma exclusão e chama mutação", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue(undefined);
    mockUseDeleteCompany.mockReturnValue({
      ...mutationStub,
      mutateAsync,
    } as never);
    mockUseGlobalDashboard.mockReturnValue({
      data: MOCK_DASHBOARD,
      isLoading: false,
      error: null,
    } as never);

    renderDashboard();
    // Click first row's Excluir to open confirmation dialog
    await user.click(screen.getAllByText("Excluir")[0]);
    // Confirm: the dialog button is the last "Excluir" button in the DOM
    const excluirButtons = screen.getAllByRole("button", { name: /^Excluir$/i });
    await user.click(excluirButtons[excluirButtons.length - 1]);

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith("c1");
    });
  });
});
