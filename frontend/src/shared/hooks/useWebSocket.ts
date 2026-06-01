import { useEffect, useState } from "react";
import { wsClient, type WsStatus } from "@/shared/ws/client";

export function useWebSocket(channel: string | null) {
  const [status, setStatus] = useState<WsStatus>("disconnected");

  useEffect(() => {
    if (!channel) return;

    wsClient.connect(channel);
    const unsubStatus = wsClient.onStatus(setStatus);

    return () => {
      unsubStatus();
      wsClient.disconnect();
    };
  }, [channel]);

  return { status };
}
