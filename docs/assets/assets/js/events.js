/**
 * Event Bus — lightweight pub/sub for component communication
 */

class EventBus {
  constructor() {
    this._listeners = new Map();
  }

  on(event, handler) {
    if (!this._listeners.has(event)) {
      this._listeners.set(event, new Set());
    }
    this._listeners.get(event).add(handler);
    return () => this.off(event, handler);
  }

  off(event, handler) {
    const set = this._listeners.get(event);
    if (set) set.delete(handler);
  }

  emit(event, payload) {
    const set = this._listeners.get(event);
    if (!set) return;
    for (const handler of set) {
      try {
        handler(payload);
      } catch (err) {
        console.error(`[EventBus] Error in handler for "${event}":`, err);
      }
    }
  }

  clear() {
    this._listeners.clear();
  }
}

export const events = new EventBus();
export default events;
