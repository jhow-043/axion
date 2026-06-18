import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { CompanyProvisionModal } from "../CompanyProvisionModal";

vi.mock("../../api");

import * as api from "../../api";
const mockUseProvisionCompany = vi.mocked(api.useProvisionCompany);

const mutationBase = { isPending: false, mutateAsync: vi.fn() };

function renderModal(onClose = vi.fn()) {
  return render(<CompanyProvisionModal onClose={onClose} />);
}

describe("CompanyProvisionModal", () => {
  beforeEach(() => {
    mockUseProvisionCompany.mockReturnValue(mutationBase as never);
  });

  it("renderiza campos do formulário", () => {
    renderModal();
    expect(screen.getByText(/Nome da empresa \*/i)).toBeInTheDocument();
    expect(screen.getByText(/^Slug \*$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Nome \*$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Email \*$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Senha \*$/i)).toBeInTheDocument();
    // 3 text inputs + 1 email input
    expect(screen.getAllByRole("textbox")).toHaveLength(4);
    // 1 password input
    expect(document.querySelector("input[type=password]")).not.toBeNull();
  });

  it("slug é gerado automaticamente a partir do nome", async () => {
    const user = userEvent.setup();
    const { container } = renderModal();

    const nameInput = container.querySelectorAll("input[type=text]")[0];
    await user.type(nameInput, "Acme Corporation");

    const slugInput = container.querySelectorAll("input[type=text]")[1] as HTMLInputElement;
    expect(slugInput.value).toBe("acme-corporation");
  });

  it("slug normaliza caracteres especiais e acentos", async () => {
    const user = userEvent.setup();
    const { container } = renderModal();

    const nameInput = container.querySelectorAll("input[type=text]")[0];
    await user.type(nameInput, "Ação & Reação");

    const slugInput = container.querySelectorAll("input[type=text]")[1] as HTMLInputElement;
    expect(slugInput.value).toMatch(/^[a-z0-9-]+$/);
    expect(slugInput.value).not.toContain("&");
  });

  it("chama onClose ao clicar em Cancelar", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderModal(onClose);

    await user.click(screen.getByRole("button", { name: /cancelar/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("chama provision e fecha modal ao submeter com sucesso", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({ id: "new", name: "New Corp" });
    const onClose = vi.fn();
    mockUseProvisionCompany.mockReturnValue({ ...mutationBase, mutateAsync } as never);

    const { container } = renderModal(onClose);
    const textInputs = container.querySelectorAll("input[type=text]");
    const emailInput = container.querySelector("input[type=email]") as HTMLInputElement;
    const passwordInput = container.querySelector("input[type=password]") as HTMLInputElement;

    await user.type(textInputs[0], "New Corp");      // name
    await user.type(textInputs[2], "Admin User");    // admin_name
    await user.type(emailInput, "admin@new.com");
    await user.type(passwordInput, "securepass123");
    await user.click(screen.getByRole("button", { name: /provisionar/i }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledOnce();
      expect(onClose).toHaveBeenCalledOnce();
    });
  });

  it("exibe mensagem de erro quando provision falha", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockRejectedValue(new Error("Slug já em uso."));
    mockUseProvisionCompany.mockReturnValue({ ...mutationBase, mutateAsync } as never);

    const { container } = renderModal();
    const textInputs = container.querySelectorAll("input[type=text]");
    const emailInput = container.querySelector("input[type=email]") as HTMLInputElement;
    const passwordInput = container.querySelector("input[type=password]") as HTMLInputElement;

    await user.type(textInputs[0], "Dup Corp");
    await user.type(textInputs[2], "Admin");
    await user.type(emailInput, "a@b.com");
    await user.type(passwordInput, "securepass123");
    await user.click(screen.getByRole("button", { name: /provisionar/i }));

    await waitFor(() => {
      expect(screen.getByText(/Slug já em uso/i)).toBeInTheDocument();
    });
  });

  it("botão submit fica desabilitado durante pending", () => {
    mockUseProvisionCompany.mockReturnValue({
      ...mutationBase,
      isPending: true,
    } as never);

    renderModal();
    expect(screen.getByRole("button", { name: /provisionando/i })).toBeDisabled();
  });
});
