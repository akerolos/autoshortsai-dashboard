/**
 * API client — fetch wrapper with interceptors, error handling, retry
 */

const BASE_URL = '/api/v1';

class ApiClient {
  constructor(baseUrl = BASE_URL) {
    this.baseUrl = baseUrl;
    this.requestInterceptors = [];
    this.responseInterceptors = [];
  }

  async request(path, options = {}) {
    const url = `${this.baseUrl}${path}`;
    const defaultHeaders = { 'Content-Type': 'application/json' };

    const config = {
      ...options,
      headers: { ...defaultHeaders, ...options.headers },
    };

    // Apply request interceptors
    for (const interceptor of this.requestInterceptors) {
      await interceptor(config);
    }

    try {
      const response = await fetch(url, config);

      // Apply response interceptors
      for (const interceptor of this.responseInterceptors) {
        await interceptor(response);
      }

      if (!response.ok) {
        const error = await this._parseError(response);
        throw error;
      }

      // Handle empty responses
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const data = await response.json();
        return data;
      }
      return response.text();
    } catch (err) {
      if (err.name === 'AbortError') throw err;
      // Network errors
      if (err.status === undefined) {
        throw {
          success: false,
          error: {
            code: 'network_error',
            message: 'Network error. Please check your connection.',
          },
        };
      }
      throw err;
    }
  }

  async _parseError(response) {
    try {
      const data = await response.json();
      return {
        success: false,
        status: response.status,
        error: data.error || { code: 'unknown', message: response.statusText },
        request_id: data.request_id,
      };
    } catch {
      return {
        success: false,
        status: response.status,
        error: {
          code: 'http_error',
          message: response.statusText || `HTTP ${response.status}`,
        },
      };
    }
  }

  // HTTP methods
  get(path, params = {}) {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v != null && v !== '')
    ).toString();
    return this.request(`${path}${query ? `?${query}` : ''}`);
  }

  post(path, body = {}) {
    return this.request(path, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  patch(path, body = {}) {
    return this.request(path, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }

  put(path, body = {}) {
    return this.request(path, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  delete(path) {
    return this.request(path, { method: 'DELETE' });
  }

  // Raw download
  async download(path, params = {}) {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v != null && v !== '')
    ).toString();
    const url = `${this.baseUrl}${path}${query ? `?${query}` : ''}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Download failed');
    return response.text();
  }
}

export const api = new ApiClient();

// ===== Convenience API methods =====

export const dashboardApi = {
  getOverview: () => api.get('/dashboard/overview'),
};

export const pipelineApi = {
  getOverview: () => api.get('/pipeline/overview'),
  getToday: () => api.get('/pipeline/today'),
  getRecent: (limit = 10) => api.get('/pipeline/recent', { limit }),
  getRun: (id) => api.get(`/pipeline/${id}`),
  createRun: (targetVideos = 5) => api.post('/pipeline/runs', { target_videos: targetVideos }),
  startRun: (id) => api.post(`/pipeline/runs/${id}/start`),
};

export const videosApi = {
  list: (params = {}) => api.get('/videos', params),
  getRecent: (limit = 5) => api.get('/videos/recent', { limit }),
  get: (id) => api.get(`/videos/${id}`),
};

export const analyticsApi = {
  getOverview: () => api.get('/analytics/overview'),
};

export const logsApi = {
  list: (params = {}) => api.get('/logs', params),
  getSources: () => api.get('/logs/sources'),
  download: (params = {}) => api.download('/logs/download', params),
};

export const settingsApi = {
  getAll: () => api.get('/settings'),
  get: (key) => api.get(`/settings/${key}`),
  update: (key, value) => api.patch(`/settings/${key}`, { value }),
};
