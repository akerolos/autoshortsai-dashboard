/**
 * Custom Chart component — Canvas-based, no dependencies
 * Supports: line, bar, donut
 */

import { el, formatNumber, hexToRgba } from '../utils.js';

class Chart {
  constructor(config) {
    this.config = config;
    this.canvas = null;
    this.ctx = null;
    this.container = null;
    this.tooltip = null;
    this.animationProgress = 0;
    this.animationFrame = null;
    this.hoveredIndex = null;
  }

  render() {
    this.container = el('div', { class: 'chart-container' });
    this.canvas = el('canvas');
    this.ctx = this.canvas.getContext('2d');
    this.container.appendChild(this.canvas);

    // Tooltip
    this.tooltip = el('div', { class: 'chart-tooltip' });
    this.container.appendChild(this.tooltip);

    // Setup
    this._setupCanvas();
    this._bindEvents();

    // Animate
    this._animate();

    return this.container;
  }

  _setupCanvas() {
    const dpr = window.devicePixelRatio || 1;
    const rect = this.container.getBoundingClientRect();
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width = `${rect.width}px`;
    this.canvas.style.height = `${rect.height}px`;
    this.ctx.scale(dpr, dpr);
    this.width = rect.width;
    this.height = rect.height;
  }

  _bindEvents() {
    this.canvas.addEventListener('mousemove', (e) => this._onMouseMove(e));
    this.canvas.addEventListener('mouseleave', () => this._onMouseLeave());

    // Resize handling
    const resizeObserver = new ResizeObserver(() => this._onResize());
    resizeObserver.observe(this.container);
    this._resizeObserver = resizeObserver;
  }

  _onResize() {
    this._setupCanvas();
    this._draw();
  }

  _onMouseMove(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    this.hoveredIndex = this._getHoveredIndex(x, y);
    this._draw();
    if (this.hoveredIndex != null) {
      this._showTooltip(x, y, this.hoveredIndex);
    } else {
      this._hideTooltip();
    }
  }

  _onMouseLeave() {
    this.hoveredIndex = null;
    this._draw();
    this._hideTooltip();
  }

  _animate() {
    const duration = 600;
    const start = performance.now();
    const animate = (now) => {
      const elapsed = now - start;
      this.animationProgress = Math.min(elapsed / duration, 1);
      // Easing
      this.animationProgress = 1 - Math.pow(1 - this.animationProgress, 3);
      this._draw();
      if (elapsed < duration) {
        this.animationFrame = requestAnimationFrame(animate);
      }
    };
    this.animationFrame = requestAnimationFrame(animate);
  }

  _draw() {
    this.ctx.clearRect(0, 0, this.width, this.height);
    const type = this.config.type;
    if (type === 'line') this._drawLine();
    else if (type === 'bar') this._drawBar();
    else if (type === 'donut') this._drawDonut();
  }

