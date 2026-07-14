/**
 * Badge component — status indicators
 */

import { el } from '../utils.js';

export function Badge({ status, label = null, dot = true, size = 'sm' }) {
  const text = label || status;
  const badge = el('span', {
    class: `badge badge--${status}`,
  });
  if (dot) {
    badge.innerHTML = `<span class="badge__dot"></span><span>${text}</span>`;
  } else {
    badge.textContent = text;
  }
  return badge;
}

export function LogLevelBadge({ level }) {
  return el('span', {
    class: `badge badge--${level.toUpperCase()}`,
  }, level);
}

export default Badge;
