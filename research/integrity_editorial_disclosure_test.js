/* DOM-contract tests for the disclosure primitive; browser behavior has a separate gate. */
'use strict';
const assert = require('assert'), fs = require('fs'), vm = require('vm');
class Node {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.children = []; this.attributes = {}; this.dataset = {}; this.style = {}; this.listeners = {}; this.hidden = false; this.isConnected = true; this.className = ''; this._text = ''; }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
  setAttribute(key, value) { this.attributes[key] = String(value); }
  getAttribute(key) { return this.attributes[key]; }
  get childNodes() { return this.children; }
  contains(node) { return node === this || this.children.some(child => child.contains(node)); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text = ''; this.children = children; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  click() { for (const fn of this.listeners.click || []) fn({ target: this }); }
  focus() { document.activeElement = this; }
  showModal() { this.open = true; this.querySelectorAll('button')[0]?.focus(); }
  close() { this.open = false; for (const fn of this.listeners.close || []) fn(); }
  querySelectorAll(selector) {
    const matches = node => selector[0] === '.' ? node.className.split(' ').includes(selector.slice(1)) : selector === '[data-fie-expand]' ? 'fieExpand' in node.dataset : node.tagName === selector.toUpperCase();
    return this.children.flatMap(node => [...(matches(node) ? [node] : []), ...node.querySelectorAll(selector)]);
  }
}
const document = { readyState: 'loading', documentElement: new Node('html'), body: new Node('body'), activeElement: null, createElement: tag => new Node(tag), addEventListener() {}, querySelectorAll(selector) { return this.body.querySelectorAll(selector); } };
const context = { document, window: {}, console, URLSearchParams, queueMicrotask };
vm.createContext(context);
vm.runInContext(fs.readFileSync('app/ui/editorial-workspace.js', 'utf8'), context);
const ui = context.window.FIEEditorial;
const table = ui.createTable({ title: 'Evidence', columns: [{ key: 'player', label: 'Player' }, { key: 'points', label: 'Points', numeric: true }, { key: 'status', label: 'Gate' }], rows: [
  { player: '<script>unsafe</script>', title: 'Player A', points: 0, status: { label: 'Blocked', tone: 'blocked' }, expanded: [['Reason', 'Incomplete exact scoring']], advanced: [['Source', null]] },
  { player: 'Player B', points: null, status: { label: 'Research only', tone: 'research' }, expanded: [['Reason', 'Research evidence']], advanced: [['Gate', 'Blocked']] }
] });
document.body.append(table);
const rows = table.querySelectorAll('.fie-expanded'), buttons = table.querySelectorAll('[data-fie-expand]');
assert(rows.every(row => row.hidden), 'Basic must start collapsed');
assert(table.textContent.includes('Blocked'), 'Blocker must be present in Basic');
assert.strictEqual(table.querySelectorAll('script').length, 0, 'Content must not become markup');
assert(table.querySelectorAll('td').some(cell => cell.textContent === '0'), 'Real zero must be distinct from missing');
assert(table.querySelectorAll('td').some(cell => cell.textContent === 'Unavailable'), 'Missing must never become zero');
buttons[0].click(); assert(!rows[0].hidden); assert.strictEqual(buttons[0].getAttribute('aria-expanded'), 'true');
buttons[1].click(); assert(rows[0].hidden && !rows[1].hidden, 'Only one explanation should be open');
buttons[1].click(); assert(rows[1].hidden, 'Repeat click should collapse');
const advanced = table.querySelectorAll('button').find(button => button.textContent === 'Advanced');
advanced.focus(); advanced.click();
const dialog = document.body.querySelectorAll('dialog')[0];
assert(dialog.open, 'Advanced must open directly from Basic');
assert(dialog.textContent.includes('Unavailable'), 'Advanced missing source must remain typed');
ui.closeReader(); assert.strictEqual(document.activeElement, advanced, 'Close must restore focus to its trigger');
const nestedTrigger = document.createElement('button'); nestedTrigger.textContent = 'Inspect source';
ui.openReader({title:'Outer detail',content:nestedTrigger},advanced);
ui.openReader({title:'Inner evidence',entries:[['Exact value',0]]},nestedTrigger);
assert(dialog.textContent.includes('Back to previous details'), 'Nested evidence must have a return path');
dialog.querySelectorAll('button').find(x=>x.textContent==='Back to previous details').click();
assert(dialog.textContent.includes('Outer detail')); assert.strictEqual(document.activeElement,nestedTrigger);
ui.closeReader(); assert.strictEqual(document.activeElement,advanced,'Close returns to outer trigger');
assert.strictEqual(table.querySelectorAll('table')[0].getAttribute('role'),'table');
assert.strictEqual(table.querySelectorAll('th')[0].getAttribute('role'),'columnheader');
buttons[0].click(); advanced.click(); ui.clearDisclosures();
assert(!dialog.open && rows.every(row => row.hidden), 'Context reset must clear both disclosure levels');
assert.strictEqual(buttons[0].getAttribute('aria-expanded'), 'false');
console.log('PASS editorial disclosure: visible blockers, missing vs zero, one expansion, direct Advanced, safe text, focus and context reset');
