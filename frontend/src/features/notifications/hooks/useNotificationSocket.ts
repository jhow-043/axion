import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { env } from "@/config/env";
import { getAccessToken } from "@/shared/api/client";
import type { Notification } from "../types";

/**
 * Connects to the WebSocket notification endpoint and invalidates the
 * notification query cache when a push arrives, keeping the bell counter
 * up-to-date in real time.
 *
 * Reconnects automatically on unexpected disconnect (exponential backoff,
 * capped at 30s).
 */
export function useNotificationSocket() {
  const qc = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryDelayRef = useRef(1000);

  useEffect(() => {
    let stopped = false;

    function connect() {
      const token = getAccessToken();
      if (!token) return;

      const url = `${env.wsBaseUrl}/ws/notifications?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data as string) as {
            type: string;
            data: Notification;
          };
          if (msg.type === "notification") {
            qc.invalidateQueries({ queryKey: ["notifications"] });
          }
        } catch {
          // ignore malformed messages
        }
      };

      ws.onclose = () => {
        if (stopped) return;
        // Exponential backoff reconnect
        retryTimeoutRef.current = setTimeout(() => {
          retryDelayRef.current = Math.min(retryDelayRef.current * 2, 30_000);
          connect();
        }, retryDelayRef.current);
      };

      ws.onopen = () => {
        retryDelayRef.current = 1000; // reset on successful connect
      };
    }

    connect();

    return () => {
      stopped = true;
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [qc]);
}
