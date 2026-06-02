import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { WsStatus } from "@/shared/ws/client";

const mockConnect = vi.fn();
const mockDisconnect = vi.fn();
let statusHandler: ((s: WsStatus) => void) | null = null;

vi.mock("@/shared/ws/client", () => ({
  wsClient: {
    connect: mockConnect,
    disconnect: mockDisconnect,
    onStatus: vi.fn((handler: (s: WsStatus) => void) => {
      statusHandler = handler;
      return () => { statusHandler = null; };
    }),
  },
}));

// import after mock is set up
const { useWebSocket } = await import("@/shared/hooks/useWebSocket");

describe("useWebSocket", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    statusHandler = null;
  });

  afterEach(() => {
    statusHandler = null;
  });

  it("chama connect com o canal ao montar", () => {
    renderHook(() => useWebSocket("notifications"));
    expect(mockConnect).toHaveBeenCalledWith("notifications");
  });

  it("não conecta quando channel é null", () => {
    renderHook(() => useWebSocket(null));
    expect(mockConnect).not.toHaveBeenCalled();
  });

  it("retorna status inicial 'disconnected'", () => {
    const { result } = renderHook(() => useWebSocket("notifications"));
    expect(result.current.status).toBe("disconnected");
  });

  it("atualiza status quando o cliente emite mudança", () => {
    const { result } = renderHook(() => useWebSocket("notifications"));
    act(() => statusHandler?.("connected"));
    expect(result.current.status).toBe("connected");
  });

  it("chama disconnect ao desmontar", () => {
    const { unmount } = renderHook(() => useWebSocket("notifications"));
    unmount();
    expect(mockDisconnect).toHaveBeenCalledOnce();
  });
});
