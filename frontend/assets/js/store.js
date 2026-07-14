/**
 * Reactive Store — minimal Redux-like state management
 */

class Store {
  constructor(initialState = {}) {
    this._state = { ...initialState };
    this._listeners = new Set();
  }

  get state() {
    return this._state;
  }

  setState(partial) {
    const prev = this._state;
    this._state = { ...this._state, ...partial };
    this._notify(prev, this._state);
  }

  subscribe(listener) {
    this._listeners.add(listener);
    return () => this._listeners.delete(listener);
  }

  _notify(prev, next) {
    for (const listener of this._listeners) {
      try {
        listener(next, prev);
      } catch (err) {
        console.error('[Store] Listener error:', err);
      }
    }
  }
}

export const store = new Store({
  // حالة الـ UI
  currentPage: 'dashboard',
  sidebarCollapsed: false,
  sidebarOpen: false,
  commandPaletteOpen: false,
  theme: 'dark',

  // البيانات
  dashboard: null,
  pipeline: null,
  videos: null,
  analytics: null,
  settings: null,
  logs: null,

  // حالة الاتصال
  wsConnected: false,
  loading: {},
});

export default store;
