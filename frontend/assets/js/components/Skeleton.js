/**
 * Skeleton loader component
 */

import { el } from '../utils.js';

export function Skeleton({ type = 'text', count = 1, width = null, height = null }) {
  const wrapper = el('div');
  for (let i = 0; i < count; i++) {
    const skel = el('div', {
      class: `skeleton skeleton--${type}`,
      style: {
        ...(width ? { width: typeof width === 'number' ? `${width}px` : width } : {}),
        ...(height ? { height: typeof height === 'number' ? `${height}px` : height } : {}),
      },
    });
    wrapper.appendChild(skel);
  }
  return wrapper;
}

export function StatCardSkeleton() {
  const card = el('div', { class: 'stat-card' });
  card.innerHTML = `
    <div class="stat-card__header">
      <div class="skeleton skeleton--circle"></div>
    </div>
    <div class="skeleton" style="height: 10px; width: 80px; margin-bottom: 8px;"></div>
    <div class="skeleton" style="height: 28px; width: 60%;"></div>
  `;
  return card;
}

export function CardSkeleton() {
  const card = el('div', { class: 'card' });
  card.innerHTML = `
    <div class="card__header">
      <div class="skeleton" style="height: 16px; width: 140px;"></div>
    </div>
    <div class="skeleton" style="height: 180px; width: 100%;"></div>
  `;
  return card;
}

export function TableSkeleton({ rows = 5, cols = 5 }) {
  const wrapper = el('div', { class: 'table-wrapper' });
  const table = el('table', { class: 'table' });
  const thead = el('thead');
  const headRow = el('tr');
  for (let i = 0; i < cols; i++) {
    headRow.appendChild(el('th', {}, el('div', { class: 'skeleton', style: 'height: 12px; width: 60px;' })));
  }
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = el('tbody');
  for (let r = 0; r < rows; r++) {
    const row = el('tr');
    for (let c = 0; c < cols; c++) {
      row.appendChild(el('td', {}, el('div', { class: 'skeleton', style: 'height: 14px;' })));
    }
    tbody.appendChild(row);
  }
  table.appendChild(tbody);
  wrapper.appendChild(table);
  return wrapper;
}

export default Skeleton;
