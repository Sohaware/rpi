<?php
require_once __DIR__ . '/config.php';
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title><?= htmlspecialchars($dashboard_title, ENT_QUOTES, 'UTF-8') ?></title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
:root {
    --bg: #f3f5f9;
    --card-bg: #ffffff;
    --text: #1f2937;
    --muted: #6b7280;
    --border: #e5e7eb;
    --danger: #b91c1c;

    --red: #ef4444;
    --green: #22c55e;
    --blue: #3b82f6;
    --yellow: #eab308;

    --red-soft: #fee2e2;
    --green-soft: #dcfce7;
    --blue-soft: #dbeafe;
    --yellow-soft: #fef9c3;
}

* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    background: var(--bg);
    color: var(--text);
}

.header {
    min-height: 72px;
    background: #ffffff;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 24px;
    position: sticky;
    top: 0;
    z-index: 10;
}

.logo-box {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: var(--blue-soft);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    flex-shrink: 0;
}

.logo-box img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
}

.logo-placeholder {
    font-weight: 700;
    color: var(--blue);
}

.header-title {
    font-size: 22px;
    font-weight: 700;
}

.header-subtitle {
    font-size: 13px;
    color: var(--muted);
    margin-top: 2px;
}

.container { padding: 24px; }

.grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 18px;
}

.card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-top: 5px solid var(--blue);
    border-radius: 16px;
    min-height: 240px;
    height: 240px;
    padding: 16px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.card-red { border-top-color: var(--red); }
