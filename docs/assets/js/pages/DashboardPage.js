/**
 * Dashboard Page — Home / Mission Control overview
 */

import { el, formatNumber, formatDuration, formatTime, formatDateTime } from '../utils.js';
import { getIcon } from '../icons.js';
import { dashboardApi } from '../api.js';
import Card from '../components/Card.js';
import StatCard from '../components/StatCard.js';
import Badge from '../components/Badge.js';
import ProgressBar from '../components/ProgressBar.js';
import { createChart } from '../components/Chart.js';
import { StatCardSkeleton, CardSkeleton } from '../components/Skeleton.js';
import toast from '../components/Toast.js';
import events from '../events.js';
import { store } from '../store.js';

let charts = [];
let refreshHandler = null;
let wsHandlers = [];

export function render() {
  const main = el('div');

  main.innerHTML = `
    <div class="main__inner">
      <div class="page-header">
        <div class="page-header__title">
          <h1>Dashboard</h1>
          <span class="page-header__subtitle">Real-time overview of your AutoShortsAI system</span>
        </div>
        <div class="page-header__actions">
          <button class="btn btn--secondary btn--sm" id="refresh-btn">
            ${getIcon('refresh', 16)}
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <!-- Stat Cards -->
      <div class="grid grid-cols-6" id="stats-grid">
        ${Array(6).fill(0).map(() => StatCardSkeleton().outerHTML).join('')}
      </div>

      <!-- Today's Run + Pipeline Status -->
      <div class="grid grid-cols-2">
        <div id="today-run-section"></div>
        <div id="pipeline-status-section"></div>
      </div>

      <!-- Today's Videos -->
      <div id="today-videos-section">
        ${CardSkeleton().outerHTML}
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-2" id="charts-section">
        ${CardSkeleton().outerHTML}
        ${CardSkeleton().outerHTML}
      </div>
    </div>
  `;

  return main;
}

export async function mount() {
  // Load data
  await loadOverview();

  // Refresh button
  const refreshBtn = document.getElementById('refresh-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', loadOverview);
  }

  // Listen for refresh events
  refreshHandler = () => loadOverview();
  events.on('page:refresh', refreshHandler);

  // WebSocket handlers for real-time updates
  wsHandlers.push(
    events.on('ws:stage_update', (data) => {
      updateStageStatus(data);
    }),
    events.on('ws:pipeline_run_update', (data) => {
      // Refresh today's run section
      loadOverview();
    })
  );

  return () => {
    if (refreshHandler) events.off('page:refresh', refreshHandler);
    wsHandlers.forEach(unsub => unsub && unsub());
    wsHandlers = [];
    charts.forEach(c => c.destroy && c.destroy());
    charts = [];
  };
}

async function loadOverview() {
  try {
    const response = await dashboardApi.getOverview();
    if (response.success) {
      renderOverview(response.data);
    }
  } catch (err) {
    toast.error('Failed to load dashboard', err.error?.message || 'Unknown error');
  }
}

function renderOverview(data) {
  // Stats
  const statsGrid = document.getElementById('stats-grid');
  if (statsGrid) {
    statsGrid.innerHTML = '';
    data.stats.forEach((stat, i) => {
      const card = StatCard({
        label: stat.label,
        value: stat.value,
        icon: stat.icon,
        color: stat.color,
        rawValue: stat.raw_value,
        change: stat.change,
        changeLabel: stat.change_label,
      });
      card.classList.add('animate-fade-in-up', `delay-${i + 1}`);
      statsGrid.appendChild(card);
    });
  }

  // Today's Run
  renderTodayRun(data.today_run);

  // Pipeline Status
  renderPipelineStatus(data.pipeline_stages);

  // Today's Videos
  renderTodayVideos(data.today_videos);

  // Charts
  renderCharts(data.charts);
}

