/**
 * Analytics Page — deep dive into performance metrics
 */

import { el, formatNumber, formatDate, formatDuration } from '../utils.js';
import { getIcon } from '../icons.js';
import { analyticsApi } from '../api.js';
import Card from '../components/Card.js';
import StatCard from '../components/StatCard.js';
import Badge from '../components/Badge.js';
import { createChart } from '../components/Chart.js';
import { StatCardSkeleton, CardSkeleton } from '../components/Skeleton.js';
import toast from '../components/Toast.js';
import events from '../events.js';

let charts = [];
let refreshHandler = null;

export function render() {
  const main = el('div');
  main.innerHTML = `
    <div class="main__inner">
      <div class="page-header">
        <div class="page-header__title">
          <h1>Analytics</h1>
          <span class="page-header__subtitle">Deep insights into your video performance</span>
        </div>
        <div class="page-header__actions">
          <button class="btn btn--secondary btn--sm" id="export-btn">
            ${getIcon('download', 16)}
            <span>Export</span>
          </button>
        </div>
      </div>

      <!-- Stat Cards -->
      <div class="grid grid-cols-6" id="stats-grid">
        ${Array(6).fill(0).map(() => StatCardSkeleton().outerHTML).join('')}
      </div>

      <!-- Charts row 1 -->
      <div class="grid grid-cols-2" id="charts-row-1">
        ${CardSkeleton().outerHTML}
        ${CardSkeleton().outerHTML}
      </div>

      <!-- Charts row 2 -->
      <div class="grid grid-cols-3" id="charts-row-2">
        ${CardSkeleton().outerHTML}
        ${CardSkeleton().outerHTML}
        ${CardSkeleton().outerHTML}
      </div>

      <!-- Top & Worst Videos -->
      <div class="grid grid-cols-2" id="top-worst-section">
        ${CardSkeleton().outerHTML}
        ${CardSkeleton().outerHTML}
      </div>

      <!-- Best Hooks + Upload Frequency -->
      <div class="grid grid-cols-2" id="hooks-freq-section">
        ${CardSkeleton().outerHTML}
        ${CardSkeleton().outerHTML}
      </div>
    </div>
  `;
  return main;
}

export async function mount() {
  await loadAnalytics();

  document.getElementById('export-btn')?.addEventListener('click', exportData);

  refreshHandler = () => loadAnalytics();
  events.on('page:refresh', refreshHandler);

  return () => {
    if (refreshHandler) events.off('page:refresh', refreshHandler);
    charts.forEach(c => c.destroy && c.destroy());
    charts = [];
  };
}

async function loadAnalytics() {
  try {
    const response = await analyticsApi.getOverview();
    if (response.success) {
      renderAnalytics(response.data);
    }
  } catch (err) {
    toast.error('Failed to load analytics', err.error?.message || 'Unknown error');
  }
}

function renderAnalytics(data) {
  // Stats
  const statsGrid = document.getElementById('stats-grid');
  if (statsGrid && data.stats) {
    statsGrid.innerHTML = '';
    data.stats.slice(0, 6).forEach((stat, i) => {
      const card = StatCard({
        label: stat.label,
        value: stat.value,
        icon: stat.icon,
        color: stat.color,
        rawValue: stat.raw_value,
      });
      card.classList.add('animate-fade-in-up', `delay-${i + 1}`);
      statsGrid.appendChild(card);
    });
  }

  // Charts row 1
  renderChartRow('charts-row-1', data.charts.slice(0, 2));

  // Charts row 2
  renderChartRow('charts-row-2', data.charts.slice(2, 5));

  // Top & Worst Videos
  renderTopWorst(data.top_videos, data.worst_videos);

  // Best Hooks + Upload Frequency
  renderHooksAndFreq(data.best_hooks, data.upload_frequency, data.avg_hook_performance);
}

function renderChartRow(containerId, chartConfigs) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';

  chartConfigs.forEach(config => {
    const card = Card({ title: config.title, body: '' });
    container.appendChild(card);

    setTimeout(() => {
      const chart = createChart(config);
      const chartEl = chart.render();
      card.querySelector('.card__body').appendChild(chartEl);
      charts.push(chart);
    }, 0);
  });
}

function renderTopWorst(topVideos, worstVideos) {
  const container = document.getElementById('top-worst-section');
  if (!container) return;
  container.innerHTML = '';

  container.appendChild(renderVideoList('Top Performing Videos', topVideos, 'trending'));
  container.appendChild(renderVideoList('Underperforming Videos', worstVideos, 'trending-down'));
}

