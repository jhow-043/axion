import { act, renderHook } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { usePagination } from "@/shared/hooks/usePagination";

describe("usePagination", () => {
  it("inicia na página 1 com o pageSize padrão (20)", () => {
    const { result } = renderHook(() => usePagination());
    expect(result.current.page).toBe(1);
    expect(result.current.pageSize).toBe(20);
  });

  it("aceita pageSize inicial customizado", () => {
    const { result } = renderHook(() => usePagination(50));
    expect(result.current.pageSize).toBe(50);
  });

  it("setPage atualiza a página", () => {
    const { result } = renderHook(() => usePagination());
    act(() => result.current.setPage(3));
    expect(result.current.page).toBe(3);
  });

  it("setPageSize atualiza o tamanho e reseta para página 1", () => {
    const { result } = renderHook(() => usePagination());
    act(() => result.current.setPage(5));
    act(() => result.current.setPageSize(10));
    expect(result.current.pageSize).toBe(10);
    expect(result.current.page).toBe(1);
  });

  it("reset volta à página 1 e ao pageSize inicial", () => {
    const { result } = renderHook(() => usePagination(30));
    act(() => {
      result.current.setPage(4);
      result.current.setPageSize(5);
    });
    act(() => result.current.reset());
    expect(result.current.page).toBe(1);
    expect(result.current.pageSize).toBe(30);
  });
});
