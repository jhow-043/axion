import { describe, it, expect } from "vitest";
import { hasRole, hasMinRole } from "@/utils/permissions";

describe("hasRole", () => {
  it("retorna true quando papel está na lista", () => {
    expect(hasRole("admin", ["admin", "supervisor"])).toBe(true);
  });

  it("retorna false quando papel não está na lista", () => {
    expect(hasRole("requester", ["admin", "supervisor"])).toBe(false);
  });
});

describe("hasMinRole", () => {
  it("admin tem pelo menos o papel de supervisor", () => {
    expect(hasMinRole("admin", "supervisor")).toBe(true);
  });

  it("requester não tem pelo menos o papel de technician", () => {
    expect(hasMinRole("requester", "technician")).toBe(false);
  });

  it("technician tem exatamente o papel de technician", () => {
    expect(hasMinRole("technician", "technician")).toBe(true);
  });
});
