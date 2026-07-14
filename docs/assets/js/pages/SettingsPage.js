/**
 * Settings Page — configuration management
 */

import { el } from '../utils.js';
import { getIcon } from '../icons.js';
import { settingsApi } from '../api.js';
import Card from '../components/Card.js';
import toast from '../components/Toast.js';
import events from '../events.js';

let refreshHandler = null;
let allSettings = [];
let activeCategory = 'production';

const CATEGORY_LABELS = {
  production: { label: 'Production', icon: 'film' },
  narrator: { label: 'Narrator', icon: 'mic' },
  upload: { label: 'Upload', icon: 'upload' },
  render: { label: 'Render', icon: 'cpu' },
  ui: { label: 'Interface', icon: 'settings' },
  channels: { label: 'Channels', icon: 'users' },
};

const SELECT_OPTIONS = {
  narrator_voice: [
    { value: 'ar-MA-Jawad', label: 'Jawad (Arabic, Morocco)' },
    { value: 'ar-EG-Salma', label: 'Salma (Arabic, Egypt)' },
    { value: 'ar-SA-Hamed', label: 'Hamed (Arabic, Saudi)' },
    { value: 'en-US-Guy', label: 'Guy (English, US)' },
    { value: 'en-GB-Anne', label: 'Anne (English, UK)' },
  ],
  category: [
    { value: 'technology', label: 'Technology' },
    { value: 'programming', label: 'Programming' },
    { value: 'ai', label: 'AI & Machine Learning' },
    { value: 'web-dev', label: 'Web Development' },
    { value: 'tutorial', label: 'Tutorial' },
    { value: 'entertainment', label: 'Entertainment' },
  ],
  output_resolution: [
    { value: '1080x1920', label: '1080×1920 (Vertical HD)' },
    { value: '720x1280', label: '720×1280 (Vertical SD)' },
    { value: '1920x1080', label: '1920×1080 (Horizontal HD)' },
    { value: '3840x2160', label: '3840×2160 (4K)' },
  ],
  subtitle_style: [
    { value: 'modern-bold', label: 'Modern Bold' },
    { value: 'classic', label: 'Classic' },
    { value: 'minimal', label: 'Minimal' },
    { value: 'neon', label: 'Neon Glow' },
    { value: 'boxed', label: 'Boxed' },
  ],
  theme: [
    { value: 'dark', label: 'Dark' },
    { value: 'light', label: 'Light' },
  ],
  language: [
    { value: 'ar', label: 'العربية' },
    { value: 'en', label: 'English' },
  ],
};

export function render() {
  const main = el('div');
  main.innerHTML = `
    <div class="main__inner">
      <div class="page-header">
        <div class="page-header__title">
          <h1>Settings</h1>
          <span class="page-header__subtitle">Configure your AutoShortsAI pipeline</span>
        </div>
        <div class="page-header__actions">
          <button class="btn btn--primary btn--sm" id="save-all-btn">
            ${getIcon('save', 16)}
            <span>Save Changes</span>
          </button>
        </div>
      </div>

      <div class="settings__layout">
        <div class="settings__sidebar" id="settings-nav"></div>
        <div class="settings__content" id="settings-content">
          <div class="card">
            <div class="spinner spinner--lg spinner--center" style="margin: var(--space-12) auto;"></div>
          </div>
        </div>
      </div>
    </div>
  `;
  return main;
}

export async function mount() {
  await loadSettings();

  document.getElementById('save-all-btn')?.addEventListener('click', saveAll);

  refreshHandler = () => loadSettings();
  events.on('page:refresh', refreshHandler);

  return () => {
    if (refreshHandler) events.off('page:refresh', refreshHandler);
  };
}

async function loadSettings() {
  try {
    const response = await settingsApi.getAll();
    if (response.success) {
      allSettings = response.data.all;
      renderSettingsNav(response.data.groups);
      renderSettingsContent();
    }
  } catch (err) {
    toast.error('Failed to load settings', err.error?.message || 'Unknown error');
  }
}

function renderSettingsNav(groups) {
  const nav = document.getElementById('settings-nav');
  if (!nav) return;
  nav.innerHTML = '';

  groups.forEach(group => {
    const item = el('div', {
      class: `settings__nav-item ${group.category === activeCategory ? 'is-active' : ''}`,
      dataset: { category: group.category },
    });
    const catInfo = CATEGORY_LABELS[group.category] || { label: group.category, icon: 'settings' };
    item.innerHTML = `
      ${getIcon(catInfo.icon, 16)}
      <span>${catInfo.label}</span>
    `;
    item.addEventListener('click', () => {
      activeCategory = group.category;
      document.querySelectorAll('.settings__nav-item').forEach(n => n.classList.remove('is-active'));
      item.classList.add('is-active');
      renderSettingsContent();
    });
    nav.appendChild(item);
  });
}

