/**
 * Topbar component — breadcrumb, search, actions
 */

import { el } from '../utils.js';
import { getIcon } from '../icons.js';
import { store } from '../store.js';
import { router } from '../router.js';
import events from '../events.js';

const PAGE_TITLES = {
  '/dashboard': 'Dashboard',
  '/pipeline': 'Pipeline',
  '/videos': 'Videos',
  '/analytics': 'Analytics',
  '/logs': 'Logs',
  '/settings': 'Settings',
};

export function Topbar() {
  const topbar = el('header', { class: 'topbar' });

  // Left: mobile menu toggle + breadcrumb
  const left = el('div', { class: 'topbar__left' });

  const menuBtn = el('button', {
    class: 'topbar__icon-btn',
    style: { display: 'none' },
    html: getIcon('menu', 20),
  });
  menuBtn.addEventListener('click', () => {
    store.setState({ sidebarOpen: !store.state.sidebarOpen });
  });
  left.appendChild(menuBtn);

  const breadcrumb = el('div', { class: 'topbar__breadcrumb' });
  breadcrumb.innerHTML = `
    <span>AutoShortsAI</span>
    <span>›</span>
    <span class="topbar__page-title">${PAGE_TITLES['/dashboard']}</span>
  `;
  left.appendChild(breadcrumb);
  topbar.appendChild(left);

  // Center: search (command palette trigger)
  const center = el('div', { class: 'topbar__center' });
  const search = el('div', {
    class: 'topbar__search',
    role: 'button',
    tabindex: '0',
  });
  search.innerHTML = `
    <span style="color: var(--text-tertiary); display: flex;">${getIcon('search', 16)}</span>
    <input class="topbar__search-input" placeholder="Search or jump to..." readonly />
    <kbd class="topbar__search-kbd">⌘K</kbd>
  `;
  search.addEventListener('click', () => {
    events.emit('command-palette:open');
  });
  center.appendChild(search);
  topbar.appendChild(center);

  // Right: actions
  const right = el('div', { class: 'topbar__right' });

  const refreshBtn = el('button', {
    class: 'topbar__icon-btn',
    title: 'Refresh',
    html: getIcon('refresh', 18),
  });
  refreshBtn.addEventListener('click', () => {
    events.emit('page:refresh');
  });
  right.appendChild(refreshBtn);

  const bellBtn = el('button', {
    class: 'topbar__icon-btn',
    title: 'Notifications',
    html: getIcon('bell', 18),
  });
  right.appendChild(bellBtn);

  // WS status indicator
  const wsStatus = el('div', {
    class: 'topbar__icon-btn',
    title: 'WebSocket disconnected',
    style: { color: 'var(--status-failed)' },
    html: getIcon('globe', 18),
  });
  wsStatus.dataset.role = 'ws-status';
  right.appendChild(wsStatus);

  topbar.appendChild(right);

  // Show mobile menu button on small screens
  const updateMenuBtn = () => {
    menuBtn.style.display = window.innerWidth <= 1024 ? 'flex' : 'none';
  };
  updateMenuBtn();
  window.addEventListener('resize', updateMenuBtn);

  return topbar;
}

export function updateTopbarTitle(path) {
  const titleEl = document.querySelector('.topbar__page-title');
  if (titleEl) {
    titleEl.textContent = PAGE_TITLES[path] || 'AutoShortsAI';
  }
}

export function updateWSStatus(connected) {
  const wsStatus = document.querySelector('[data-role="ws-status"]');
  if (wsStatus) {
    wsStatus.style.color = connected ? 'var(--status-completed)' : 'var(--status-failed)';
    wsStatus.title = connected ? 'WebSocket connected' : 'WebSocket disconnected';
  }
}

export default Topbar;
