/**
 * Videos Page — full videos list with filters and table
 */

import { el, formatNumber, formatDuration, formatDate } from '../utils.js';
import { getIcon } from '../icons.js';
import { videosApi } from '../api.js';
import Card from '../components/Card.js';
import Badge from '../components/Badge.js';
import { TableSkeleton } from '../components/Skeleton.js';
import toast from '../components/Toast.js';
import events from '../events.js';
import { debounce } from '../utils.js';

let refreshHandler = null;
let currentPage = 1;
let currentFilters = {
  status: '',
  platform: '',
  search: '',
  sort_by: 'upload_date',
  sort_order: 'desc',
};

export function render() {
  const main = el('div');
  main.innerHTML = `
    <div class="main__inner">
      <div class="page-header">
        <div class="page-header__title">
          <h1>Videos</h1>
          <span class="page-header__subtitle">Browse and manage all generated videos</span>
        </div>
      </div>

      <div class="card card--no-padding">
        <div class="filter-bar" style="border: none; border-radius: 0; border-bottom: 1px solid var(--border-default);">
          <div class="filter-bar__search">
            <span class="filter-bar__search-icon">${getIcon('search', 14)}</span>
            <input type="text" id="search-input" placeholder="Search videos..." value="" />
          </div>
          <select class="filter-bar__select" id="status-filter">
            <option value="">All Status</option>
            <option value="published">Published</option>
            <option value="pending">Pending</option>
            <option value="rendering">Rendering</option>
            <option value="uploading">Uploading</option>
            <option value="failed">Failed</option>
          </select>
          <select class="filter-bar__select" id="platform-filter">
            <option value="">All Platforms</option>
            <option value="youtube">YouTube</option>
            <option value="tiktok">TikTok</option>
            <option value="instagram">Instagram</option>
            <option value="facebook">Facebook</option>
          </select>
          <select class="filter-bar__select" id="sort-filter">
            <option value="upload_date:desc">Newest First</option>
            <option value="upload_date:asc">Oldest First</option>
            <option value="views:desc">Most Viewed</option>
            <option value="views:asc">Least Viewed</option>
            <option value="ctr:desc">Highest CTR</option>
            <option value="retention:desc">Best Retention</option>
          </select>
        </div>

        <div id="videos-table-wrapper">
          ${TableSkeleton({ rows: 8, cols: 7 }).outerHTML}
        </div>

        <div id="videos-pagination" style="padding: var(--space-3) var(--space-4);"></div>
      </div>
    </div>
  `;
  return main;
}

export async function mount() {
  // Filter handlers
  const searchInput = document.getElementById('search-input');
  const statusFilter = document.getElementById('status-filter');
  const platformFilter = document.getElementById('platform-filter');
  const sortFilter = document.getElementById('sort-filter');

  searchInput?.addEventListener('input', debounce((e) => {
    currentFilters.search = e.target.value;
    currentPage = 1;
    loadVideos();
  }, 300));

  statusFilter?.addEventListener('change', (e) => {
    currentFilters.status = e.target.value;
    currentPage = 1;
    loadVideos();
  });

  platformFilter?.addEventListener('change', (e) => {
    currentFilters.platform = e.target.value;
    currentPage = 1;
    loadVideos();
  });

  sortFilter?.addEventListener('change', (e) => {
    const [sortBy, sortOrder] = e.target.value.split(':');
    currentFilters.sort_by = sortBy;
    currentFilters.sort_order = sortOrder;
    currentPage = 1;
    loadVideos();
  });

  await loadVideos();

  refreshHandler = () => loadVideos();
  events.on('page:refresh', refreshHandler);

  return () => {
    if (refreshHandler) events.off('page:refresh', refreshHandler);
  };
}

async function loadVideos() {
  try {
    const response = await videosApi.list({
      page: currentPage,
      page_size: 20,
      ...currentFilters,
    });

    if (response.success) {
      renderTable(response.data.items, response.data.pagination);
    }
  } catch (err) {
    toast.error('Failed to load videos', err.error?.message || 'Unknown error');
  }
}

