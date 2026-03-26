import { useState, useEffect, useCallback, useRef } from "react";

interface WsMessage {
  type: string;
  step?: string;
  message?: string;
  content?: string;
}

interface UseWebSocketReturn {
  send: (data: Record<string, unknown>) => void;
  messages: WsMessage[];
  status: "connected" | "disconnected" | "reconnecting";
  clearMessages: () => void;
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [messages, setMessages] = useState<WsMessage[]>([]);
  const [status, setStatus] = useState<UseWebSocketReturn["status"]>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);

  const connect = useCallback(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      retryRef.current = 0;
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as WsMessage;
      setMessages((prev) => [...prev, data]);
    };

    ws.onclose = () => {
      setStatus("reconnecting");
      const delay = Math.min(1000 * 2 ** retryRef.current, 30000);
      retryRef.current++;
      setTimeout(connect, delay);
    };

    ws.onerror = () => ws.close();
  }, [url]);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const clearMessages = useCallback(() => setMessages([]), []);

  return { send, messages, status, clearMessages };
}
