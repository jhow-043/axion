import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { WsClient } from "../client";

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  readyState = 0;
  url: string;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  close() {
    this.readyState = 3;
    this.onclose?.();
  }

  simulateOpen() {
    this.readyState = 1;
    this.onopen?.();
  }

  simulateMessage(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  simulateClose() {
    this.readyState = 3;
    this.onclose?.();
  }
}

describe("WsClient", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("emite status 'connecting' ao conectar", () => {
    const statusSpy = vi.fn();
    const client = new WsClient();
    client.onStatus(statusSpy);
    client.connect("notifications");
    expect(statusSpy).toHaveBeenCalledWith("connecting");
  });

  it("emite status 'connected' quando WebSocket abre", () => {
    const statusSpy = vi.fn();
    const client = new WsClient();
    client.onStatus(statusSpy);
    client.connect("notifications");

    MockWebSocket.instances[0]!.simulateOpen();
    expect(statusSpy).toHaveBeenCalledWith("connected");
  });

  it("entrega mensagens JSON recebidas aos handlers", () => {
    const msgSpy = vi.fn();
    const client = new WsClient();
    client.subscribe(msgSpy);
    client.connect("notifications");

    MockWebSocket.instances[0]!.simulateOpen();
    MockWebSocket.instances[0]!.simulateMessage({ type: "ping" });
    expect(msgSpy).toHaveBeenCalledWith({ type: "ping" });
  });

  it("reconecta com backoff após queda", () => {
    const statusSpy = vi.fn();
    const client = new WsClient();
    client.onStatus(statusSpy);
    client.connect("notifications");

    MockWebSocket.instances[0]!.simulateOpen();
    MockWebSocket.instances[0]!.simulateClose();

    expect(statusSpy).toHaveBeenCalledWith("disconnected");
    vi.advanceTimersByTime(1000);
    expect(MockWebSocket.instances).toHaveLength(2);
  });

  it("desconecta sem reconectar quando disconnect() é chamado", () => {
    const client = new WsClient();
    client.connect("notifications");
    MockWebSocket.instances[0]!.simulateOpen();
    client.disconnect();

    vi.advanceTimersByTime(5000);
    expect(MockWebSocket.instances).toHaveLength(1);
  });
});
