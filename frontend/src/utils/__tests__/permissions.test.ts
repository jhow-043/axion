import { describe, it, expect } from "vitest";
import { hasRole, hasMinRole, hasModule } from "@/utils/permissions";
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

describe("hasRole", () => {
  it("retorna true quando papel está na lista", () => {
    expect(hasRole(["admin", "supervisor"], ["admin", "supervisor"])).toBe(true);
  });

  it("retorna false quando papel não está na lista", () => {
    expect(hasRole(["requester"], ["admin", "supervisor"])).toBe(false);
  });
});

describe("hasMinRole", () => {
  it("admin tem pelo menos o papel de supervisor", () => {
    expect(hasMinRole(["admin"], "supervisor")).toBe(true);
  });

  it("requester não tem pelo menos o papel de technician", () => {
    expect(hasMinRole(["requester"], "technician")).toBe(false);
  });

  it("technician tem exatamente o papel de technician", () => {
    expect(hasMinRole(["technician"], "technician")).toBe(true);
  });
});

describe("hasModule", () => {
  it("retorna true quando módulo está na sessão", () => {
    expect(hasModule(makeSession(["manutencao"]), "manutencao")).toBe(true);
  });

  it("retorna false quando módulo não está na sessão", () => {
    expect(hasModule(makeSession([]), "manutencao")).toBe(false);
  });

  it("retorna false para sessão nula sem lançar erro", () => {
    expect(hasModule(null, "manutencao")).toBe(false);
  });
});
