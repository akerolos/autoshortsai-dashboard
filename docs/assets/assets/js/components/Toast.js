/**
 * Toast notification system
 */

import { uid } from '../utils.js';
import { getIcon } from '../icons.js';

class ToastManager {
  constructor() {
    this.container = null;
    this.toasts = new Map();
  }

  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  }

  show({ title, message, type = 'info', duration = 4000 }) {
    this.init();

    const id = uid('toast');
    const toast = this._createToast(id, { title, message, type });
    this.container.appendChild(toast);
    this.toasts.set(id, { element: toast, timeout: null });

    // Auto-dismiss
    if (duration > 0) {
      const timeout = setTimeout(() => this.dismiss(id), duration);
      this.toasts.get(id).timeout = timeout;
    }

    // Pause on hover
    toast.addEventListener('mouseenter', () => {
      const t = this.toasts.get(id);
      if (t && t.timeout) clearTimeout(t.timeout);
    });
    toast.addEventListener('mouseleave', () => {
      const t = this.toasts.get(id);
      if (t && duration > 0) {
        t.timeout = setTimeout(() => this.dismiss(id), 1000);
      }
    });

    return id;
  }

  success(title, message, duration) {
    return this.show({ title, message, type: 'success', duration });
  }

  error(title, message, duration) {
    return this.show({ title, message, type: 'error', duration: duration || 6000 });
  }

  warning(title, message, duration) {
    return this.show({ title, message, type: 'warning', duration });
  }

  info(title, message, duration) {
    return this.show({ title, message, type: 'info', duration });
  }

  dismiss(id) {
    const toast = this.toasts.get(id);
    if (!toast) return;
    toast.element.classList.add('toast--leaving');
    setTimeout(() => {
      toast.element.remove();
      this.toasts.delete(id);
    }, 200);
  }

  _createToast(id, { title, message, type }) {
    const icons = {
      success: 'check-circle',
      error: 'alert-triangle',
      warning: 'alert-triangle',
      info: 'info',
    };
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.dataset.id = id;
    toast.innerHTML = `
      <span class="toast__icon">${getIcon(icons[type] || 'info', 20)}</span>
      <div class="toast__content">
        ${title ? `<div class="toast__title">${title}</div>` : ''}
        ${message ? `<div class="toast__message">${message}</div>` : ''}
      </div>
      <span class="toast__close">${getIcon('x', 16)}</span>
    `;
    toast.querySelector('.toast__close').addEventListener('click', () => this.dismiss(id));
    return toast;
  }
}

export const toast = new ToastManager();
export default toast;
