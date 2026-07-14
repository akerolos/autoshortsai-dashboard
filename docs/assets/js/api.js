/**
 * API client — يدعم وضعين:
 * 1. Live mode: يطلب من /api/v1/* (لما السيرفر شغال)
 * 2. Static mode: يقرأ من /data/*.json (على GitHub Pages)
 *
 * بيختار الوضع تلقائياً بناءً على:
 * - لو الصفحة على GitHub Pages → static mode
 * - لو على localhost أو domain تاني بـ /api/v1 → live mode
 */

import { staticData } from './static-data.js';

const BASE_URL = '/api/v1';

// تحديد الوضع تلقائياً
// static mode = على github.io، أو مفيش API server (port مش 8000)، أو ?static=true
const isGitHubPages = window.location.hostname.includes('github.io');
const isLocalStatic = window.location.port !== '8000' && !window.location.hostname.includes('localhost:8000');
const STATIC_MODE = isGitHubPages ||
                     isLocalStatic ||
                     window.location.search.includes('static=true');

console.log(`[API] Mode: ${STATIC_MODE ? 'STATIC (GitHub Pages)' : 'LIVE (FastAPI)'}`);
console.log(`[API] Hostname: ${window.location.hostname}, Port: ${window.location.port}`);


class ApiClient {
  constructor(baseUrl = BASE_URL) {
    this.baseUrl = baseUrl;
    this.staticMode = STATIC_MODE;
  }

  async request(path, options = {}) {
    if (this.staticMode) {
      return null; // الـ static mode بيستخدم دوال staticData مباشرة
    }

    const url = `${this.baseUrl}${path}`;
    const defaultHeaders = { 'Content-Type': 'application/json' };
    const config = {
      ...options,
      headers: { ...defaultHeaders, ...options.headers },
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        throw await this._parseError(response);
      }
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        return await response.json();
      }
      return response.text();
    } catch (err) {
      if (err.status === undefined) {
        throw {
          success: false,
          error: { code: 'network_error', message: 'Network error.' },
        };
      }
      throw err;
    }
  }

  async _parseError(response) {
    try {
      const data = await response.json();
      return { success: false, status: response.status, error: data.error || {} };
    } catch {
      return { success: false, status: response.status, error: { code: 'http_error', message: `HTTP ${response.status}` } };
    }
  }

  get(path, params = {}) {
    const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== '')).toString();
    return this.request(`${path}${query ? `?${query}` : ''}`);
  }

  async download(path, params = {}) {
    const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== '')).toString();
    const url = `${this.baseUrl}${path}${query ? `?${query}` : ''}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Download failed');
    return response.text();
  }
}

export const api = new ApiClient();

// ===== Convenience API methods (تدعم الوضعين) =====

export const dashboardApi = {
  async getOverview() {
    if (STATIC_MODE) {
      const data = await staticData.getDashboardOverview();
      return { success: true, data };
    }
    return api.get('/dashboard/overview');
  },
};

export const pipelineApi = {
  async getOverview() {
    if (STATIC_MODE) {
      const data = await staticData.getPipelineOverview();
      return { success: true, data };
    }
    return api.get('/pipeline/overview');
  },
  async getToday() {
    if (STATIC_MODE) {
      const data = await staticData.getPipelineToday();
      return { success: true, data };
    }
    return api.get('/pipeline/today');
  },
  async getRecent(limit = 10) {
    if (STATIC_MODE) {
      const data = await staticData.getPipelineOverview();
      return { success: true, data: { data: data?.recent_runs || [] } };
    }
    return api.get('/pipeline/recent', { limit });
  },
};

export const videosApi = {
  async list(params = {}) {
    if (STATIC_MODE) {
      const data = await staticData.getVideos();
      return { success: true, data };
    }
    return api.get('/videos', params);
  },
  async getRecent(limit = 5) {
    if (STATIC_MODE) {
      const data = await staticData.getVideos();
      const items = (data?.items || []).slice(0, limit);
      return { success: true, data: items };
    }
    return api.get('/videos/recent', { limit });
  },
};

export const analyticsApi = {
  async getOverview() {
    if (STATIC_MODE) {
      const data = await staticData.getAnalyticsOverview();
      return { success: true, data };
    }
    return api.get('/analytics/overview');
  },
};

export const logsApi = {
  async list(params = {}) {
    if (STATIC_MODE) {
      const data = await staticData.getLogs();
      // محاكاة فلترة بسيطة
      let items = data?.items || [];
      if (params.level) {
        items = items.filter(l => l.level === params.level.toUpperCase());
      }
      if (params.search) {
        const q = params.search.toLowerCase();
        items = items.filter(l => l.message.toLowerCase().includes(q));
      }
      return {
        success: true,
        data: {
          items,
          pagination: {
            page: 1, page_size: items.length, total: items.length,
            total_pages: 1, has_next: false, has_prev: false,
          },
        },
      };
    }
    return api.get('/logs', params);
  },
  async getSources() {
    if (STATIC_MODE) {
      const data = await staticData.getLogs();
      return { success: true, data: data?.sources || [] };
    }
    return api.get('/logs/sources');
  },
  async download(params = {}) {
    if (STATIC_MODE) {
      const data = await staticData.getLogs();
      const logs = data?.items || [];
      return logs.map(l => `[${l.created_at}] [${l.level}] [${l.source}] ${l.message}`).join('\n');
    }
    return api.download('/logs/download', params);
  },
};

export const settingsApi = {
  async getAll() {
    if (STATIC_MODE) {
      const data = await staticData.getSettings();
      return { success: true, data };
    }
    return api.get('/settings');
  },
  async update(key, value) {
    if (STATIC_MODE) {
      console.warn('[Settings] Update not available in static mode');
      return { success: false, error: { message: 'Static mode — read only' } };
    }
    return api.request(`/settings/${key}`, {
      method: 'PATCH',
      body: JSON.stringify({ value }),
    });
  },
};
