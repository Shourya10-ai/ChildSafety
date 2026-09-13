import { WEBSOCKET_URL } from './api';

export type WebSocketEventHandler = (event: string, data: any) => void;

class RealtimeService {
  private ws: WebSocket | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private listeners: Set<WebSocketEventHandler> = new Set();
  private isConnecting = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  public connect() {
    if (typeof window === 'undefined') return;
    const token = localStorage.getItem('access_token');
    if (!token) {
      console.warn('[WebSocket] No access token found in localStorage.');
      return;
    }

    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isConnecting = true;
    const wsUrl = `${WEBSOCKET_URL}?token=${token}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected to Child Safety real-time feed');
        this.isConnecting = false;
        this.reconnectAttempts = 0;

        // Start ping every 30 seconds
        if (this.pingInterval) clearInterval(this.pingInterval);
        this.pingInterval = setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ action: 'ping' }));
          }
        }, 30000);
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.event === 'pong') return;
          this.notifyListeners(msg.event, msg.data || msg);
        } catch (e) {
          console.error('[WebSocket] Failed to parse message:', e);
        }
      };

      this.ws.onerror = (err) => {
        console.warn('[WebSocket] Error occurred:', err);
      };

      this.ws.onclose = () => {
        console.log('[WebSocket] Connection closed');
        this.isConnecting = false;
        if (this.pingInterval) clearInterval(this.pingInterval);

        // Exponential backoff reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
          setTimeout(() => this.connect(), delay);
        }
      };
    } catch (err) {
      console.error('[WebSocket] Connection failed:', err);
      this.isConnecting = false;
    }
  }

  public disconnect() {
    if (this.pingInterval) clearInterval(this.pingInterval);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  public subscribe(handler: WebSocketEventHandler) {
    this.listeners.add(handler);
    return () => {
      this.listeners.delete(handler);
    };
  }

  private notifyListeners(event: string, data: any) {
    this.listeners.forEach((handler) => handler(event, data));
  }
}

export const realtimeService = new RealtimeService();
