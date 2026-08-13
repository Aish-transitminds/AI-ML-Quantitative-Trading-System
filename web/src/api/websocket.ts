/**
 * WebSocket client with automatic reconnection.
 * Receives real-time state updates from the backend.
 */
import { WS_URL } from '../utils/constants';

type MessageHandler = (data: any) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: Set<MessageHandler> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private _connected = false;
  private _reconnectAttempts = 0;
  private _maxReconnectAttempts = 50;
  private _reconnectDelay = 2000;

  get connected() { return this._connected; }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    
    try {
      this.ws = new WebSocket(WS_URL);

      this.ws.onopen = () => {
        this._connected = true;
        this._reconnectAttempts = 0;
        console.log('[WS] Connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handlers.forEach(h => h(data));
        } catch (e) {
          console.warn('[WS] Parse error:', e);
        }
      };

      this.ws.onclose = () => {
        this._connected = false;
        console.log('[WS] Disconnected');
        this._scheduleReconnect();
      };

      this.ws.onerror = () => {
        this._connected = false;
      };
    } catch (e) {
      console.warn('[WS] Connection error:', e);
      this._scheduleReconnect();
    }
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this._connected = false;
  }

  subscribe(handler: MessageHandler) {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  private _scheduleReconnect() {
    if (this._reconnectAttempts >= this._maxReconnectAttempts) return;
    this._reconnectAttempts++;
    const delay = Math.min(this._reconnectDelay * this._reconnectAttempts, 15000);
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }
}

export const wsClient = new WebSocketClient();
