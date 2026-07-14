/**
 * Command Palette — Cmd+K search and navigation
 */

import { el } from '../utils.js';
import { getIcon } from '../icons.js';
import { router } from '../router.js';
import { store } from '../store.js';
import events from '../events.js';

const COMMANDS = [
  { group: 'Navigation', label: 'Go to Dashboard', icon: 'dashboard', shortcut: 'G D', action: () => router.navigate('/dashboard') },
  { group: 'Navigation', label: 'Go to Pipeline', icon: 'pipeline', shortcut: 'G P', action: () => router.navigate('/pipeline') },
  { group: 'Navigation', label: 'Go to Videos', icon: 'videos', shortcut: 'G V', action: () => router.navigate('/videos') },
  { group: 'Navigation', label: 'Go to Analytics', icon: 'analytics', shortcut: 'G A', action: () => router.navigate('/analytics') },
  { group: 'Navigation', label: 'Go to Logs', icon: 'logs', shortcut: 'G L', action: () => router.navigate('/logs') },
  { group: 'Navigation', label: 'Go to Settings', icon: 'settings', shortcut: 'G S', action: () => router.navigate('/settings') },
  { group: 'Actions', label: 'Refresh Current Page', icon: 'refresh', shortcut: 'R', action: () => events.emit('page:refresh') },
  { group: 'Actions', label: 'Toggle Sidebar', icon: 'menu', shortcut: '⌘B', action: () => store.setState({ sidebarCollapsed: !store.state.sidebarCollapsed }) },
];

export class CommandPalette {
  constructor() {
    this.isOpen = false;
    this.selectedIndex = 0;
    this.filteredCommands = [...COMMANDS];
    this.element = null;
  }

  init() {
    // Keyboard shortcut
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        this.toggle();
      }
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });

    events.on('command-palette:open', () => this.open());
  }

  toggle() {
    if (this.isOpen) this.close();
    else this.open();
  }

  open() {
    if (this.isOpen) return;
    this.isOpen = true;
    this.selectedIndex = 0;
    this.filteredCommands = [...COMMANDS];
    this._render();
  }

  close() {
    if (!this.isOpen) return;
    this.isOpen = false;
    if (this.element) {
      this.element.remove();
      this.element = null;
    }
  }

  _render() {
    this.element = el('div', { class: 'command-palette' });

    // Input
    const input = el('input', {
      class: 'command-palette__input',
      placeholder: 'Type a command or search...',
      autocomplete: 'off',
    });
    input.addEventListener('input', (e) => this._filter(e.target.value));
    input.addEventListener('keydown', (e) => this._onKeyDown(e));
    this.element.appendChild(input);

    // Results
    this.resultsEl = el('div', { class: 'command-palette__results' });
    this.element.appendChild(this.resultsEl);
    this._renderResults();

    // Backdrop
    const backdrop = el('div', {
      class: 'modal-backdrop',
      style: { alignItems: 'flex-start' },
    });
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) this.close();
    });
    backdrop.appendChild(this.element);
    document.body.appendChild(backdrop);
    this.backdrop = backdrop;

    // Focus input
    setTimeout(() => input.focus(), 50);
  }

  _filter(query) {
    const q = query.toLowerCase().trim();
    if (!q) {
      this.filteredCommands = [...COMMANDS];
    } else {
      this.filteredCommands = COMMANDS.filter(c =>
        c.label.toLowerCase().includes(q) || c.group.toLowerCase().includes(q)
      );
    }
    this.selectedIndex = 0;
    this._renderResults();
  }

  _renderResults() {
    this.resultsEl.innerHTML = '';
    if (this.filteredCommands.length === 0) {
      this.resultsEl.innerHTML = '<div class="command-palette__empty">No commands found</div>';
      return;
    }

    let currentGroup = '';
    this.filteredCommands.forEach((cmd, idx) => {
      if (cmd.group !== currentGroup) {
        currentGroup = cmd.group;
        this.resultsEl.appendChild(el('div', { class: 'command-palette__group' }, currentGroup));
      }
      const item = el('div', {
        class: `command-palette__item ${idx === this.selectedIndex ? 'is-selected' : ''}`,
        dataset: { index: idx },
      });
      item.innerHTML = `
        <span class="command-palette__item-icon">${getIcon(cmd.icon, 16)}</span>
        <span class="command-palette__item-label">${cmd.label}</span>
        ${cmd.shortcut ? `<span class="command-palette__item-shortcut">${cmd.shortcut}</span>` : ''}
      `;
      item.addEventListener('click', () => this._execute(idx));
      this.resultsEl.appendChild(item);
    });
  }

  _onKeyDown(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      this.selectedIndex = Math.min(this.selectedIndex + 1, this.filteredCommands.length - 1);
      this._renderResults();
      this._scrollToSelected();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
      this._renderResults();
      this._scrollToSelected();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      this._execute(this.selectedIndex);
    }
  }

  _scrollToSelected() {
    const selected = this.resultsEl.querySelector('.is-selected');
    if (selected) {
      selected.scrollIntoView({ block: 'nearest' });
    }
  }

  _execute(idx) {
    const cmd = this.filteredCommands[idx];
    if (cmd && typeof cmd.action === 'function') {
      cmd.action();
      this.close();
    }
  }
}

export const commandPalette = new CommandPalette();
export default commandPalette;
