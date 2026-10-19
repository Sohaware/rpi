const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const page = fs.readFileSync(path.join(__dirname, '../components/ide/dashboard/index.php'), 'utf8');
const renderer = page.slice(page.indexOf('function pointFromEntry('), page.indexOf('function parseChartData('));
const labels = [];
const context = new Proxy({
    fillText(text, x, y) { labels.push({ text: String(text), x, y }); },
}, { get(target, key) { return target[key] ?? (() => {}); } });
const sandbox = {
    numeric: (value, fallback) => Number.isFinite(Number(value)) ? Number(value) : fallback,
    niceNumber: value => String(Number(Number(value).toFixed(2))),
    escapeHtml: value => String(value),
    canvasFont: () => '11px Arial',
    prepareCanvas: () => ({ ctx: context, width: 700, height: 400 }),
};
vm.createContext(sandbox);
vm.runInContext(renderer, sandbox);
assert.equal(JSON.stringify(sandbox.parseGraphSeries('[0,10]')[0].points), '[[1,0],[2,10]]');
assert.equal(JSON.stringify(sandbox.parseGraphSeries('{"10":2,"20":3}')[0].points), '[[10,2],[20,3]]');

const note = {};
const card = {
    dataset: { yPaddingPercent: '20', xAxisLabel: 'Sample', yAxisLabel: 'Temperature (C)' },
    querySelector: selector => selector.includes('graph-note') ? note : {},
};
sandbox.drawGraph(card, '[0,10]');
const yTicks = labels.filter(label => label.x === 53).map(label => label.text);
assert.deepEqual(yTicks, ['-2', '1.5', '5', '8.5', '12']);
assert(labels.some(label => label.text === 'Sample'));
assert(labels.some(label => label.text === 'Temperature (C)'));
assert(note.title.includes('y: -2 to 12'));

labels.length = 0;
sandbox.drawGraph(card, '[21,21]');
assert.equal(labels.filter(label => label.x === 53).length, 5);
assert(labels.every(label => Number.isFinite(label.x) && Number.isFinite(label.y)));
console.log('Dashboard graph: padding, ticks, samples, labels, constant values OK');