function renderTodayRun(todayRun) {
  const section = document.getElementById('today-run-section');
  if (!section) return;

  const progress = todayRun.current_progress || 0;
  const completed = todayRun.completed_videos || 0;
  const target = todayRun.target_videos || 5;

  const card = Card({
    title: "Today's Run",
    subtitle: todayRun.run_uid ? `Run ${todayRun.run_uid.slice(0, 8)}` : 'No active run',
    actions: Badge({ status: todayRun.status, dot: true }),
    body: `
      <div class="dashboard__today-run">
        <div class="today-run__info">
          <div class="today-run__time-row">
            <div class="today-run__time-item">
              <span class="today-run__time-label">Start Time</span>
              <span class="today-run__time-value">${formatTime(todayRun.started_at)}</span>
            </div>
            <div class="today-run__time-item">
              <span class="today-run__time-label">Finish Time</span>
              <span class="today-run__time-value">${formatTime(todayRun.finished_at)}</span>
            </div>
            <div class="today-run__time-item">
              <span class="today-run__time-label">Execution Time</span>
              <span class="today-run__time-value">${formatDuration(todayRun.execution_time_seconds)}</span>
            </div>
          </div>
          <div class="today-run__time-row">
            <div class="today-run__time-item">
              <span class="today-run__time-label">Current Stage</span>
              <span class="today-run__time-value" style="text-transform: capitalize;">${(todayRun.current_stage || '—').replace(/_/g, ' ')}</span>
            </div>
            <div class="today-run__time-item">
              <span class="today-run__time-label">Videos</span>
              <span class="today-run__time-value">${completed} / ${target}</span>
            </div>
          </div>
        </div>
        <div class="today-run__progress-ring">
          ${createProgressRing(progress, todayRun.color)}
        </div>
      </div>
      <div style="margin-top: var(--space-4);">
        ${ProgressBar({ value: progress, status: todayRun.status, size: 'lg', showLabel: true, label: 'Overall Progress' }).outerHTML}
      </div>
    `,
  });

  section.innerHTML = '';
  section.appendChild(card);
}

function createProgressRing(percent, color = '#8B5CF6') {
  const size = 120;
  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;

  return `
    <svg width="${size}" height="${size}" style="transform: rotate(-90deg);">
      <circle cx="${size/2}" cy="${size/2}" r="${radius}" stroke="var(--bg-elevated)" stroke-width="${stroke}" fill="none"/>
      <circle cx="${size/2}" cy="${size/2}" r="${radius}" stroke="${color}" stroke-width="${stroke}" fill="none"
        stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
        stroke-linecap="round" style="transition: stroke-dashoffset 1s ease;"/>
      <text x="${size/2}" y="${size/2}" text-anchor="middle" dominant-baseline="central"
        fill="var(--text-primary)" font-size="20" font-weight="700"
        style="transform: rotate(90deg); transform-origin: ${size/2}px ${size/2}px;">
        ${percent.toFixed(0)}%
      </text>
    </svg>
  `;
}

function renderPipelineStatus(stages) {
  const section = document.getElementById('pipeline-status-section');
  if (!section) return;

  const stagesHtml = stages.map(stage => `
    <div class="stage-card" data-stage-key="${stage.key}" data-status="${stage.status}"
      style="--stage-color: ${stage.color};">
      <div class="stage-card__header">
        <div class="stage-card__title">
          <span class="stage-card__icon">${getIcon(stage.icon, 16)}</span>
          <span>${stage.name}</span>
        </div>
        ${Badge({ status: stage.status, dot: true }).outerHTML}
      </div>
      ${stage.progress != null ? ProgressBar({ value: stage.progress, status: stage.status }).outerHTML : ''}
      ${stage.current_task ? `<div class="stage-card__task">${stage.current_task}</div>` : ''}
    </div>
  `).join('');

  const card = Card({
    title: 'Pipeline Status',
    subtitle: 'Real-time stage monitoring',
    body: `<div class="dashboard__pipeline-grid">${stagesHtml}</div>`,
  });

  section.innerHTML = '';
  section.appendChild(card);
}

