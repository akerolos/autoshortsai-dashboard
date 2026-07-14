/**
 * Sidebar component — main navigation
 */

import { el } from '../utils.js';
import { getIcon } from '../icons.js';
import { router } from '../router.js';
import { store } from '../store.js';

const NAV_ITEMS = [
  {
    section: 'Main',
    items: [
      { path: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
      { path: '/pipeline', label: 'Pipeline', icon: 'pipeline' },
      { path: '/videos', label: 'Videos', icon: 'videos' },
    ],
  },
  {
    section: 'Insights',
    items: [
      { path: '/analytics', label: 'Analytics', icon: 'analytics' },
      { path: '/logs', label: 'Logs', icon: 'logs' },
    ],
  },
  {
    section: 'System',
    items: [
      { path: '/settings', label: 'Settings', icon: 'settings' },
    ],
  },
];

export function Sidebar() {
  const sidebar = el('aside', { class: 'sidebar' });

  // Header
  const header = el('div', { class: 'sidebar__header' });
  header.innerHTML = `
    <div class="sidebar__logo">${getIcon('rocket', 18)}</div>
    <div class="sidebar__brand">
      <span class="sidebar__brand-name">AutoShortsAI</span>
      <span class="sidebar__brand-sub">Mission Control</span>
    </div>
  `;
  sidebar.appendChild(header);

  // Nav
  const nav = el('nav', { class: 'sidebar__nav' });
  NAV_ITEMS.forEach((section) => {
    nav.appendChild(el('div', { class: 'sidebar__label-section' }, section.section));
    section.items.forEach((item) => {
      const navItem = el('div', {
        class: 'nav-item',
        dataset: { path: item.path },
      });
      navItem.innerHTML = `
        <span class="nav-item__icon">${getIcon(item.icon, 18)}</span>
        <span class="nav-item__label">${item.label}</span>
      `;
      navItem.addEventListener('click', () => {
        router.navigate(item.path);
        // Close sidebar on mobile
        store.setState({ sidebarOpen: false });
      });
      nav.appendChild(navItem);
    });
  });
  sidebar.appendChild(nav);

  // Footer — system status
  const footer = el('div', { class: 'sidebar__footer' });
  footer.innerHTML = `
    <div class="sidebar__footer-content">
      <span class="sidebar__status-dot"></span>
      <div class="sidebar__status-text">
        <strong>System Online</strong>
        <span>v1.0.0</span>
      </div>
    </div>
  `;
  sidebar.appendChild(footer);

  return sidebar;
}

export function updateActiveNav(path) {
  document.querySelectorAll('.nav-item').forEach((item) => {
    if (item.dataset.path === path) {
      item.classList.add('is-active');
    } else {
      item.classList.remove('is-active');
    }
  });
}

export default Sidebar;
