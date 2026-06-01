import { describe, it, expect } from "vitest";
import { formatDate, formatDateTime } from "@/utils/dates";

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
