/**
 * Pipeline Page — detailed view of pipeline runs and stages
 */

import { el, formatDuration, formatTime, formatDateTime } from '../utils.js';
import { getIcon } from '../icons.js';
import { pipelineApi } from '../api.js';
import Card from '../components/Card.js';
import Badge from '../components/Badge.js';
import ProgressBar from '../components/ProgressBar.js';
import { CardSkeleton } from '../components/Skeleton.js';
import toast from '../components/Toast.js';
import events from '../events.js';

let refreshHandler = null;
let wsHandlers = [];

export function render() {
  const main = el('div');
  main.innerHTML = `
    <div class="main__inner">
      <div class="page-header">
        <div class="page-header__title">
          <h1>Pipeline</h1>
          <span class="page-header__subtitle">Monitor and manage your video production pipeline</span>
        </div>
        <div class="page-header__actions">
          <button class="btn btn--primary btn--sm" id="new-run-btn">
            ${getIcon('plus', 16)}
            <span>New Run</span>
          </button>
          <button class="btn btn--secondary btn--sm" id="refresh-btn">
            ${getIcon('refresh', 16)}
          </button>
        </div>
      </div>

      <div id="pipeline-content">
        ${CardSkeleton().outerHTML}
      </div>
    </div>
  `;
  return main;
}

export async function mount() {
  await loadPipeline();

  document.getElementById('refresh-btn')?.addEventListener('click', loadPipeline);
  document.getElementById('new-run-btn')?.addEventListener('click', createNewRun);

  refreshHandler = () => loadPipeline();
  events.on('page:refresh', refreshHandler);

  wsHandlers.push(
    events.on('ws:stage_update', () => {
      // Live update — just reload
      loadPipeline();
    })
  );

  return () => {
    if (refreshHandler) events.off('page:refresh', refreshHandler);
    wsHandlers.forEach(u => u && u());
    wsHandlers = [];
  };
}

async function loadPipeline() {
  try {
    const [todayResp, recentResp] = await Promise.all([
      pipelineApi.getToday(),
      pipelineApi.getOverview(),
    ]);

    const content = document.getElementById('pipeline-content');
    if (!content) return;
    content.innerHTML = '';

    // Today's run — detailed view
    if (todayResp.success && todayResp.data) {
      content.appendChild(renderTodayRunDetail(todayResp.data));
    } else {
      content.appendChild(renderNoRun());
    }

    // Recent runs
    if (recentResp.success) {
      content.appendChild(renderRecentRuns(recentResp.data.recent_runs || []));
      content.appendChild(renderPipelineStats(recentResp.data));
    }
  } catch (err) {
    toast.error('Failed to load pipeline', err.error?.message || 'Unknown error');
  }
}

function renderTodayRunDetail(run) {
  const stages = run.stages || [];

  const stagesHtml = stages.map(stage => `
    <div class="stage-card" data-stage-key="${stage.stage_key}" data-status="${stage.status}"
      style="--stage-color: ${stage.color || getStatusColor(stage.status)};">
      <div class="stage-card__header">
        <div class="stage-card__title">
          <span class="stage-card__icon">${getIcon(getStageIcon(stage.stage_key), 16)}</span>
          <span>${stage.stage_name}</span>
        </div>
        ${Badge({ status: stage.status, dot: true }).outerHTML}
      </div>
      ${stage.progress > 0 ? ProgressBar({ value: stage.progress, status: stage.status }).outerHTML : ''}
      ${stage.current_task ? `<div class="stage-card__task">${stage.current_task}</div>` : ''}
      ${stage.error_message ? `<div style="color: var(--status-failed); font-size: var(--fs-xs); margin-top: var(--space-2);">${stage.error_message}</div>` : ''}
      ${(stage.memory_usage_mb != null || stage.cpu_usage_percent != null) ? `
        <div class="stage-card__metrics">
          ${stage.memory_usage_mb != null ? `
            <div class="stage-card__metric">
              <span class="stage-card__metric-label">Memory</span>
              <span class="stage-card__metric-value">${stage.memory_usage_mb.toFixed(0)} MB</span>
            </div>
          ` : ''}
          ${stage.cpu_usage_percent != null ? `
            <div class="stage-card__metric">
              <span class="stage-card__metric-label">CPU</span>
              <span class="stage-card__metric-value">${stage.cpu_usage_percent.toFixed(1)}%</span>
            </div>
          ` : ''}
          ${stage.execution_time_seconds != null ? `
            <div class="stage-card__metric">
              <span class="stage-card__metric-label">Time</span>
              <span class="stage-card__metric-value">${formatDuration(stage.execution_time_seconds)}</span>
            </div>
          ` : ''}
        </div>
      ` : ''}
    </div>
  `).join('');

  return Card({
    title: `Today's Run — ${run.run_uid.slice(0, 12)}`,
    subtitle: `Started ${formatDateTime(run.started_at)}`,
    actions: el('div', { style: { display: 'flex', gap: 'var(--space-2)', alignItems: 'center' } }, [
      Badge({ status: run.status, dot: true }),
      run.status === 'running' ? el('button', {
        class: 'btn btn--ghost btn--sm',
        html: getIcon('pause', 14),
        title: 'Pause',
      }) : null,
    ].filter(Boolean)),
    body: `
      <div class="grid grid-cols-4" style="margin-bottom: var(--space-4);">
        <div class="stat-card" style="--stat-color: var(--status-running); padding: var(--space-3);">
          <div class="stat-card__label">Started</div>
          <div class="stat-card__value" style="font-size: var(--fs-lg);">${formatTime(run.started_at)}</div>
        </div>
        <div class="stat-card" style="--stat-color: var(--status-completed); padding: var(--space-3);">
          <div class="stat-card__label">Finished</div>
          <div class="stat-card__value" style="font-size: var(--fs-lg);">${formatTime(run.finished_at)}</div>
        </div>
        <div class="stat-card" style="--stat-color: var(--accent); padding: var(--space-3);">
          <div class="stat-card__label">Execution</div>
          <div class="stat-card__value" style="font-size: var(--fs-lg);">${formatDuration(run.execution_time_seconds)}</div>
        </div>
        <div class="stat-card" style="--stat-color: var(--status-waiting); padding: var(--space-3);">
          <div class="stat-card__label">Progress</div>
          <div class="stat-card__value" style="font-size: var(--fs-lg);">${run.current_progress.toFixed(0)}%</div>
        </div>
      </div>
      <div style="margin-bottom: var(--space-4);">
        ${ProgressBar({ value: run.current_progress, status: run.status, size: 'lg', showLabel: true, label: 'Overall Progress' }).outerHTML}
      </div>
      <div class="pipeline__stages-grid">${stagesHtml}</div>
    `,
  });
}