.card-green { border-top-color: var(--green); }
.card-blue { border-top-color: var(--blue); }
.card-yellow { border-top-color: var(--yellow); }
.card-error { border-top-color: var(--danger); background: #fff7f7; }

.card-title {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 10px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.card-body {
    flex: 1;
    min-height: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
}

.card-description {
    font-size: 12px;
    color: var(--muted);
    margin-top: 10px;
    line-height: 1.35;
    max-height: 34px;
    overflow: hidden;
}

.value-text {
    font-size: 20px;
    font-weight: 700;
    margin-top: 10px;
    text-align: center;
}

.small-note {
    font-size: 12px;
    color: var(--muted);
    margin-top: 8px;
}

.empty-state, .load-error {
    grid-column: 1 / -1;
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    color: var(--muted);
}

.load-error { color: var(--danger); }

/* LED */
.led-wrap { display: flex; flex-direction: column; align-items: center; justify-content: center; }
.led {
    width: 78px;
    height: 78px;
    border-radius: 50%;
    border: 4px solid #e5e7eb;
    background: #9ca3af;
    box-shadow: inset 0 0 16px rgba(0,0,0,0.22);
}
.card-red .led-on { background: var(--red); box-shadow: 0 0 24px rgba(239, 68, 68, 0.75); }
.card-green .led-on { background: var(--green); box-shadow: 0 0 24px rgba(34, 197, 94, 0.75); }
.card-blue .led-on { background: var(--blue); box-shadow: 0 0 24px rgba(59, 130, 246, 0.75); }
.card-yellow .led-on { background: var(--yellow); box-shadow: 0 0 24px rgba(234, 179, 8, 0.75); }
.led-off { background: #9ca3af; }

/* Gauge */
.gauge-wrap { width: 100%; text-align: center; }
.gauge-svg { width: 100%; max-width: 180px; height: auto; }
.gauge-bg { fill: none; stroke: #e5e7eb; stroke-width: 12; stroke-linecap: round; }
.gauge-fill {
    fill: none;
    stroke: var(--blue);
    stroke-width: 12;
    stroke-linecap: round;
    stroke-dasharray: 141.4;
    stroke-dashoffset: 141.4;
    transition: stroke-dashoffset 0.25s ease;
}
.card-red .gauge-fill { stroke: var(--red); }
.card-green .gauge-fill { stroke: var(--green); }
.card-blue .gauge-fill { stroke: var(--blue); }
.card-yellow .gauge-fill { stroke: var(--yellow); }
.gauge-needle {
    stroke: #111827;
    stroke-width: 3;
    stroke-linecap: round;
    transform-origin: 60px 60px;
    transition: transform 0.25s ease;
}
.gauge-center { fill: #111827; }

/* Text/info */
.dash-textarea, .dash-info {
    width: 100%;
    height: 120px;
    resize: none;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px;
    font-size: 15px;
    outline: none;
    font-family: inherit;
    background: #fff;
}
.dash-info { background: #f9fafb; color: #374151; }
.dash-textarea:focus { border-color: var(--blue); box-shadow: 0 0 0 3px var(--blue-soft); }

/* Button and switch */
.dash-button {
    width: 100%;
    max-width: 190px;
    padding: 14px 18px;
    border: none;
    border-radius: 14px;
    color: white;
    background: var(--blue);
    font-size: 17px;
    font-weight: 700;
    cursor: pointer;
}
.card-red .dash-button { background: var(--red); }
.card-green .dash-button { background: var(--green); }
.card-blue .dash-button { background: var(--blue); }
.card-yellow .dash-button { background: var(--yellow); color: #1f2937; }
.dash-button:active { transform: scale(0.97); }
.dash-button:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }

.switch-wrap {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
}
.dash-switch {
    width: 92px;
    height: 48px;
    border: none;
    border-radius: 999px;
    background: #cbd5e1;
    position: relative;
    cursor: pointer;
    transition: background 0.2s ease;
    padding: 0;
}
.dash-switch::after {
    content: '';
    position: absolute;
    width: 38px;
    height: 38px;
    top: 5px;
    left: 5px;
    border-radius: 50%;
    background: #ffffff;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.28);
    transition: transform 0.2s ease;
}
.dash-switch-on { background: var(--blue); }
.card-red .dash-switch-on { background: var(--red); }
.card-green .dash-switch-on { background: var(--green); }
.card-blue .dash-switch-on { background: var(--blue); }
.card-yellow .dash-switch-on { background: var(--yellow); }
.dash-switch-on::after { transform: translateX(44px); }
.switch-state { font-size: 13px; color: var(--muted); font-weight: 700; }

/* Slider */
.dash-slider { width: 100%; cursor: pointer; }

/* Graphs and charts */
.graph-canvas, .chart-canvas {
    width: 100%;
    aspect-ratio: 360 / 155;
    height: auto;
    max-height: 155px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: #ffffff;
    display: block;
    flex: 0 0 auto;
}
.graph-note, .chart-note {
    font-size: 12px;
    color: var(--muted);
    margin-top: 6px;
    width: 100%;
    line-height: 1.25;
    overflow: hidden;
}
.graph-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 5px 9px;
    justify-content: center;
    max-height: 32px;
    overflow: hidden;
}
.legend-item { white-space: nowrap; }
.legend-dot {
    display: inline-block;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    margin-right: 4px;
    vertical-align: -1px;
}

/* Table */
.table-wrap {
    width: 100%;
    height: 150px;
    overflow: auto;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: #fff;
}
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
.data-table th, .data-table td {
    padding: 7px 8px;
    border-bottom: 1px solid var(--border);
    text-align: left;
    vertical-align: top;
    word-break: break-word;
}
.data-table th {
    position: sticky;
    top: 0;
    background: #f9fafb;
    font-size: 12px;
    color: var(--muted);
    z-index: 1;
}
.table-error, .table-empty {
    padding: 12px;
    color: var(--muted);
    font-size: 13px;
}
.table-error { color: var(--danger); }

.error-list {
    margin: 8px 0 0 0;
    padding-left: 18px;
    color: var(--danger);
    font-size: 13px;
    line-height: 1.4;
}

@media (max-width: 1200px) { .grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 900px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 560px) {
    .header { padding: 12px 16px; }
    .header-title { font-size: 18px; }
    .container { padding: 16px; }
    .grid { grid-template-columns: 1fr; }
    .card { height: 230px; min-height: 230px; }
}
</style>
</head>
<body>

<header class="header">
    <div class="logo-box">
        <img src="<?= htmlspecialchars($logo_path, ENT_QUOTES, 'UTF-8') ?>" alt="Logo" onerror="this.style.display='none'; this.parentNode.querySelector('.logo-placeholder').style.display='block';">
        <div class="logo-placeholder" style="display:none;">IoT</div>
    </div>
    <div>
        <div class="header-title"><?= htmlspecialchars($dashboard_title, ENT_QUOTES, 'UTF-8') ?></div>
        <div class="header-subtitle"><?= htmlspecialchars($dashboard_subtitle, ENT_QUOTES, 'UTF-8') ?></div>
    </div>
</header>

<main class="container">
    <div class="grid" id="dashboardGrid">
        <div class="empty-state">Loading dashboard...</div>
    </div>
</main>

<script>
const POLL_INTERVAL_MS = <?= (int)$poll_interval_ms ?>;
const grid = document.getElementById('dashboardGrid');
const saveTimers = {};
const editingTextareaValues = {};
let isRenderingCards = false;
let firstLoadComplete = false;
let latestCards = [];

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function normalizeType(type) {
    type = String(type || '').toLowerCase().trim();
    return type === 'guage' ? 'gauge' : type;
}

function normalizeColor(color) {
    color = String(color || '').toLowerCase().trim();
    return ['red', 'green', 'blue', 'yellow'].includes(color) ? color : 'blue';
}

function numeric(value, fallback = 0) {
    const n = parseFloat(value);
    return Number.isFinite(n) ? n : fallback;
}

function niceNumber(value, digits = 2) {
    const n = Number(value);
    if (!Number.isFinite(n)) return String(value ?? '');
    if (Number.isInteger(n)) return String(n);
    return String(Number(n.toFixed(digits)));
}

function isOn(value) {
    value = String(value || '').toLowerCase().trim();
    return ['on', 'true', '1', 'yes'].includes(value);
}

function apiSet(id, value) {
    const formData = new FormData();
    formData.append('id', id);
    formData.append('value', value);

    return fetch('cards.php?action=set', {
        method: 'POST',
        body: formData
    }).then(response => response.json());
}

function debounceSet(id, value, delay = 400) {
    clearTimeout(saveTimers[id]);
    saveTimers[id] = setTimeout(() => apiSet(id, value).catch(console.error), delay);
}

function renderCardShell(card) {
    const id = escapeHtml(card.id);
    const type = normalizeType(card.type);
    const color = normalizeColor(card.color);
    const title = escapeHtml(card.title || `Card ${id}`);
    const description = card.description ? `<div class="card-description">${escapeHtml(card.description)}</div>` : '';
    const isValid = card.valid !== false;

    return `
        <div class="card ${isValid ? `card-${color}` : 'card-error'}" data-card-id="${id}" data-card-type="${escapeHtml(type)}">
            <div class="card-title">${title}</div>
            <div class="card-body">${renderCardBody(card)}</div>
            ${description}
        </div>
    `;
}

function renderCardBody(card) {
    if (card.valid === false) {
        const errors = Array.isArray(card.errors) ? card.errors : ['Invalid card'];
        return `
            <div>
                <strong>Invalid card</strong>
                <ul class="error-list">
                    ${errors.map(e => `<li>${escapeHtml(e)}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    const type = normalizeType(card.type);
    const value = card.value ?? '';
    const min = card.min_value ?? 0;
    const max = card.max_value ?? 100;

    if (type === 'led') {
        return `
            <div class="led-wrap">
                <div class="led ${isOn(value) ? 'led-on' : 'led-off'}" data-role="led"></div>
                <div class="value-text" data-role="value">${isOn(value) ? 'ON' : 'OFF'}</div>
            </div>
        `;
    }

    if (type === 'gauge') {
        return `
            <div class="gauge-wrap">
                <svg class="gauge-svg" viewBox="0 0 120 70">
                    <path class="gauge-bg" d="M 15 60 A 45 45 0 0 1 105 60"></path>
                    <path class="gauge-fill" data-role="gauge-fill" d="M 15 60 A 45 45 0 0 1 105 60"></path>
                    <line class="gauge-needle" data-role="gauge-needle" x1="60" y1="60" x2="60" y2="22"></line>
                    <circle class="gauge-center" cx="60" cy="60" r="4"></circle>
                </svg>
                <div class="value-text"><span data-role="value"></span></div>
                <div class="small-note"><span data-role="min"></span> to <span data-role="max"></span></div>
            </div>
        `;
    }

    if (type === 'textarea') {
        return `
            <textarea class="dash-textarea" data-role="input">${escapeHtml(value)}</textarea>
            <div class="small-note">Auto-saves while typing</div>
        `;
    }

    if (type === 'info') {
        return `<textarea class="dash-info" data-role="info" readonly>${escapeHtml(value)}</textarea>`;
    }

    if (type === 'button') {
        const pressed = String(value).toLowerCase().trim() === 'true';
        return `<button class="dash-button" data-role="button" ${pressed ? 'disabled' : ''}>${escapeHtml(card.title || 'Button')}</button>`;
    }

    if (type === 'switch') {
        const on = isOn(value);
        return `
            <div class="switch-wrap">
                <button class="dash-switch ${on ? 'dash-switch-on' : ''}" data-role="switch" aria-pressed="${on ? 'true' : 'false'}" title="${escapeHtml(card.title || 'Switch')}"></button>
                <div class="switch-state" data-role="switch-state">${on ? 'ON' : 'OFF'}</div>
            </div>
        `;
    }

    if (type === 'slider') {
        return `
            <input class="dash-slider" data-role="input" type="range" min="${escapeHtml(min)}" max="${escapeHtml(max)}" value="${escapeHtml(value)}">
            <div class="value-text"><span data-role="value"></span></div>
            <div class="small-note"><span data-role="min"></span> to <span data-role="max"></span></div>
        `;
    }

    if (type === 'graph') {
        return `
            <canvas class="graph-canvas" data-role="graph" width="360" height="155"></canvas>
            <div class="graph-note" data-role="graph-note"></div>
        `;
    }

    if (type === 'bar') {
        return `
            <canvas class="chart-canvas" data-role="bar" width="360" height="155"></canvas>
            <div class="chart-note" data-role="chart-note"></div>
        `;
    }

    if (type === 'pie') {
        return `
            <canvas class="chart-canvas" data-role="pie" width="360" height="155"></canvas>
            <div class="chart-note" data-role="chart-note"></div>
        `;
    }

    if (type === 'table') {
        return `<div class="table-wrap" data-role="table"></div>`;
    }

    return `<div class="unknown-card">Unknown card type</div>`;
}

function renderAllCards(cards) {
    latestCards = cards;

    if (!cards.length) {
        grid.innerHTML = '<div class="empty-state">No cards found. Add rows to the iot_cards table to create dashboard cards.</div>';
        firstLoadComplete = true;
        return;
    }

    const focused = document.activeElement;
    const focusedCardId = focused?.closest?.('.card')?.dataset?.cardId || null;
    const focusedRole = focused?.dataset?.role || null;
    const focusedType = focused?.closest?.('.card')?.dataset?.cardType || null;
    const selectionStart = focused && typeof focused.selectionStart === 'number' ? focused.selectionStart : null;
    const selectionEnd = focused && typeof focused.selectionEnd === 'number' ? focused.selectionEnd : null;
    const scrollX = window.scrollX;
    const scrollY = window.scrollY;

    // If the user is typing in a textarea, keep the browser value as the source of truth.
    // This prevents the backend/device from overwriting the field during the AJAX refresh cycle.
    if (focusedCardId && focusedType === 'textarea' && focusedRole === 'input') {
        editingTextareaValues[focusedCardId] = focused.value;
        debounceSet(focusedCardId, focused.value, 100);
    }

    isRenderingCards = true;
    grid.innerHTML = cards.map(renderCardShell).join('');
    cards.forEach(updateCardValues);
    attachEvents();

    Object.keys(editingTextareaValues).forEach(id => {
        const editedInput = document.querySelector(`[data-card-id="${CSS.escape(id)}"] [data-role="input"]`);
        if (editedInput && normalizeType(editedInput.closest('.card')?.dataset?.cardType) === 'textarea') {
            editedInput.value = editingTextareaValues[id];
        }
    });

    if (focusedCardId && focusedRole) {
        const replacement = document.querySelector(`[data-card-id="${CSS.escape(focusedCardId)}"] [data-role="${CSS.escape(focusedRole)}"]`);
        if (replacement && replacement.tagName !== 'BUTTON') {
            try { replacement.focus({ preventScroll: true }); } catch (e) { replacement.focus(); }
            if (focusedType === 'textarea' && focusedRole === 'input' && editingTextareaValues[focusedCardId] !== undefined) {
                replacement.value = editingTextareaValues[focusedCardId];
            }
            if (selectionStart !== null && typeof replacement.setSelectionRange === 'function') {
                replacement.setSelectionRange(selectionStart, selectionEnd);
            }
        }
    }

    window.scrollTo(scrollX, scrollY);
    isRenderingCards = false;
    firstLoadComplete = true;
}

function updateCardValues(card) {
    const id = String(card.id);
    const type = normalizeType(card.type);
    const cardEl = document.querySelector(`[data-card-id="${CSS.escape(id)}"]`);
    if (!cardEl || card.valid === false) return;

    const value = card.value ?? '';
    const min = numeric(card.min_value, 0);
    const max = numeric(card.max_value, 100);

    if (type === 'led') {
        const led = cardEl.querySelector('[data-role="led"]');
        const valueEl = cardEl.querySelector('[data-role="value"]');
        if (led) {
            led.classList.toggle('led-on', isOn(value));
            led.classList.toggle('led-off', !isOn(value));
        }
        if (valueEl) valueEl.textContent = isOn(value) ? 'ON' : 'OFF';
    }

    if (type === 'gauge') updateGauge(cardEl, value, min, max);

    if (type === 'textarea') {
        const input = cardEl.querySelector('[data-role="input"]');
        if (input) {
            if (editingTextareaValues[id] !== undefined) {
                input.value = editingTextareaValues[id];
                debounceSet(id, editingTextareaValues[id], 100);
            } else if (document.activeElement !== input) {
                input.value = value;
            }
        }
    }

    if (type === 'info') {
        const info = cardEl.querySelector('[data-role="info"]');
        if (info) info.value = value;
    }

    if (type === 'button') {
        const button = cardEl.querySelector('[data-role="button"]');
        if (button) {
            button.textContent = card.title || 'Button';
            button.disabled = String(value).toLowerCase().trim() === 'true';
        }
    }

    if (type === 'switch') {
        const sw = cardEl.querySelector('[data-role="switch"]');
        const state = cardEl.querySelector('[data-role="switch-state"]');
        const on = isOn(value);
        if (sw) {
            sw.classList.toggle('dash-switch-on', on);
            sw.setAttribute('aria-pressed', on ? 'true' : 'false');
            sw.title = card.title || 'Switch';
        }
        if (state) state.textContent = on ? 'ON' : 'OFF';
    }

    if (type === 'slider') {
        const input = cardEl.querySelector('[data-role="input"]');
        const valueEl = cardEl.querySelector('[data-role="value"]');
        const minEl = cardEl.querySelector('[data-role="min"]');
        const maxEl = cardEl.querySelector('[data-role="max"]');

        if (input) {
            input.min = min;
            input.max = max;
            if (document.activeElement !== input) input.value = numeric(value, min);
        }
        if (valueEl) valueEl.textContent = numeric(value, min);
        if (minEl) minEl.textContent = min;
        if (maxEl) maxEl.textContent = max;
    }

    if (type === 'graph') drawGraph(cardEl, value);

    if (type === 'bar') drawBarChart(cardEl, value);

    if (type === 'pie') drawPieChart(cardEl, value);

    if (type === 'table') drawTable(cardEl, value);
}

function updateGauge(cardEl, value, minValue, maxValue) {
    const fill = cardEl.querySelector('[data-role="gauge-fill"]');
    const needle = cardEl.querySelector('[data-role="gauge-needle"]');
    const valueEl = cardEl.querySelector('[data-role="value"]');
    const minEl = cardEl.querySelector('[data-role="min"]');
    const maxEl = cardEl.querySelector('[data-role="max"]');

    const min = numeric(minValue, 0);
    const max = numeric(maxValue, 100);
    const val = numeric(value, min);
    const range = max > min ? max - min : 100;
    const percent = Math.max(0, Math.min(1, (val - min) / range));
    const pathLength = 141.4;
    const offset = pathLength - (pathLength * percent);
    const angle = -90 + (180 * percent);

    if (fill) fill.style.strokeDashoffset = offset;
    if (needle) needle.style.transform = `rotate(${angle}deg)`;
    if (valueEl) valueEl.textContent = val;
    if (minEl) minEl.textContent = min;
    if (maxEl) maxEl.textContent = max;
}

function pointFromEntry(key, value) {
    if (typeof value === 'object' && value !== null) {
        const x = value.x ?? value[0] ?? key;
        const y = value.y ?? value[1];
        return [numeric(x, NaN), numeric(y, NaN)];
    }
    return [numeric(key, NaN), numeric(value, NaN)];
}

function parseGraphSeries(raw) {
    const parsed = JSON.parse(raw || '{}');
    if (!parsed || typeof parsed !== 'object') {
        throw new Error('Graph JSON must be an object or array');
    }

    const isNested = !Array.isArray(parsed) && Object.keys(parsed).some(key => !isFinite(Number(key)) && parsed[key] && typeof parsed[key] === 'object');
    const seriesList = [];

    function addSeries(name, source) {
        const points = [];
        if (Array.isArray(source)) {
            source.forEach((value, index) => points.push(pointFromEntry(index, value)));
        } else if (source && typeof source === 'object') {
            Object.keys(source).forEach(key => points.push(pointFromEntry(key, source[key])));
        } else {
            throw new Error('Graph series must be an object or array');
        }

        if (points.some(p => !Number.isFinite(p[0]) || !Number.isFinite(p[1]))) {
            throw new Error('Graph points must be numeric');
        }
        points.sort((a, b) => a[0] - b[0]);
        seriesList.push({ name: String(name), color: chartSliceColor(String(name), seriesList.length), points });
    }

    if (isNested) {
        Object.keys(parsed).forEach(name => addSeries(name, parsed[name]));
    } else {
        addSeries('value', parsed);
    }

    return seriesList.filter(series => series.points.length > 0);
}

function drawGraph(cardEl, rawValue) {
    const canvas = cardEl.querySelector('[data-role="graph"]');
    const note = cardEl.querySelector('[data-role="graph-note"]');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.font = '11px Arial';
    ctx.textBaseline = 'middle';

    let seriesList = [];
    try {
        seriesList = parseGraphSeries(rawValue);
    } catch (e) {
        if (note) note.textContent = 'Invalid graph JSON';
        ctx.fillStyle = '#b91c1c';
        ctx.fillText('Invalid graph JSON', 12, 24);
        return;
    }

    const allPoints = seriesList.flatMap(series => series.points);
    if (allPoints.length < 2) {
        if (note) note.textContent = 'Graph needs at least 2 points';
        ctx.fillStyle = '#6b7280';
        ctx.fillText('Not enough points', 12, 24);
        return;
    }

    const xs = allPoints.map(p => p[0]);
    const ys = allPoints.map(p => p[1]);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const rangeX = maxX > minX ? maxX - minX : 1;
    const rangeY = maxY > minY ? maxY - minY : 1;

    if (note) {
        const legend = seriesList.map(series => `<span class="legend-item"><span class="legend-dot" style="background:${escapeHtml(series.color)}"></span>${escapeHtml(series.name)}</span>`).join('');
        note.innerHTML = `<div class="graph-legend">${legend}</div>`;
        note.title = `x: ${niceNumber(minX)} to ${niceNumber(maxX)} | y: ${niceNumber(minY)} to ${niceNumber(maxY)} | ${allPoints.length} points`;
    }

    const padLeft = 42;
    const padRight = 10;
    const padTop = 10;
    const padBottom = 28;
    const plotLeft = padLeft;
    const plotRight = w - padRight;
    const plotTop = padTop;
    const plotBottom = h - padBottom;
    const plotW = plotRight - plotLeft;
    const plotH = plotBottom - plotTop;

    function sx(x) { return plotLeft + ((x - minX) / rangeX) * plotW; }
    function sy(y) { return plotBottom - ((y - minY) / rangeY) * plotH; }

    ctx.lineWidth = 1;
    ctx.strokeStyle = '#e5e7eb';
    ctx.fillStyle = '#6b7280';

    const yTicks = [minY, minY + rangeY / 2, maxY];
    yTicks.forEach(v => {
        const y = sy(v);
        ctx.beginPath();
        ctx.moveTo(plotLeft, y);
        ctx.lineTo(plotRight, y);
        ctx.stroke();
        ctx.textAlign = 'right';
        ctx.fillText(niceNumber(v), plotLeft - 5, y);
    });

    const xTicks = [minX, minX + rangeX / 2, maxX];
    xTicks.forEach(v => {
        const x = sx(v);
        ctx.beginPath();
        ctx.moveTo(x, plotTop);
        ctx.lineTo(x, plotBottom);
        ctx.stroke();
        ctx.textAlign = 'center';
        ctx.fillText(niceNumber(v), x, plotBottom + 14);
    });

    ctx.strokeStyle = '#9ca3af';
    ctx.beginPath();
    ctx.moveTo(plotLeft, plotTop);
    ctx.lineTo(plotLeft, plotBottom);
    ctx.lineTo(plotRight, plotBottom);
    ctx.stroke();

    seriesList.forEach(series => {
        if (series.points.length < 2) return;
        ctx.lineWidth = 2;
        ctx.strokeStyle = series.color;
        ctx.beginPath();
        series.points.forEach((p, i) => {
            const x = sx(p[0]);
            const y = sy(p[1]);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        ctx.fillStyle = series.color;
        series.points.forEach(p => {
            ctx.beginPath();
            ctx.arc(sx(p[0]), sy(p[1]), 2.3, 0, Math.PI * 2);
            ctx.fill();
        });
    });
}

function chartSliceColor(label, index) {
    let hash = 2166136261;
    const text = `${label}:${index}`;
    for (let i = 0; i < text.length; i++) {
        hash ^= text.charCodeAt(i);
        hash = Math.imul(hash, 16777619);
    }
    const hue = Math.abs(hash) % 360;
    const saturation = 68 + (Math.abs(hash >> 8) % 18);
    const lightness = 46 + (Math.abs(hash >> 16) % 10);
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

function parseChartData(raw) {
    const parsed = JSON.parse(raw || '{}');
    const items = [];

    if (Array.isArray(parsed)) {
        parsed.forEach((item, index) => {
            if (Array.isArray(item) && item.length >= 2) {
                items.push([String(item[0]), numeric(item[1], NaN)]);
            } else if (typeof item === 'object' && item !== null && ('value' in item || 'y' in item)) {
                items.push([String(item.key ?? item.label ?? item.x ?? index), numeric(item.value ?? item.y, NaN)]);
            } else {
                items.push([String(index), numeric(item, NaN)]);
            }
        });
    } else if (parsed && typeof parsed === 'object') {
        Object.keys(parsed).forEach(key => items.push([String(key), numeric(parsed[key], NaN)]));
    } else {
        throw new Error('Chart JSON must be an object or array');
    }

    if (!items.length || items.some(item => !Number.isFinite(item[1]))) {
        throw new Error('Chart values must be numeric');
    }

    return items;
}

function drawBarChart(cardEl, rawValue) {
    const canvas = cardEl.querySelector('[data-role="bar"]');
    const note = cardEl.querySelector('[data-role="chart-note"]');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.font = '11px Arial';
    ctx.textBaseline = 'middle';

    let items = [];
    try {
        items = parseChartData(rawValue);
    } catch (e) {
        if (note) note.textContent = 'Invalid bar chart JSON';
        ctx.fillStyle = '#b91c1c';
        ctx.fillText('Invalid bar chart JSON', 12, 24);
        return;
    }

    const values = items.map(item => item[1]);
    const minY = Math.min(0, ...values);
    const maxY = Math.max(...values);
    const rangeY = maxY > minY ? maxY - minY : 1;
    const padLeft = 42;
    const padRight = 12;
    const padTop = 10;
    const padBottom = 34;
    const plotLeft = padLeft;
    const plotRight = w - padRight;
    const plotTop = padTop;
    const plotBottom = h - padBottom;
    const plotW = plotRight - plotLeft;
    const plotH = plotBottom - plotTop;
    const gap = 5;
    const barW = Math.max(3, (plotW - gap * (items.length - 1)) / items.length);

    if (note) note.textContent = `${items.length} bars | max: ${niceNumber(maxY)}`;

    function sy(y) { return plotBottom - ((y - minY) / rangeY) * plotH; }
    const zeroY = sy(0);

    ctx.lineWidth = 1;
    ctx.strokeStyle = '#e5e7eb';
    ctx.fillStyle = '#6b7280';
    [minY, minY + rangeY / 2, maxY].forEach(v => {
        const y = sy(v);
        ctx.beginPath();
        ctx.moveTo(plotLeft, y);
        ctx.lineTo(plotRight, y);
        ctx.stroke();
        ctx.textAlign = 'right';
        ctx.fillText(niceNumber(v), plotLeft - 5, y);
    });

    ctx.strokeStyle = '#9ca3af';
    ctx.beginPath();
    ctx.moveTo(plotLeft, plotTop);
    ctx.lineTo(plotLeft, plotBottom);
    ctx.lineTo(plotRight, plotBottom);
    ctx.stroke();

    ctx.fillStyle = '#2563eb';
    items.forEach((item, i) => {
        const x = plotLeft + i * (barW + gap);
        const y = sy(Math.max(0, item[1]));
        const barBottom = sy(Math.min(0, item[1]));
        const height = Math.max(1, Math.abs(barBottom - y));
        ctx.fillRect(x, y, barW, height);

        if (items.length <= 8) {
            ctx.save();
            ctx.translate(x + barW / 2, plotBottom + 14);
            ctx.rotate(-0.35);
            ctx.textAlign = 'center';
            ctx.fillStyle = '#6b7280';
            ctx.fillText(item[0].slice(0, 10), 0, 0);
            ctx.restore();
        }
    });

    ctx.strokeStyle = '#9ca3af';
    ctx.beginPath();
    ctx.moveTo(plotLeft, zeroY);
    ctx.lineTo(plotRight, zeroY);
    ctx.stroke();
}

function drawPieChart(cardEl, rawValue) {
    const canvas = cardEl.querySelector('[data-role="pie"]');
    const note = cardEl.querySelector('[data-role="chart-note"]');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.font = '11px Arial';
    ctx.textBaseline = 'middle';

    let items = [];
    try {
        items = parseChartData(rawValue).filter(item => item[1] > 0);
    } catch (e) {
        if (note) note.textContent = 'Invalid pie chart JSON';
        ctx.fillStyle = '#b91c1c';
        ctx.fillText('Invalid pie chart JSON', 12, 24);
        return;
    }

    const total = items.reduce((sum, item) => sum + item[1], 0);
    if (!items.length || total <= 0) {
        if (note) note.textContent = 'Pie chart needs positive values';
        ctx.fillStyle = '#6b7280';
        ctx.fillText('No positive values', 12, 24);
        return;
    }

    if (note) note.textContent = `${items.length} slices | total: ${niceNumber(total)}`;

    const cx = 86;
    const cy = 74;
    const r = 54;
    const colors = items.map((item, i) => chartSliceColor(item[0], i));
    let start = -Math.PI / 2;

    items.forEach((item, i) => {
        const angle = (item[1] / total) * Math.PI * 2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, r, start, start + angle);
        ctx.closePath();
        ctx.fillStyle = colors[i];
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1;
        ctx.stroke();
        start += angle;
    });

    const legendX = 160;
    const legendY = 28;
    items.slice(0, 6).forEach((item, i) => {
        const y = legendY + i * 18;
        const pct = (item[1] / total) * 100;
        ctx.fillStyle = colors[i];
        ctx.fillRect(legendX, y - 5, 10, 10);
        ctx.fillStyle = '#374151';
        ctx.textAlign = 'left';
        ctx.fillText(`${item[0].slice(0, 12)} (${niceNumber(pct)}%)`, legendX + 15, y);
    });
}

function parseTableData(raw) {
    const parsed = JSON.parse(raw || '{}');
    const rows = [];

    if (Array.isArray(parsed)) {
        parsed.forEach((item, index) => {
            if (Array.isArray(item) && item.length >= 2) {
                rows.push([item[0], item[1]]);
            } else if (typeof item === 'object' && item !== null && ('key' in item || 'value' in item)) {
                rows.push([item.key ?? index, item.value ?? '']);
            } else {
                rows.push([index, item]);
            }
        });
    } else if (parsed && typeof parsed === 'object') {
        Object.keys(parsed).forEach(key => rows.push([key, parsed[key]]));
    } else {
        throw new Error('Table JSON must be an object or array');
    }

    return rows;
}

function tableValueToText(value) {
    if (value === null || value === undefined) return '';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
}

function drawTable(cardEl, rawValue) {
    const tableWrap = cardEl.querySelector('[data-role="table"]');
    if (!tableWrap) return;

    let rows = [];
    try {
        rows = parseTableData(rawValue);
    } catch (e) {
        tableWrap.innerHTML = `<div class="table-error">Invalid table JSON</div>`;
        return;
    }

    if (!rows.length) {
        tableWrap.innerHTML = `<div class="table-empty">No rows</div>`;
        return;
    }

    tableWrap.innerHTML = `
        <table class="data-table">
            <thead><tr><th>Key</th><th>Value</th></tr></thead>
            <tbody>
                ${rows.map(row => `
                    <tr>
                        <td>${escapeHtml(tableValueToText(row[0]))}</td>
                        <td>${escapeHtml(tableValueToText(row[1]))}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function attachEvents() {
    document.querySelectorAll('.card').forEach(cardEl => {
        const id = cardEl.dataset.cardId;
        const type = normalizeType(cardEl.dataset.cardType);

        if (type === 'textarea') {
            const input = cardEl.querySelector('[data-role="input"]');
            if (input) {
                input.addEventListener('focus', () => {
                    editingTextareaValues[id] = input.value;
                });
                input.addEventListener('input', () => {
                    editingTextareaValues[id] = input.value;
                    debounceSet(id, input.value, 100);
                });
                input.addEventListener('blur', () => {
                    if (isRenderingCards) return;
                    apiSet(id, input.value)
                        .then(() => { delete editingTextareaValues[id]; })
                        .catch(console.error);
                });
            }
        }

        if (type === 'button') {
            const button = cardEl.querySelector('[data-role="button"]');
            if (button) {
                button.addEventListener('click', () => {
                    button.disabled = true;
                    apiSet(id, 'true').then(() => pollState()).catch(console.error);
                });
            }
        }

        if (type === 'switch') {
            const sw = cardEl.querySelector('[data-role="switch"]');
            if (sw) {
                sw.addEventListener('click', () => {
                    const nextValue = sw.classList.contains('dash-switch-on') ? 'false' : 'true';
                    sw.classList.toggle('dash-switch-on', nextValue === 'true');
                    sw.setAttribute('aria-pressed', nextValue === 'true' ? 'true' : 'false');
                    const state = cardEl.querySelector('[data-role="switch-state"]');
                    if (state) state.textContent = nextValue === 'true' ? 'ON' : 'OFF';
                    apiSet(id, nextValue).then(() => pollState()).catch(console.error);
                });
            }
        }

        if (type === 'slider') {
            const input = cardEl.querySelector('[data-role="input"]');
            const valueEl = cardEl.querySelector('[data-role="value"]');
            if (input) {
                input.addEventListener('input', () => {
                    if (valueEl) valueEl.textContent = input.value;
                    debounceSet(id, input.value);
                });
            }
        }
    });
}

function pollState() {
    fetch('cards.php?action=state', { cache: 'no-store' })
        .then(response => response.json())
        .then(data => {
            if (!data.ok || !Array.isArray(data.cards)) {
                throw new Error(data.error || 'Invalid API response');
            }

            // Because title/color/description/type may also change, the entire dashboard is AJAX-rendered.
            renderAllCards(data.cards);
        })
        .catch(error => {
            if (!firstLoadComplete) {
                grid.innerHTML = `<div class="load-error">Unable to load dashboard: ${escapeHtml(error.message)}</div>`;
            }
            console.error(error);
        });
}

pollState();
setInterval(pollState, POLL_INTERVAL_MS);
</script>
</body>
</html>
