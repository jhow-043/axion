import { describe, it, expect } from "vitest";
import { MODULE_REGISTRY } from "../modules";

describe("MODULE_REGISTRY", () => {
  it("contém a entrada manutencao", () => {
    const mod = MODULE_REGISTRY.find((m) => m.code === "manutencao");
    expect(mod).toBeDefined();
  });

  it("entrada manutencao tem todos os campos obrigatórios", () => {
    const mod = MODULE_REGISTRY.find((m) => m.code === "manutencao")!;
    expect(mod.label).toBeTruthy();
    expect(mod.description).toBeTruthy();
    expect(mod.icon).toBeTruthy();
    expect(mod.homeRoute).toBeTruthy();
  });

  it("homeRoute do manutencao é /dashboard", () => {
    const mod = MODULE_REGISTRY.find((m) => m.code === "manutencao")!;
    expect(mod.homeRoute).toBe("/dashboard");
  });
});
