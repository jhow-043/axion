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

  it("manutencao tem 7 itens de menu", () => {
    const mod = MODULE_REGISTRY.find((m) => m.code === "manutencao")!;
    expect(mod.navItems).toHaveLength(7);
  });

  it("navItems do manutencao inclui Dashboard, Chamados, Equipamentos, Setores / Locais, Usuários, Relatórios e Administração", () => {
    const mod = MODULE_REGISTRY.find((m) => m.code === "manutencao")!;
    const labels = mod.navItems.map((n) => n.label);
    expect(labels).toContain("Dashboard");
    expect(labels).toContain("Chamados");
    expect(labels).toContain("Equipamentos");
    expect(labels).toContain("Setores / Locais");
    expect(labels).toContain("Usuários");
    expect(labels).toContain("Relatórios");
    expect(labels).toContain("Administração");
  });

  it("cada navItem tem to, label e icon preenchidos", () => {
    const mod = MODULE_REGISTRY.find((m) => m.code === "manutencao")!;
    for (const item of mod.navItems) {
      expect(item.to).toBeTruthy();
      expect(item.label).toBeTruthy();
      expect(item.icon).toBeTruthy();
    }
  });
});
