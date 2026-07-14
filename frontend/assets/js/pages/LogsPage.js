/**
 * Logs Page — real-time log viewer with filters
 */

import { el, formatDateTime, copyToClipboard, downloadBlob } from '../utils.js';
import { getIcon } from '../icons.js';
import { logsApi } from '../api.js';
import Card from '../components/Card.js';
import Badge from '../components/Badge.js';
import { LogLevelBadge } from '../components/Badge.js';
import toast from '../components/Toast.js';
import events from '../events.js';
import { debounce } from '../utils.js';

let refreshHandler = null;
let wsHandlers = [];
let currentFilters = {
  level: '',
  source: '',
  search: '',
};
let currentPage = 1;
let allLogs = [];
let autoScroll = true;
let logList = null;

export function render() {
  const main = el('div');
  main.innerHTML = `
    <div class="main__inner" style="height: calc(100vh - var(--topbar-height)); display: flex; flex-direction: column; gap: var(--space-4);">
      <div class="page-header" style="flex-shrink: 0;">
        <div class="page-header__title">
          <h1>Logs</h1>
          <span class="page-header__subtitle">Real-time system logs and events</span>
        </div>
        <div class="page-header__actions">
          <button class="btn btn--secondary btn--sm" id="download-btn">
            ${getIcon('download', 16)}
            <span>Download</span>
          </button>
          <button class="btn btn--secondary btn--sm" id="autoscroll-btn" data-active="true">
            ${getIcon('chevronDown', 16)}
            <span>Auto-scroll</span>
          </button>
        </div>
      </div>

      <div class="logs__container">
        <div class="logs__header">
          <div class="filter-bar__search" style="flex: 1; min-width: 200px;">
            <span class="filter-bar__search-icon">${getIcon('search', 14)}</span>
            <input type="text" id="search-input" placeholder="Search logs..." />
          </div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn--ghost btn--sm log-level-btn" data-level="">All</button>
            <button class="btn btn--ghost btn--sm log-level-btn" data-level="INFO">Info</button>
            <button class="btn btn--ghost btn--sm log-level-btn" data-level="SUCCESS">Success</button>
            <button class="btn btn--ghost btn--sm log-level-btn" data-level="WARNING">Warning</button>
            <button class="btn btn--ghost btn--sm log-level-btn" data-level="ERROR">Error</button>
          </div>
          <select class="filter-bar__select" id="source-filter" style="width: 160px;">
            <option value="">All Sources</option>
          </select>
        </div>
        <div class="logs__list" id="logs-list"></div>
      </div>

      <div id="logs-pagination" style="flex-shrink: 0;"></div>
    </div>
  `;
  return main;
}

export async function mount() {
  logList = document.getElementById('logs-list');

  // Filters
  document.getElementById('search-input')?.addEventListener('input', debounce((e) => {
    currentFilters.search = e.target.value;
    currentPage = 1;
    loadLogs();
  }, 300));

  document.querySelectorAll('.log-level-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.log-level-btn').forEach(b => {
        b.classList.remove('btn--secondary');
        b.classList.add('btn--ghost');
      });
      btn.classList.remove('btn--ghost');
      btn.classList.add('btn--secondary');
      currentFilters.level = btn.dataset.level;
      currentPage = 1;
      loadLogs();
    });
  });

  document.getElementById('source-filter')?.addEventListener('change', (e) => {
    currentFilters.source = e.target.value;
    currentPage = 1;
    loadLogs();
  });

  // Auto-scroll toggle
  document.getElementById('autoscroll-btn')?.addEventListener('click', (e) => {
    autoScroll = !autoScroll;
    e.currentTarget.dataset.active = autoScroll;
    e.currentTarget.style.opacity = autoScroll ? '1' : '0.5';
  });

  // Download
  document.getElementById('download-btn')?.addEventListener('click', downloadLogs);

  // Load sources for filter
  try {
    const sourcesResp = await logsApi.getSources();
    if (sourcesResp.success) {
      const select = document.getElementById('source-filter');
      sourcesResp.data.forEach(src => {
        const opt = document.createElement('option');
        opt.value = src;
        opt.textContent = src;
        select.appendChild(opt);
      });
    }
  } catch {}

  await loadLogs();

  // WebSocket for new logs
  wsHandlers.push(
    events.on('ws:log_new', (logEntry) => {
      addLogEntry(logEntry);
    })
  );

  refreshHandler = () => loadLogs();
  events.on('page:refresh', refreshHandler);

  return () => {
    if (refreshHandler) events.off('page:refresh', refreshHandler);
    wsHandlers.forEach(u => u && u());
    wsHandlers = [];
  };
}

