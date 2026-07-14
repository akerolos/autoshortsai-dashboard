/**
 * Card component
 */

import { el } from '../utils.js';

export function Card({ title, subtitle, body, footer, glass = false, noPadding = false, actions = null }) {
  const card = el('div', { class: `card ${glass ? 'card--glass' : ''} ${noPadding ? 'card--no-padding' : ''}` });

  if (title || actions) {
    const header = el('div', { class: 'card__header' });
    const titleWrap = el('div');
    if (title) titleWrap.appendChild(el('div', { class: 'card__title' }, title));
    if (subtitle) titleWrap.appendChild(el('div', { class: 'card__subtitle' }, subtitle));
    header.appendChild(titleWrap);
    if (actions) header.appendChild(actions);
    card.appendChild(header);
  }

  if (body) {
    const bodyEl = el('div', { class: 'card__body' });
    if (Array.isArray(body)) {
      body.forEach(b => bodyEl.appendChild(typeof b === 'string' ? document.createTextNode(b) : b));
    } else if (typeof body === 'string') {
      bodyEl.innerHTML = body;
    } else {
      bodyEl.appendChild(body);
    }
    card.appendChild(bodyEl);
  }

  if (footer) {
    const footerEl = el('div', { class: 'card__footer' }, footer);
    card.appendChild(footerEl);
  }

  return card;
}

export default Card;
