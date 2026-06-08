import { describe, it, expect } from "vitest";
import { formatDate, formatDateTime, formatDistanceToNow } from "@/utils/dates";

describe("formatDate", () => {
  it("formata ISO UTC no padrão dd/mm/aaaa", () => {
    const result = formatDate("2026-06-01T00:00:00Z");
    expect(result).toMatch(/\d{2}\/\d{2}\/\d{4}/);
  });
});

describe("formatDateTime", () => {
  it("formata ISO UTC no padrão dd/mm/aaaa hh:mm", () => {
    const result = formatDateTime("2026-06-01T14:30:00Z");
    expect(result).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    expect(result).toMatch(/\d{2}:\d{2}/);
  });
});

describe("formatDistanceToNow", () => {
  const now = new Date("2026-06-08T12:00:00Z");

  it("formata prazo futuro em minutos", () => {
    const result = formatDistanceToNow(new Date("2026-06-08T12:30:00Z"), now);
    expect(result).toBe("em 30 minutos");
  });

  it("formata prazo passado em horas", () => {
    const result = formatDistanceToNow(new Date("2026-06-08T10:00:00Z"), now);
    expect(result).toBe("há 2 horas");
  });
});