async function loadLogs() {
  try {
    const response = await logsApi.list({
      page: currentPage,
      page_size: 100,
      ...currentFilters,
    });

    if (response.success) {
      allLogs = response.data.items;
      renderLogs(allLogs);
      renderPagination(response.data.pagination);
    }
  } catch (err) {
    toast.error('Failed to load logs', err.error?.message || 'Unknown error');
  }
}

function renderLogs(logs) {
  if (!logList) return;
  logList.innerHTML = '';

  if (logs.length === 0) {
    logList.innerHTML = `
      <div class="empty-state" style="padding: var(--space-12);">
        <div class="empty-state__icon">${getIcon('logs', 48)}</div>
        <div class="empty-state__title">No logs found</div>
        <div class="empty-state__description">Try adjusting your filters.</div>
      </div>
    `;
    return;
  }

  logs.forEach(log => {
    logList.appendChild(createLogEntry(log));
  });

  if (autoScroll) {
    logList.scrollTop = 0; // Newest first, scroll to top
  }
}

function createLogEntry(log) {
  const entry = el('div', { class: 'logs__entry', dataset: { id: log.id } });
  entry.innerHTML = `
    <span class="logs__entry-time">${formatDateTime(log.created_at)}</span>
    <span class="logs__entry-level">${LogLevelBadge({ level: log.level }).outerHTML}</span>
    <span class="logs__entry-source">${log.source}</span>
    <span class="logs__entry-message">${escapeHtml(log.message)}</span>
    <span class="logs__entry-action">
      <button class="topbar__icon-btn copy-log-btn" title="Copy" style="width: 24px; height: 24px;">${getIcon('copy', 12)}</button>
    </span>
  `;

  entry.querySelector('.copy-log-btn')?.addEventListener('click', (e) => {
    e.stopPropagation();
    copyToClipboard(log.message);
    toast.success('Copied', 'Log message copied to clipboard');
  });

  return entry;
}

function addLogEntry(log) {
  if (!logList) return;

  // Apply filters
  if (currentFilters.level && log.level !== currentFilters.level.toUpperCase()) return;
  if (currentFilters.source && log.source !== currentFilters.source) return;
  if (currentFilters.search && !log.message.toLowerCase().includes(currentFilters.search.toLowerCase())) return;

  const entry = createLogEntry(log);
  logList.insertBefore(entry, logList.firstChild);

  // Limit to 500 entries
  while (logList.children.length > 500) {
    logList.removeChild(logList.lastChild);
  }
}

function renderPagination(pagination) {
  const container = document.getElementById('logs-pagination');
  if (!container) return;

  if (!pagination || pagination.total_pages <= 1) {
    container.innerHTML = `<div class="pagination__info">${pagination.total} log entries</div>`;
    return;
  }

  container.innerHTML = `
    <div class="pagination">
      <div class="pagination__info">Page ${pagination.page} of ${pagination.total_pages} — ${pagination.total} entries</div>
      <div class="pagination__controls">
        <button class="pagination__btn" data-page="${pagination.page - 1}" ${!pagination.has_prev ? 'disabled' : ''}>
          ${getIcon('chevronLeft', 14)}
        </button>
        <button class="pagination__btn" data-page="${pagination.page + 1}" ${!pagination.has_next ? 'disabled' : ''}>
          ${getIcon('chevronRight', 14)}
        </button>
      </div>
    </div>
  `;

  container.querySelectorAll('[data-page]').forEach(btn => {
    btn.addEventListener('click', () => {
      const page = parseInt(btn.dataset.page);
      if (page && page !== currentPage) {
        currentPage = page;
        loadLogs();
      }
    });
  });
}

async function downloadLogs() {
  try {
    toast.info('Preparing download', 'Fetching logs...');
    const content = await logsApi.download(currentFilters);
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    downloadBlob(content, `autoshortsai_logs_${timestamp}.log`);
    toast.success('Downloaded', 'Logs file has been downloaded.');
  } catch (err) {
    toast.error('Download failed', err.error?.message || 'Unknown error');
  }
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

export default { render, mount };