function renderVideoList(title, videos, icon) {
  if (!videos || videos.length === 0) {
    return Card({ title, body: '<div class="empty-state">No videos found.</div>' });
  }

  const items = videos.map((v, i) => `
    <div class="analytics__list-item">
      <div class="analytics__rank">${i + 1}</div>
      <img class="analytics__thumbnail" src="${v.thumbnail_url || ''}" alt="${v.title}"
        onerror="this.style.visibility='hidden';" loading="lazy" />
      <div>
        <div class="analytics__title">${v.title}</div>
        <div style="font-size: 10px; color: var(--text-tertiary); margin-top: 2px;">${formatDate(v.upload_date)}</div>
      </div>
      <div class="analytics__stats">
        <div class="analytics__stat">
          <span class="analytics__stat-value">${formatNumber(v.views)}</span>
          <span class="analytics__stat-label">Views</span>
        </div>
        <div class="analytics__stat">
          <span class="analytics__stat-value">${v.ctr.toFixed(1)}%</span>
          <span class="analytics__stat-label">CTR</span>
        </div>
        <div class="analytics__stat">
          <span class="analytics__stat-value">${v.retention.toFixed(0)}%</span>
          <span class="analytics__stat-label">Ret.</span>
        </div>
      </div>
    </div>
  `).join('');

  return Card({
    title,
    actions: el('span', { style: { color: 'var(--text-tertiary)' } }, getIcon(icon, 16)),
    body: `<div class="analytics__top-list">${items}</div>`,
  });
}

function renderHooksAndFreq(bestHooks, uploadFreq, avgHook) {
  const container = document.getElementById('hooks-freq-section');
  if (!container) return;
  container.innerHTML = '';

  // Best Hooks
  if (bestHooks && bestHooks.length > 0) {
    const hooksHtml = bestHooks.map((h, i) => `
      <div class="analytics__list-item" style="grid-template-columns: 40px 1fr auto;">
        <div class="analytics__rank">${i + 1}</div>
        <div>
          <div class="analytics__title">${h.title}</div>
          <div style="font-size: 10px; color: var(--text-tertiary); margin-top: 2px;">Retention: ${h.retention.toFixed(1)}%</div>
        </div>
        <div class="analytics__stats">
          <div class="analytics__stat">
            <span class="analytics__stat-value" style="color: var(--status-completed);">${h.ctr.toFixed(1)}%</span>
            <span class="analytics__stat-label">CTR</span>
          </div>
        </div>
      </div>
    `).join('');

    container.appendChild(Card({
      title: 'Best Hooks',
      subtitle: avgHook ? `Average hook CTR: ${avgHook.toFixed(1)}%` : '',
      actions: el('span', { style: { color: 'var(--text-tertiary)' } }, getIcon('zap', 16)),
      body: `<div class="analytics__top-list">${hooksHtml}</div>`,
    }));
  }

  // Upload Frequency
  if (uploadFreq && uploadFreq.labels) {
    const maxVal = Math.max(...uploadFreq.values, 1);
    const barsHtml = uploadFreq.labels.map((label, i) => {
      const value = uploadFreq.values[i] || 0;
      const height = (value / maxVal) * 100;
      return `
        <div style="display: flex; flex-direction: column; align-items: center; gap: var(--space-2); flex: 1;">
          <div style="font-size: var(--fs-sm); font-weight: var(--fw-semibold); color: var(--text-primary);">${value}</div>
          <div style="width: 100%; height: 120px; display: flex; align-items: flex-end; background: var(--bg-elevated); border-radius: var(--radius-sm); overflow: hidden;">
            <div style="width: 100%; height: ${height}%; background: linear-gradient(180deg, var(--accent), var(--accent-hover)); border-radius: var(--radius-sm); transition: height 0.6s ease;"></div>
          </div>
          <div style="font-size: var(--fs-xs); color: var(--text-tertiary);">${label}</div>
        </div>
      `;
    }).join('');

    container.appendChild(Card({
      title: 'Upload Frequency',
      subtitle: 'Videos published per day (last 7 days)',
      actions: el('span', { style: { color: 'var(--text-tertiary)' } }, getIcon('calendar', 16)),
      body: `<div style="display: flex; gap: var(--space-3); height: 180px; padding-top: var(--space-2);">${barsHtml}</div>`,
    }));
  }
}

function exportData() {
  toast.info('Export started', 'Preparing analytics data for download...');
  // In real implementation, would call an export endpoint
  setTimeout(() => {
    toast.success('Export ready', 'Analytics data has been exported.');
  }, 1500);
}

export default { render, mount };
