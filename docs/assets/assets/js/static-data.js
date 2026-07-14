/**
 * Static Data Loader
 *
 * يحمل البيانات من ملفات JSON بدلاً من API calls.
 * يُستخدم في وضع GitHub Pages (static hosting).
 *
 * المسارات:
 *   - /data/dashboard/overview.json
 *   - /data/pipeline/overview.json
 *   - /data/pipeline/today.json
 *   - /data/videos.json
 *   - /data/analytics/overview.json
 *   - /data/logs.json
 *   - /data/settings.json
 *   - /data/health.json
 */

const DATA_BASE = './data';

class StaticDataLoader {
  constructor() {
    this.cache = new Map();
    this.basePath = this._detectBasePath();
  }

  /**
   * يحدد المسار الأساسي للملفات.
   * على GitHub Pages: /autoshortsai-dashboard/
   * محلياً: /
   */
  _detectBasePath() {
    const path = window.location.pathname;
    // لو على GitHub Pages (مثلاً /autoshortsai-dashboard/)
    if (path.includes('/autoshortsai-dashboard/')) {
      return '/autoshortsai-dashboard/data';
    }
    // لو محلياً أو في root
    return './data';
  }

  async load(path, useCache = true) {
    const url = `${this.basePath}/${path}`;
    if (useCache && this.cache.has(url)) {
      return this.cache.get(url);
    }

    try {
      const response = await fetch(url);
      if (!response.ok) {
        console.warn(`[StaticData] Failed to load ${path}: ${response.status}`);
        return null;
      }
      const data = await response.json();
      this.cache.set(url, data);
      return data;
    } catch (err) {
      console.error(`[StaticData] Error loading ${path}:`, err);
      return null;
    }
  }

  async getDashboardOverview() {
    return this.load('dashboard/overview.json', false);
  }

  async getPipelineOverview() {
    return this.load('pipeline/overview.json', false);
  }

  async getPipelineToday() {
    return this.load('pipeline/today.json', false);
  }

  async getVideos() {
    return this.load('videos.json', false);
  }

  async getAnalyticsOverview() {
    return this.load('analytics/overview.json', false);
  }

  async getLogs() {
    return this.load('logs.json', false);
  }

  async getSettings() {
    return this.load('settings.json', false);
  }

  async getHealth() {
    return this.load('health.json', false);
  }

  clearCache() {
    this.cache.clear();
  }
}

export const staticData = new StaticDataLoader();
export default staticData;
