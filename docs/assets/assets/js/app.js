/**
 * AutoShortsAI Dashboard — Application bootstrap
 */

import { el } from './utils.js';
import { router } from './router.js';
import { store } from './store.js';
import events from './events.js';
import { ws } from './ws.js';
import { Sidebar, updateActiveNav } from './components/Sidebar.js';
import { Topbar, updateTopbarTitle, updateWSStatus } from './components/Topbar.js';
import { commandPalette } from './components/CommandPalette.js';
import toast from './components/Toast.js';

// Page imports
const pageLoaders = {
  '/dashboard': () => import('./pages/DashboardPage.js'),
  '/pipeline': () => import('./pages/PipelinePage.js'),
  '/videos': () => import('./pages/VideosPage.js'),
  '/analytics': () => import('./pages/AnalyticsPage.js'),
  '/logs': () => import('./pages/LogsPage.js'),
  '/settings': () => import('./pages/SettingsPage.js'),
};

function initApp() {
  const app = document.getElementById('app');
  if (!app) return;

  // Clear any loading placeholders
  app.innerHTML = '';

  // Build app shell
  const shell = el('div', { class: 'app-shell' });

  // Sidebar backdrop (mobile)
  const backdrop = el('div', { class: 'sidebar-backdrop' });
  backdrop.addEventListener('click', () => store.setState({ sidebarOpen: false }));
  shell.appendChild(backdrop);

  // Sidebar
  shell.appendChild(Sidebar());

  // Topbar
  shell.appendChild(Topbar());

  // Main content
  const main = el('main', { class: 'main' });
  const pageContent = el('div', { id: 'page-content' });
  main.appendChild(pageContent);
  shell.appendChild(main);

  app.appendChild(shell);

  // Setup router with lazy-loaded pages
  Object.entries(pageLoaders).forEach(([path, loader]) => {
    router.addRoute(path, loader);
  });

  router.start();

  // Update nav active state on route change
  events.on('route:change', ({ path }) => {
    updateActiveNav(path);
    updateTopbarTitle(path);
  });

  // Update sidebar state
  store.subscribe((state, prev) => {
    const shellEl = document.querySelector('.app-shell');
    if (!shellEl) return;

    if (state.sidebarCollapsed !== prev.sidebarCollapsed) {
      shellEl.classList.toggle('sidebar-collapsed', state.sidebarCollapsed);
    }
    if (state.sidebarOpen !== prev.sidebarOpen) {
      shellEl.classList.toggle('sidebar-open', state.sidebarOpen);
    }
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // Toggle sidebar (Ctrl/Cmd + B)
    if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
      e.preventDefault();
      store.setState({ sidebarCollapsed: !store.state.sidebarCollapsed });
    }
  });

  // Initialize command palette
  commandPalette.init();

  // Connect WebSocket (في live mode فقط — يعني لما السيرفر بيشتغل على بورت 8000)
  // إحنا بنكتشف الـ static mode بـ: مفيش /api/v1/ متاح، أو على github.io، أو مع static=true
  const isStatic = window.location.hostname.includes('github.io') ||
                   window.location.search.includes('static=true') ||
                   window.location.port === '' ||
                   window.location.port === '80' ||
                   window.location.port === '8080' ||
                   window.location.port === '5500';

  if (!isStatic) {
    ws.connect('all');

    // Update WS status indicator
    events.on('ws:connected', () => updateWSStatus(true));
    events.on('ws:disconnected', () => updateWSStatus(false));
  } else {
    // Static mode — مفيش WebSocket
    console.log('[App] Static mode — WebSocket disabled');
    updateWSStatus(false);
  }

  // Welcome toast
  setTimeout(() => {
    toast.success('Welcome back!', 'AutoShortsAI Dashboard is ready. Press ⌘K for commands.');
  }, 500);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

export default { initApp };