  // ===== Line Chart =====
  _drawLine() {
    const { series, x_labels: xLabels } = this.config;
    if (!series || series.length === 0) return;

    const padding = { top: 16, right: 16, bottom: 28, left: 48 };
    const chartWidth = this.width - padding.left - padding.right;
    const chartHeight = this.height - padding.top - padding.bottom;

    // Find max value
    let maxValue = 0;
    series.forEach(s => {
      s.points.forEach(p => {
        maxValue = Math.max(maxValue, p.value);
      });
    });
    maxValue = maxValue * 1.1 || 1;

    // Grid lines
    this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
    this.ctx.lineWidth = 1;
    const gridLines = 5;
    for (let i = 0; i <= gridLines; i++) {
      const y = padding.top + (chartHeight / gridLines) * i;
      this.ctx.beginPath();
      this.ctx.moveTo(padding.left, y);
      this.ctx.lineTo(this.width - padding.right, y);
      this.ctx.stroke();

      // Y-axis labels
      const value = maxValue - (maxValue / gridLines) * i;
      this.ctx.fillStyle = '#71717A';
      this.ctx.font = '10px Inter, sans-serif';
      this.ctx.textAlign = 'right';
      this.ctx.fillText(formatNumber(value), padding.left - 8, y + 3);
    }

    // X-axis labels (sparse)
    const labelStep = Math.max(1, Math.ceil(xLabels.length / 7));
    this.ctx.fillStyle = '#71717A';
    this.ctx.font = '10px Inter, sans-serif';
    this.ctx.textAlign = 'center';
    xLabels.forEach((label, i) => {
      if (i % labelStep === 0 || i === xLabels.length - 1) {
        const x = padding.left + (chartWidth / Math.max(1, xLabels.length - 1)) * i;
        const date = new Date(label);
        const shortLabel = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        this.ctx.fillText(shortLabel, x, this.height - 8);
      }
    });

    // Draw each series
    series.forEach((s, seriesIdx) => {
      const points = s.points;
      if (points.length === 0) return;

      const pointStep = chartWidth / Math.max(1, points.length - 1);
      const visiblePoints = Math.floor(points.length * this.animationProgress);

      // Gradient fill
      const gradient = this.ctx.createLinearGradient(0, padding.top, 0, padding.top + chartHeight);
      gradient.addColorStop(0, hexToRgba(s.color, 0.20));
      gradient.addColorStop(1, hexToRgba(s.color, 0.0));

      // Fill area
      this.ctx.beginPath();
      this.ctx.moveTo(padding.left, padding.top + chartHeight);
      for (let i = 0; i <= visiblePoints && i < points.length; i++) {
        const x = padding.left + pointStep * i;
        const y = padding.top + chartHeight - (points[i].value / maxValue) * chartHeight;
        if (i === 0) this.ctx.lineTo(x, y);
        else this.ctx.lineTo(x, y);
      }
      this.ctx.lineTo(padding.left + pointStep * visiblePoints, padding.top + chartHeight);
      this.ctx.closePath();
      this.ctx.fillStyle = gradient;
      this.ctx.fill();

      // Line
      this.ctx.beginPath();
      this.ctx.strokeStyle = s.color;
      this.ctx.lineWidth = 2;
      this.ctx.lineJoin = 'round';
      this.ctx.lineCap = 'round';
      for (let i = 0; i <= visiblePoints && i < points.length; i++) {
        const x = padding.left + pointStep * i;
        const y = padding.top + chartHeight - (points[i].value / maxValue) * chartHeight;
        if (i === 0) this.ctx.moveTo(x, y);
        else this.ctx.lineTo(x, y);
      }
      this.ctx.stroke();

      // Hover point
      if (this.hoveredIndex != null && this.hoveredIndex < points.length) {
        const x = padding.left + pointStep * this.hoveredIndex;
        const y = padding.top + chartHeight - (points[this.hoveredIndex].value / maxValue) * chartHeight;
        this.ctx.beginPath();
        this.ctx.arc(x, y, 5, 0, Math.PI * 2);
        this.ctx.fillStyle = s.color;
        this.ctx.fill();
        this.ctx.beginPath();
        this.ctx.arc(x, y, 8, 0, Math.PI * 2);
        this.ctx.fillStyle = hexToRgba(s.color, 0.2);
        this.ctx.fill();

        // Vertical line
        this.ctx.beginPath();
        this.ctx.strokeStyle = hexToRgba(s.color, 0.3);
        this.ctx.lineWidth = 1;
        this.ctx.setLineDash([3, 3]);
        this.ctx.moveTo(x, padding.top);
        this.ctx.lineTo(x, padding.top + chartHeight);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
      }
    });
  }

  // ===== Bar Chart =====
  _drawBar() {
    const { series, x_labels: xLabels } = this.config;
    if (!series || series.length === 0) return;

    const padding = { top: 16, right: 16, bottom: 28, left: 48 };
    const chartWidth = this.width - padding.left - padding.right;
    const chartHeight = this.height - padding.top - padding.bottom;

    let maxValue = 0;
    series.forEach(s => s.points.forEach(p => maxValue = Math.max(maxValue, p.value)));
    maxValue = maxValue * 1.1 || 1;

    // Grid
    this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
    this.ctx.lineWidth = 1;
    const gridLines = 5;
    for (let i = 0; i <= gridLines; i++) {
      const y = padding.top + (chartHeight / gridLines) * i;
      this.ctx.beginPath();
      this.ctx.moveTo(padding.left, y);
      this.ctx.lineTo(this.width - padding.right, y);
      this.ctx.stroke();

      const value = maxValue - (maxValue / gridLines) * i;
      this.ctx.fillStyle = '#71717A';
      this.ctx.font = '10px Inter, sans-serif';
      this.ctx.textAlign = 'right';
      this.ctx.fillText(formatNumber(value), padding.left - 8, y + 3);
    }

    const s = series[0];
    const points = s.points;
    const barCount = points.length;
    const barWidth = (chartWidth / barCount) * 0.6;
    const barGap = (chartWidth / barCount) * 0.4;
    const visibleBars = Math.floor(barCount * this.animationProgress);

    points.forEach((p, i) => {
      if (i > visibleBars) return;
      const x = padding.left + (chartWidth / barCount) * i + barGap / 2;
      const fullHeight = (p.value / maxValue) * chartHeight;
      const animHeight = i === visibleBars ? fullHeight * (this.animationProgress * barCount - visibleBars) : fullHeight;
      const y = padding.top + chartHeight - animHeight;

      // Bar
      const gradient = this.ctx.createLinearGradient(0, y, 0, padding.top + chartHeight);
      gradient.addColorStop(0, s.color);
      gradient.addColorStop(1, hexToRgba(s.color, 0.4));
      this.ctx.fillStyle = i === this.hoveredIndex ? hexToRgba(s.color, 1) : gradient;

      const radius = Math.min(3, barWidth / 2);
      this._roundRect(x, y, barWidth, animHeight, radius);
      this.ctx.fill();

      // X label
      if (i % Math.max(1, Math.ceil(barCount / 7)) === 0 || i === barCount - 1) {
        const date = new Date(p.date || xLabels[i]);
        const shortLabel = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        this.ctx.fillStyle = '#71717A';
        this.ctx.font = '10px Inter, sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(shortLabel, x + barWidth / 2, this.height - 8);
      }
    });
  }