function renderTodayVideos(videos) {
  const section = document.getElementById('today-videos-section');
  if (!section) return;

  if (!videos || videos.length === 0) {
    section.innerHTML = '';
    section.appendChild(Card({
      title: "Today's Videos",
      subtitle: 'Videos generated today',
      body: `
        <div class="empty-state">
          <div class="empty-state__icon">${getIcon('film', 48)}</div>
          <div class="empty-state__title">No videos yet today</div>
          <div class="empty-state__description">Videos will appear here once the pipeline starts generating them.</div>
        </div>
      `,
    }));
    return;
  }

  const videosHtml = videos.slice(0, 5).map(v => `
    <div class="video-card" data-video-id="${v.id}">
      <div class="video-card__thumbnail">
        ${v.thumbnail_url
          ? `<img src="${v.thumbnail_url}" alt="${v.title}" loading="lazy" onerror="this.style.display='none'; this.parentElement.style.background='var(--bg-elevated)';" />`
          : `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-tertiary);">${getIcon('film', 32)}</div>`
        }
        <span class="video-card__duration">${v.duration_seconds}s</span>
      </div>
      <div class="video-card__body">
        <div class="video-card__title">${v.title}</div>
        <div class="video-card__meta">
          ${Badge({ status: v.status, dot: true }).outerHTML}
          ${v.render_time_seconds ? `<span>Render: ${formatDuration(v.render_time_seconds)}</span>` : ''}
        </div>
      </div>
    </div>
  `).join('');

  const grid = el('div', { class: 'videos__grid' });
  grid.innerHTML = videosHtml;

  section.innerHTML = '';
  section.appendChild(Card({
    title: "Today's Videos",
    subtitle: `${videos.length} video${videos.length !== 1 ? 's' : ''} generated today`,
    body: grid,
  }));

  // Click handlers
  grid.querySelectorAll('.video-card').forEach(card => {
    card.addEventListener('click', () => {
      const videoId = card.dataset.videoId;
      const video = videos.find(v => v.id == videoId);
      if (video && video.video_url) {
        window.open(video.video_url, '_blank');
      }
    });
  });
}

function renderCharts(chartConfigs) {
  const section = document.getElementById('charts-section');
  if (!section) return;
  section.innerHTML = '';
  charts.forEach(c => c.destroy && c.destroy());
  charts = [];

  chartConfigs.forEach(config => {
    const card = Card({
      title: config.title,
      body: '',
    });
    const chartContainer = el('div', { class: 'chart-container' });
    card.querySelector('.card__body').appendChild(chartContainer);
    section.appendChild(card);

    // Create chart
    setTimeout(() => {
      const chart = createChart(config);
      const chartEl = chart.render();
      card.querySelector('.card__body').innerHTML = '';
      card.querySelector('.card__body').appendChild(chartEl);
      charts.push(chart);
    }, 0);
  });
}

function updateStageStatus(data) {
  const stageCard = document.querySelector(`.stage-card[data-stage-key="${data.stage_key}"]`);
  if (!stageCard) return;

  stageCard.dataset.status = data.status;
  stageCard.style.setProperty('--stage-color', getStatusColor(data.status));

  // Update badge
  const badge = stageCard.querySelector('.badge');
  if (badge) {
    badge.className = `badge badge--${data.status}`;
    badge.innerHTML = `<span class="badge__dot"></span><span>${data.status}</span>`;
  }

  // Update progress bar
  const progress = stageCard.querySelector('.progress__bar');
  if (progress) {
    progress.style.width = `${data.progress}%`;
  }

  // Update task
  let taskEl = stageCard.querySelector('.stage-card__task');
  if (data.current_task) {
    if (!taskEl) {
      taskEl = document.createElement('div');
      taskEl.className = 'stage-card__task';
      stageCard.appendChild(taskEl);
    }
    taskEl.textContent = data.current_task;
  }
}

function getStatusColor(status) {
  const colors = {
    running: '#3B82F6',
    completed: '#10B981',
    failed: '#EF4444',
    waiting: '#F59E0B',
    idle: '#71717A',
    skipped: '#71717A',
  };
  return colors[status] || '#71717A';
}

export default { render, mount };
