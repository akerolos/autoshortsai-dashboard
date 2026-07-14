/**
 * Hash-based router with lazy page loading
 */

import events from './events.js';
import { store } from './store.js';

class Router {
  constructor(routes = {}) {
    this.routes = routes;
    this.currentPage = null;
    this.currentCleanup = null;
  }

  start() {
    window.addEventListener('hashchange', () => this._handleRoute());
    this._handleRoute();
  }

  navigate(path) {
    if (window.location.hash !== `#${path}`) {
      window.location.hash = path;
    } else {
      this._handleRoute();
    }
  }

  addRoute(path, loader) {
    this.routes[path] = loader;
  }

  async _handleRoute() {
    const hash = window.location.hash.slice(1) || '/dashboard';
    const [path] = hash.split('?');

    // Match route (exact or with params)
    let matchedRoute = null;
    let params = {};

    for (const routePath of Object.keys(this.routes)) {
      const match = this._matchRoute(routePath, path);
      if (match) {
        matchedRoute = routePath;
        params = match;
        break;
      }
    }

    if (!matchedRoute) {
      // Default to dashboard
      matchedRoute = '/dashboard';
    }

    // Cleanup previous page
    if (this.currentCleanup) {
      try {
        this.currentCleanup();
      } catch (err) {
        console.error('[Router] Cleanup error:', err);
      }
      this.currentCleanup = null;
    }

    store.setState({ currentPage: matchedRoute });

    const main = document.querySelector('#page-content');
    if (!main) return;

    // Clear and show loading
    main.innerHTML = '<div class="main__inner"><div class="spinner spinner--lg spinner--center"></div></div>';

    try {
      const loader = this.routes[matchedRoute];
      if (loader) {
        const pageModule = await loader();
        const page = pageModule.default || pageModule;
        this.currentPage = page;
        if (typeof page.render === 'function') {
          main.innerHTML = '';
          const rendered = page.render(params);
          if (rendered) main.appendChild(rendered);
          if (typeof page.mount === 'function') {
            this.currentCleanup = page.mount(params) || null;
          }
        }
      }
    } catch (err) {
      console.error('[Router] Page load error:', err);
      main.innerHTML = `
        <div class="main__inner">
          <div class="empty-state">
            <div class="empty-state__icon">${'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'}</div>
            <div class="empty-state__title">Failed to load page</div>
            <div class="empty-state__description">${err.message || 'Unknown error'}</div>
          </div>
        </div>
      `;
    }

    events.emit('route:change', { path: matchedRoute, params });
  }

  _matchRoute(routePath, actualPath) {
    const routeParts = routePath.split('/').filter(Boolean);
    const actualParts = actualPath.split('/').filter(Boolean);

    if (routeParts.length !== actualParts.length) return null;

    const params = {};
    for (let i = 0; i < routeParts.length; i++) {
      if (routeParts[i].startsWith(':')) {
        params[routeParts[i].slice(1)] = decodeURIComponent(actualParts[i]);
      } else if (routeParts[i] !== actualParts[i]) {
        return null;
      }
    }
    return params;
  }
}

export const router = new Router();
export default router;