  // ===== Donut Chart =====
  _drawDonut() {
    const { series } = this.config;
    if (!series || series.length === 0) return;

    const cx = this.width / 2;
    const cy = this.height / 2;
    const radius = Math.min(this.width, this.height) / 2 - 20;
    const innerRadius = radius * 0.65;

    const total = series.reduce((sum, s) => sum + s.value, 0) || 1;
    let startAngle = -Math.PI / 2;
    const animTotal = total * this.animationProgress;
    let drawnTotal = 0;

    series.forEach((s, idx) => {
      const sliceAngle = (s.value / total) * Math.PI * 2;
      const remaining = animTotal - drawnTotal;
      if (remaining <= 0) return;
      const actualAngle = Math.min(sliceAngle, (remaining / total) * Math.PI * 2);
      const isHovered = idx === this.hoveredIndex;

      this.ctx.beginPath();
      this.ctx.arc(cx, cy, isHovered ? radius + 4 : radius, startAngle, startAngle + actualAngle);
      this.ctx.arc(cx, cy, innerRadius, startAngle + actualAngle, startAngle, true);
      this.ctx.closePath();
      this.ctx.fillStyle = s.color;
      this.ctx.fill();

      startAngle += sliceAngle;
      drawnTotal += s.value;
    });

    // Center text
    this.ctx.fillStyle = '#FAFAFA';
    this.ctx.font = 'bold 24px Inter, sans-serif';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(formatNumber(total), cx, cy - 6);
    this.ctx.fillStyle = '#71717A';
    this.ctx.font = '11px Inter, sans-serif';
    this.ctx.fillText('Total', cx, cy + 14);
  }

  _roundRect(x, y, w, h, r) {
    if (h < 1) return;
    r = Math.min(r, w / 2, h / 2);
    this.ctx.beginPath();
    this.ctx.moveTo(x + r, y);
    this.ctx.lineTo(x + w - r, y);
    this.ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    this.ctx.lineTo(x + w, y + h);
    this.ctx.lineTo(x, y + h);
    this.ctx.lineTo(x, y + r);
    this.ctx.quadraticCurveTo(x, y, x + r, y);
    this.ctx.closePath();
  }

  _getHoveredIndex(x, y) {
    const { type, series } = this.config;
    if (!series || series.length === 0) return null;

    if (type === 'line' || type === 'bar') {
      const padding = { left: 48, right: 16 };
      const chartWidth = this.width - padding.left - padding.right;
      const points = series[0].points;
      const step = chartWidth / Math.max(1, points.length - 1);
      const idx = Math.round((x - padding.left) / step);
      if (idx >= 0 && idx < points.length) return idx;
    } else if (type === 'donut') {
      const cx = this.width / 2;
      const cy = this.height / 2;
      const dx = x - cx;
      const dy = y - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const radius = Math.min(this.width, this.height) / 2 - 20;
      const innerRadius = radius * 0.65;
      if (dist >= innerRadius && dist <= radius + 4) {
        let angle = Math.atan2(dy, dx) + Math.PI / 2;
        if (angle < 0) angle += Math.PI * 2;
        const total = series.reduce((sum, s) => sum + s.value, 0) || 1;
        let cumulative = 0;
        for (let i = 0; i < series.length; i++) {
          cumulative += series[i].value / total;
          if (angle <= cumulative * Math.PI * 2) return i;
        }
      }
    }
    return null;
  }

  _showTooltip(x, y, idx) {
    const { type, series, unit } = this.config;
    let content = '';
    if (type === 'line' || type === 'bar') {
      const point = series[0].points[idx];
      if (!point) return;
      const date = new Date(point.date || this.config.x_labels[idx]);
      content = `
        <div class="chart-tooltip__label">${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</div>
        <div class="chart-tooltip__value">${formatNumber(point.value)}${unit || ''}</div>
      `;
    } else if (type === 'donut') {
      const s = series[idx];
      if (!s) return;
      const total = series.reduce((sum, x) => sum + x.value, 0);
      const pct = ((s.value / total) * 100).toFixed(1);
      content = `
        <div class="chart-tooltip__label">${s.name}</div>
        <div class="chart-tooltip__value">${formatNumber(s.value)} (${pct}%)</div>
      `;
    }
    this.tooltip.innerHTML = content;
    this.tooltip.style.left = `${x}px`;
    this.tooltip.style.top = `${y}px`;
    this.tooltip.classList.add('is-visible');
  }

  _hideTooltip() {
    this.tooltip.classList.remove('is-visible');
  }

  destroy() {
    if (this.animationFrame) cancelAnimationFrame(this.animationFrame);
    if (this._resizeObserver) this._resizeObserver.disconnect();
  }
}

export function createChart(config) {
  const chart = new Chart(config);
  return chart;
}

export default Chart;
