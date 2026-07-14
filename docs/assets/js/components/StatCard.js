/**
 * StatCard component — displays a single statistic
 */

import { el, formatNumber } from '../utils.js';
import { getIcon } from '../icons.js';

export function StatCard({ label, value, icon, color = '#8B5CF6', change = null, changeLabel = null, rawValue = null }) {
  const card = el('div', {
    class: 'stat-card',
    style: {
      '--stat-color': color,
      '--stat-color-bg': `${color}20`,
    },
  });

  const header = el('div', { class: 'stat-card__header' });
  if (icon) {
    header.appendChild(el('div', { class: 'stat-card__icon', html: getIcon(icon, 18) }));
  }
  header.appendChild(el('div'));

  const valueStr = typeof value === 'number' ? formatNumber(value) : value;

  card.innerHTML = `
    <div class="stat-card__header">
      ${icon ? `<div class="stat-card__icon">${getIcon(icon, 18)}</div>` : '<div></div>'}
    </div>
    <div class="stat-card__label">${label}</div>
    <div class="stat-card__value" data-raw="${rawValue ?? value}">${valueStr}</div>
    ${change != null ? `
      <div class="stat-card__change stat-card__change--${change > 0 ? 'up' : change < 0 ? 'down' : 'neutral'}">
        ${change > 0 ? '↑' : change < 0 ? '↓' : '→'} ${Math.abs(change).toFixed(1)}%
        ${changeLabel ? `<span style="color: var(--text-tertiary); margin-left: 4px;">${changeLabel}</span>` : ''}
      </div>
    ` : ''}
  `;

  return card;
}

export default StatCard;
