/**
 * Utilities — DOM helpers, formatters, etc.
 */

// ===== DOM Helpers =====
export const $ = (selector, parent = document) => parent.querySelector(selector);
export const $$ = (selector, parent = document) => Array.from(parent.querySelectorAll(selector));

export function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === 'class') node.className = value;
    else if (key === 'dataset') Object.assign(node.dataset, value);
    else if (key === 'style' && typeof value === 'object') Object.assign(node.style, value);
    else if (key.startsWith('on') && typeof value === 'function') {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (key === 'html') node.innerHTML = value;
    else if (value !== null && value !== undefined && value !== false) {
      node.setAttribute(key, value === true ? '' : value);
    }
  }
  for (const child of [].concat(children)) {
    if (child == null || child === false) continue;
    if (typeof child === 'string' || typeof child === 'number') {
      node.appendChild(document.createTextNode(String(child)));
    } else {
      node.appendChild(child);
    }
  }
  return node;
}

export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
  return node;
}

// ===== Formatters =====
export function formatNumber(value) {
  if (value == null) return '0';
  const num = Number(value);
  if (isNaN(num)) return '0';
  if (Math.abs(num) >= 1_000_000) return (num / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (Math.abs(num) >= 1_000) return (num / 1_000).toFixed(1).replace(/\.0$/, '') + 'K';
  return String(num);
}

export function formatDuration(seconds) {
  if (seconds == null) return '—';
  if (seconds < 0) return '—';
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
  const total = Math.floor(seconds);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export function formatPercentage(value, decimals = 1) {
  if (value == null) return '—';
  return `${Number(value).toFixed(decimals)}%`;
}

export function formatTime(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleTimeString('en-US', { hour12: false });
}

export function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

export function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function timeAgo(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '—';
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

// ===== Status Helpers =====
export function statusColor(status) {
  const colors = {
    running: '#3B82F6',
    completed: '#10B981',
    failed: '#EF4444',
    waiting: '#F59E0B',
    pending: '#F59E0B',
    idle: '#71717A',
    skipped: '#71717A',
    cancelled: '#71717A',
    published: '#10B981',
    publishing: '#3B82F6',
    rendering: '#3B82F6',
    uploading: '#3B82F6',
  };
  return colors[status] || '#71717A';
}

export function statusBgColor(status) {
  const bgs = {
    running: 'rgba(59, 130, 246, 0.12)',
    completed: 'rgba(16, 185, 129, 0.12)',
    failed: 'rgba(239, 68, 68, 0.12)',
    waiting: 'rgba(245, 158, 11, 0.12)',
    pending: 'rgba(245, 158, 11, 0.12)',
    published: 'rgba(16, 185, 129, 0.12)',
  };
  return bgs[status] || 'rgba(113, 113, 122, 0.12)';
}

// ===== Debounce / Throttle =====
export function debounce(fn, delay = 300) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

export function throttle(fn, limit = 100) {
  let inThrottle = false;
  return function (...args) {
    if (!inThrottle) {
      fn.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

// ===== Copy to clipboard =====
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      document.body.removeChild(ta);
      return true;
    } catch {
      document.body.removeChild(ta);
      return false;
    }
  }
}

// ===== Download helper =====
export function downloadBlob(content, filename, type = 'text/plain') {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 100);
}

// ===== Color manipulation =====
export function hexToRgba(hex, alpha = 1) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// ===== Unique ID =====
export function uid(prefix = 'id') {
  return `${prefix}-${Math.random().toString(36).slice(2, 9)}`;
}
