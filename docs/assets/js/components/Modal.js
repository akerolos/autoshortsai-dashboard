/**
 * Modal component
 */

import { el } from '../utils.js';
import { getIcon } from '../icons.js';

export function Modal({ title, body, footer, onClose = null, size = 'md' }) {
  const backdrop = el('div', { class: 'modal-backdrop' });

  const modal = el('div', {
    class: 'modal',
    style: size === 'lg' ? { maxWidth: '720px' } : size === 'sm' ? { maxWidth: '400px' } : {},
  });

  // Header
  const header = el('div', { class: 'modal__header' });
  header.appendChild(el('h3', { class: 'modal__title' }, title));
  const closeBtn = el('button', {
    class: 'topbar__icon-btn',
    title: 'Close',
    html: getIcon('x', 18),
  });
  closeBtn.addEventListener('click', () => close());
  header.appendChild(closeBtn);
  modal.appendChild(header);

  // Body
  const bodyEl = el('div', { class: 'modal__body' });
  if (typeof body === 'string') bodyEl.innerHTML = body;
  else if (body instanceof HTMLElement) bodyEl.appendChild(body);
  modal.appendChild(bodyEl);

  // Footer
  if (footer) {
    const footerEl = el('div', { class: 'modal__footer' });
    if (Array.isArray(footer)) {
      footer.forEach(f => footerEl.appendChild(typeof f === 'string' ? (() => { const d = el('div'); d.innerHTML = f; return d.firstChild; })() : f));
    } else {
      footerEl.appendChild(footer);
    }
    modal.appendChild(footerEl);
  }

  backdrop.appendChild(modal);

  function close() {
    backdrop.remove();
    if (typeof onClose === 'function') onClose();
  }

  // Close on backdrop click
  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) close();
  });

  // Close on ESC
  const escHandler = (e) => {
    if (e.key === 'Escape') {
      close();
      document.removeEventListener('keydown', escHandler);
    }
  };
  document.addEventListener('keydown', escHandler);

  // Public API
  backdrop.close = close;
  backdrop.modal = modal;

  document.body.appendChild(backdrop);
  return backdrop;
}

export default Modal;