function renderTable(videos, pagination) {
  const wrapper = document.getElementById('videos-table-wrapper');
  const paginationEl = document.getElementById('videos-pagination');

  if (!videos || videos.length === 0) {
    wrapper.innerHTML = `
      <div class="empty-state" style="padding: var(--space-12);">
        <div class="empty-state__icon">${getIcon('film', 48)}</div>
        <div class="empty-state__title">No videos found</div>
        <div class="empty-state__description">Try adjusting your filters or check back later.</div>
      </div>
    `;
    paginationEl.innerHTML = '';
    return;
  }

  wrapper.innerHTML = `
    <div class="table-wrapper" style="border: none;">
      <table class="table">
        <thead>
          <tr>
            <th>Thumbnail</th>
            <th>Title</th>
            <th>Duration</th>
            <th>Upload Date</th>
            <th>Views</th>
            <th>CTR</th>
            <th>Retention</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${videos.map(v => `
            <tr>
              <td>
                <div style="width: 80px; height: 45px; border-radius: var(--radius-sm); overflow: hidden; background: var(--bg-elevated);">
                  ${v.thumbnail_url
                    ? `<img src="${v.thumbnail_url}" alt="${v.title}" loading="lazy" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.style.display='none';" />`
                    : `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-tertiary);">${getIcon('film', 16)}</div>`
                  }
                </div>
              </td>
              <td><div class="table__title">${v.title}</div></td>
              <td><span class="font-mono">${v.duration_seconds}s</span></td>
              <td>${formatDate(v.upload_date)}</td>
              <td class="tabular-nums">${formatNumber(v.views)}</td>
              <td class="tabular-nums">${v.ctr.toFixed(1)}%</td>
              <td class="tabular-nums">${v.retention.toFixed(1)}%</td>
              <td>${Badge({ status: v.status, dot: true }).outerHTML}</td>
              <td>
                ${v.status === 'published' ? `
                  <a href="https://youtube.com/watch?v=${v.external_video_id || ''}" target="_blank" rel="noopener" class="table__action">
                    ${getIcon('external', 12)}
                    <span>Open</span>
                  </a>
                ` : ''}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;

  // Pagination
  renderPagination(paginationEl, pagination);
}

function renderPagination(container, pagination) {
  if (!pagination || pagination.total_pages <= 1) {
    container.innerHTML = `<div class="pagination__info">Showing ${pagination.total} video${pagination.total !== 1 ? 's' : ''}</div>`;
    return;
  }

  const pages = [];
  const maxVisible = 5;
  let start = Math.max(1, pagination.page - Math.floor(maxVisible / 2));
  let end = Math.min(pagination.total_pages, start + maxVisible - 1);
  if (end - start < maxVisible - 1) start = Math.max(1, end - maxVisible + 1);

  if (start > 1) {
    pages.push(`<button class="pagination__btn" data-page="1">1</button>`);
    if (start > 2) pages.push(`<span class="pagination__btn" style="border: none;">…</span>`);
  }
  for (let i = start; i <= end; i++) {
    pages.push(`<button class="pagination__btn ${i === pagination.page ? 'is-active' : ''}" data-page="${i}">${i}</button>`);
  }
  if (end < pagination.total_pages) {
    if (end < pagination.total_pages - 1) pages.push(`<span class="pagination__btn" style="border: none;">…</span>`);
    pages.push(`<button class="pagination__btn" data-page="${pagination.total_pages}">${pagination.total_pages}</button>`);
  }

  container.innerHTML = `
    <div class="pagination">
      <div class="pagination__info">
        Showing ${(pagination.page - 1) * pagination.page_size + 1}–${Math.min(pagination.page * pagination.page_size, pagination.total)} of ${pagination.total}
      </div>
      <div class="pagination__controls">
        <button class="pagination__btn" data-page="${pagination.page - 1}" ${!pagination.has_prev ? 'disabled' : ''}>
          ${getIcon('chevronLeft', 14)}
        </button>
        ${pages.join('')}
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
        loadVideos();
      }
    });
  });
}

export default { render, mount };