function renderSettingsContent() {
  const content = document.getElementById('settings-content');
  if (!content) return;
  content.innerHTML = '';

  const categorySettings = allSettings.filter(s => s.category === activeCategory);
  if (categorySettings.length === 0) {
    content.innerHTML = `
      <div class="card">
        <div class="empty-state">
          <div class="empty-state__title">No settings in this category</div>
        </div>
      </div>
    `;
    return;
  }

  const catInfo = CATEGORY_LABELS[activeCategory] || { label: activeCategory };
  const card = Card({
    title: catInfo.label,
    subtitle: `${categorySettings.length} setting${categorySettings.length !== 1 ? 's' : ''}`,
    body: '',
  });

  const body = card.querySelector('.card__body');
  categorySettings.forEach(setting => {
    body.appendChild(renderSettingRow(setting));
  });

  content.appendChild(card);
}

function renderSettingRow(setting) {
  const row = el('div', { class: 'setting-row', dataset: { key: setting.key } });

  const info = el('div', { class: 'setting-row__info' });
  info.innerHTML = `
    <div class="setting-row__label">${formatLabel(setting.key)}</div>
    ${setting.description ? `<div class="setting-row__description">${setting.description}</div>` : ''}
  `;
  row.appendChild(info);

  const control = el('div', { class: 'setting-row__control' });
  control.appendChild(renderControl(setting));
  row.appendChild(control);

  return row;
}

function renderControl(setting) {
  const options = SELECT_OPTIONS[setting.key];

  if (options) {
    // Select dropdown
    const select = el('select', { class: 'select', dataset: { key: setting.key, type: setting.value_type } });
    options.forEach(opt => {
      const option = el('option', { value: opt.value }, opt.label);
      if (opt.value === setting.value) option.setAttribute('selected', '');
      select.appendChild(option);
    });
    select.addEventListener('change', (e) => {
      updateSetting(setting.key, e.target.value);
    });
    return select;
  }

  if (setting.value_type === 'bool') {
    // Toggle
    const toggle = el('label', { class: 'toggle' });
    const input = el('input', {
      type: 'checkbox',
      class: 'toggle__input',
      dataset: { key: setting.key, type: 'bool' },
    });
    if (setting.value === 'true') input.setAttribute('checked', '');
    input.addEventListener('change', (e) => {
      updateSetting(setting.key, e.target.checked ? 'true' : 'false');
    });
    const slider = el('span', { class: 'toggle__slider' });
    toggle.appendChild(input);
    toggle.appendChild(slider);
    return toggle;
  }

  if (setting.value_type === 'int' || setting.value_type === 'float') {
    // Number input
    const input = el('input', {
      type: 'number',
      class: 'input',
      value: setting.value,
      dataset: { key: setting.key, type: setting.value_type },
      step: setting.value_type === 'float' ? '0.1' : '1',
    });
    input.addEventListener('change', (e) => {
      updateSetting(setting.key, e.target.value);
    });
    return input;
  }

  // Default: text input
  const input = el('input', {
    type: 'text',
    class: 'input',
    value: setting.value,
    dataset: { key: setting.key, type: setting.value_type },
  });
  input.addEventListener('change', (e) => {
    updateSetting(setting.key, e.target.value);
  });
  return input;
}

async function updateSetting(key, value) {
  try {
    const response = await settingsApi.update(key, value);
    if (response.success) {
      // Update local state
      const setting = allSettings.find(s => s.key === key);
      if (setting) setting.value = value;

      toast.success('Setting updated', `${formatLabel(key)} has been updated.`);

      // Special handling for theme
      if (key === 'theme') {
        document.documentElement.setAttribute('data-theme', value);
      }
    }
  } catch (err) {
    toast.error('Update failed', err.error?.message || 'Unknown error');
    // Reload to revert
    loadSettings();
  }
}

function saveAll() {
  // In our implementation, settings are saved on change
  // This button can trigger a full re-validation or batch operation
  toast.success('All changes saved', 'Your settings are up to date.');
}

function formatLabel(key) {
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export default { render, mount };
