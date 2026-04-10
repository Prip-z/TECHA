import { useEffect, useRef, useState } from "react";

import { buildRoomSocketUrl } from "../lib/realtime";
import type { SyncEnvelope } from "../types/models";

export function useRealtimeRoom(roomId: string | null, token: string | null, onMessage: (message: SyncEnvelope) => void) {
  const socketRef = useRef<WebSocket | null>(null);
  const messageHandlerRef = useRef(onMessage);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    messageHandlerRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    if (!roomId || !token) {
      return;
    }

    const socket = new WebSocket(buildRoomSocketUrl(roomId, token));
    socketRef.current = socket;

    socket.addEventListener("open", () => setConnected(true));
    socket.addEventListener("close", () => setConnected(false));
    socket.addEventListener("message", (event) => {
      try {
        const parsed = JSON.parse(event.data) as SyncEnvelope;
        messageHandlerRef.current(parsed);
      } catch {
        return;
      }
    });

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [roomId, token]);

  function send(type: string, payload: unknown) {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }
    socketRef.current.send(JSON.stringify({ type, payload }));
  }

  return { connected, send };
}
