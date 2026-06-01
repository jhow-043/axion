import { env } from "@/config/env";
import {
  WS_RECONNECT_BASE_DELAY_MS,
  WS_RECONNECT_MAX_DELAY_MS,
  WS_RECONNECT_MAX_ATTEMPTS,
} from "@/config/constants";

type MessageHandler = (data: unknown) => void;
type StatusHandler = (status: WsStatus) => void;

export type WsStatus = "connecting" | "connected" | "disconnected" | "failed";

export class WsClient {
  private ws: WebSocket | null = null;
  private channel: string | null = null;
  private attempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private messageHandlers = new Set<MessageHandler>();
  private statusHandlers = new Set<StatusHandler>();
  private intentionallyClosed = false;

  connect(channel: string): void {
    this.intentionallyClosed = false;
    this.channel = channel;
    this.attempts = 0;
    this.open();
  }

  disconnect(): void {
    this.intentionallyClosed = true;
    this.clearReconnectTimer();
    this.ws?.close();
    this.ws = null;
    this.emitStatus("disconnected");
  }

  subscribe(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onStatus(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }

  private open(): void {
    if (!this.channel) return;
    const url = `${env.wsBaseUrl}/ws/${this.channel}`;
    this.emitStatus("connecting");

    try {
      this.ws = new WebSocket(url);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.attempts = 0;
      this.emitStatus("connected");
    };

    this.ws.onmessage = (event: MessageEvent<string>) => {
      try {
        const data: unknown = JSON.parse(event.data);
        this.messageHandlers.forEach((h) => h(data));
      } catch {
        // mensagem não-JSON ignorada silenciosamente
      }
    };

    this.ws.onclose = () => {
      if (!this.intentionallyClosed) this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      // onclose sempre é chamado após onerror — reconexão tratada lá
    };
  }

  private scheduleReconnect(): void {
    if (this.attempts >= WS_RECONNECT_MAX_ATTEMPTS) {
      this.emitStatus("failed");
      return;
    }
    this.emitStatus("disconnected");
    const delay = Math.min(
      WS_RECONNECT_BASE_DELAY_MS * 2 ** this.attempts,
      WS_RECONNECT_MAX_DELAY_MS,
    );
    this.attempts++;
    this.reconnectTimer = setTimeout(() => this.open(), delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private emitStatus(status: WsStatus): void {
    this.statusHandlers.forEach((h) => h(status));
  }
}

export const wsClient = new WsClient();
