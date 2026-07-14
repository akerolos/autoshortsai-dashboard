/**
 * Progress bar component
 */

import { el } from '../utils.js';

export function ProgressBar({ value = 0, status = null, size = 'sm', showLabel = false, label = null }) {
  const wrapper = el('div', { class: 'progress-wrapper' });
  const progress = el('div', {
    class: `progress ${size === 'lg' ? 'progress--lg' : ''} ${status ? `progress--${status}` : ''}`,
  });
  const bar = el('div', {
    class: 'progress__bar',
    style: { width: `${Math.min(100, Math.max(0, value))}%` },
  });
  progress.appendChild(bar);
  wrapper.appendChild(progress);

  if (showLabel) {
    const labelEl = el('div', {
      style: {
        fontSize: 'var(--fs-xs)',
        color: 'var(--text-tertiary)',
        marginTop: 'var(--space-1)',
        display: 'flex',
        justifyContent: 'space-between',
      },
    });
    labelEl.innerHTML = `<span>${label || ''}</span><span>${value.toFixed(1)}%</span>`;
    wrapper.appendChild(labelEl);
  }

  return wrapper;
}

export default ProgressBar;