function renderNoRun() {
  return Card({
    title: "Today's Run",
    body: `
      <div class="empty-state">
        <div class="empty-state__icon">${getIcon('rocket', 48)}</div>
        <div class="empty-state__title">No pipeline run today</div>
        <div class="empty-state__description">Click "New Run" to start a new pipeline execution.</div>
      </div>
    `,
  });
}

function renderRecentRuns(runs) {
  if (!runs || runs.length === 0) return Card({ title: 'Recent Runs', body: '<div class="empty-state">No runs found.</div>' });

  const items = runs.slice(0, 10).map(run => `
    <div class="analytics__list-item" style="grid-template-columns: 1fr 90px 90px 90px 110px;">
      <div>
        <div class="analytics__title" style="font-family: var(--font-mono); font-size: var(--fs-xs);">${run.run_uid.slice(0, 20)}</div>
        <div style="font-size: 10px; color: var(--text-tertiary); margin-top: 2px;">${formatDateTime(run.created_at)}</div>
      </div>
      <div class="analytics__stats">
        <div class="analytics__stat">
          <span class="analytics__stat-value">${run.completed_videos}</span>
          <span class="analytics__stat-label">Done</span>
        </div>
      </div>
      <div class="analytics__stats">
        <div class="analytics__stat">
          <span class="analytics__stat-value">${run.failed_videos}</span>
          <span class="analytics__stat-label">Failed</span>
        </div>
      </div>
      <div class="analytics__stats">
        <div class="analytics__stat">
          <span class="analytics__stat-value">${formatDuration(run.execution_time_seconds)}</span>
          <span class="analytics__stat-label">Time</span>
        </div>
      </div>
      <div style="display: flex; justify-content: flex-end;">
        ${Badge({ status: run.status, dot: true }).outerHTML}
      </div>
    </div>
  `).join('');

  return Card({
    title: 'Recent Runs',
    subtitle: `${runs.length} total runs`,
    body: `<div class="analytics__top-list">${items}</div>`,
  });
}

function renderPipelineStats(overview) {
  const stats = [
    { label: 'Last 7 Days', value: overview.last_7_days_count || 0, icon: 'calendar', color: '#3B82F6' },
    { label: 'Success Rate', value: `${(overview.success_rate || 0).toFixed(1)}%`, icon: 'check-circle', color: '#10B981' },
  ];

  const statsHtml = stats.map(s => StatCardMini(s)).join('');

  return el('div', { class: 'grid grid-cols-2' });
}

function StatCardMini({ label, value, icon, color }) {
  return `
    <div class="stat-card" style="--stat-color: ${color}; --stat-color-bg: ${color}20;">
      <div class="stat-card__header">
        <div class="stat-card__icon">${getIcon(icon, 18)}</div>
      </div>
      <div class="stat-card__label">${label}</div>
      <div class="stat-card__value">${value}</div>
    </div>
  `;
}

function getStageIcon(key) {
  const icons = {
    content_engine: 'file-text',
    image_engine: 'image',
    narrator: 'mic',
    whisper: 'waveform',
    timeline: 'layers',
    render: 'film',
    quality_check: 'check-circle',
    upload: 'upload',
  };
  return icons[key] || 'info';
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

async function createNewRun() {
  try {
    const response = await pipelineApi.createRun(5);
    if (response.success) {
      toast.success('Run created', 'New pipeline run has been created successfully.');
      // Start the run
      await pipelineApi.startRun(response.data.id);
      loadPipeline();
    }
  } catch (err) {
    toast.error('Failed to create run', err.error?.message || 'Unknown error');
  }
}

export default { render, mount };
