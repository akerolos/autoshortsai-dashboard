/**
 * WebSocket client with auto-reconnect and backoff
 */

import events from './events.js';
import { store } from './store.js';

class WSClient {
  constructor() {
    this.ws = null;
    this.url = null;
    this.topic = 'all';
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.heartbeatInterval = null;
    this.shouldReconnect = true;
  }

  connect(topic = 'all') {
    this.topic = topic;
    this.shouldReconnect = true;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.url = `${protocol}//${window.location.host}/ws/${topic}`;

    this._createSocket();
  }

  _createSocket() {
    try {
      this.ws = new WebSocket(this.url);
    } catch (err) {
      console.error('[WS] Failed to create socket:', err);
      this._scheduleReconnect();
      return;
    }

    this.ws.onopen = this._onOpen.bind(this);
    this.ws.onmessage = this._onMessage.bind(this);
    this.ws.onerror = this._onError.bind(this);
    this.ws.onclose = this._onClose.bind(this);
  }

  _onOpen() {
    console.log('[WS] Connected');
    this.reconnectAttempts = 0;
    store.setState({ wsConnected: true });
    events.emit('ws:connected');

    // Heartbeat
    this.heartbeatInterval = setInterval(() => {
      this.send({ type: 'ping' });
    }, 30000);
  }

  _onMessage(event) {
    try {
      const message = JSON.parse(event.data);
      const { type, data, topic } = message;

      // Emit global event
      events.emit(`ws:${type}`, data);
      // Emit topic-specific event
      if (topic) events.emit(`ws:${topic}:${type}`, data);
    } catch (err) {
      console.error('[WS] Failed to parse message:', err);
    }
  }

  _onError(err) {
    console.error('[WS] Error:', err);
  }

  _onClose(event) {
    console.log('[WS] Closed:', event.code, event.reason);
    store.setState({ wsConnected: false });
    events.emit('ws:disconnected');

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.shouldReconnect) {
      this._scheduleReconnect();
    }
  }

  _scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('[WS] Max reconnect attempts reached');
      events.emit('ws:failed');
      return;
    }

    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    setTimeout(() => {
      this.reconnectAttempts++;
      this._createSocket();
    }, delay);
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(typeof message === 'string' ? message : JSON.stringify(message));
      return true;
    }
    return false;
  }

  subscribe(topics) {
    this.send({ type: 'subscribe', topics: Array.isArray(topics) ? topics : [topics] });
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }
  }
}

export const ws = new WSClient();
export default ws;
