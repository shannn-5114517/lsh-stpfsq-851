/* 贪吃蛇「最近 10 局战绩」功能测试
   用 Node + DOM 桩，直接跑 snake.html 里的真实 JS 代码 */
const fs = require('fs');
const vm = require('vm');

const file = process.argv[2] || 'snake.html';
const html = fs.readFileSync(file, 'utf8');
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error('找不到 <script>'); process.exit(1); }
const code = m[1];

/* ---------------- DOM 桩 ---------------- */
const noop = function () {};
const ctx2d = new Proxy({}, { get: () => noop, set: () => true });

const els = Object.create(null);
function makeEl(id) {
  const cls = new Set();
  return {
    id: id,
    _text: '', _html: '', style: {},
    _attrs: Object.create(null), handlers: Object.create(null),
    classList: {
      add: (c) => cls.add(c),
      remove: (c) => cls.delete(c),
      contains: (c) => cls.has(c),
      toggle: (c, force) => {
        const want = (force === undefined) ? !cls.has(c) : !!force;
        if (want) cls.add(c); else cls.delete(c);
        return want;
      },
      toString: () => Array.from(cls).join(' ')
    },
    get textContent() { return this._text; },
    set textContent(v) { this._text = String(v); },
    get innerHTML() { return this._html; },
    set innerHTML(v) { this._html = String(v); },
    setAttribute(k, v) { this._attrs[k] = String(v); },
    getAttribute(k) { return (k in this._attrs) ? this._attrs[k] : null; },
    removeAttribute(k) { delete this._attrs[k]; },
    hasAttribute(k) { return k in this._attrs; },
    addEventListener(ev, fn) { this.handlers[ev] = fn; },
    click() { if (this.handlers.click) this.handlers.click({}); },
    getContext() { return ctx2d; },
    getBoundingClientRect() { return { width: 400, height: 400, top: 0, left: 0 }; },
    appendChild: noop, focus: noop
  };
}
function el(id) { if (!els[id]) els[id] = makeEl(id); return els[id]; }

const store = new Map();
const localStorage = {
  getItem: (k) => store.has(k) ? store.get(k) : null,
  setItem: (k, v) => { store.set(k, String(v)); },
  removeItem: (k) => { store.delete(k); },
  clear: () => store.clear()
};

let rafQueue = [];
const document = {
  documentElement: { style: { setProperty: noop } },
  body: makeEl('body'),
  getElementById: el,
  addEventListener: noop,
  createElement: () => makeEl('tmp')
};
const win = { devicePixelRatio: 1, confirm: () => true, addEventListener: noop };
const getComputedStyle = () => ({
  getPropertyValue: (p) => ({
    '--board': '#0f172a', '--board-line': '#1b2540', '--snake': '#4ade80',
    '--snake-head': '#a7f3d0', '--food': '#f87171'
  }[p] || '#000')
});

const sandbox = {
  document, window: win, localStorage, getComputedStyle, console,
  requestAnimationFrame: (fn) => { rafQueue.push(fn); return rafQueue.length; },
  cancelAnimationFrame: noop, setTimeout, clearTimeout, Date, Math, JSON,
  Number, Array, Object, String, isFinite, parseFloat, parseInt
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

/* ------------------ 运行 ------------------ */
vm.runInContext(code, sandbox, { filename: 'snake.js' });

/* ------------------ 工具 ------------------ */
function tick(t) {
  const q = rafQueue; rafQueue = [];
  for (const fn of q) fn(t);
}
function isOver() {
  const c = el('overlay').className || '';
  return c.indexOf('end') >= 0 || c.indexOf('win') >= 0;
}
/** 玩一局（AI 自动玩到结束） */
function playOne() {
  el('btn-auto').click();           // 开 AI 模式并开始
  let t = 0, frames = 0;
  while (!isOver() && frames < 60000) { tick(t += 16); frames++; }
  el('btn-auto').click();           // 关掉 AI 模式，方便下一局
  return { frames: frames, overlay: el('overlay').innerHTML.slice(0, 60) };
}
/** 从渲染出的 HTML 里数有多少行记录 */
function rowCount() {
  const h = el('history-list').innerHTML;
  const mm = h.match(/<tr>/g);
  return mm ? mm.length : 0;
}
function firstRow() {
  const h = el('history-list').innerHTML;
  const mm = h.match(/<tr>([\s\S]*?)<\/tr>/);
  return mm ? mm[1].replace(/<\/td>\s*<td[^>]*>/g, ' | ').replace(/<[^>]+>/g, '').trim() : '';
}
const P = (ok, msg) => console.log((ok ? '  ✅ ' : '  ❌ ') + msg);

/* ------------------ 测试 ------------------ */
console.log('══════ 贪吃蛇「最近 10 局战绩」测试 ══════\n');

console.log('【1】初始状态');
P(rowCount() === 0, '战绩列表为空（0 行记录）');
P(el('history-count').textContent === '0', '计数显示 0');
P(el('history-list').innerHTML.indexOf('还没有记录') >= 0, '显示"还没有记录"占位文字');

console.log('\n【2】面板默认收起（直接检查 HTML 源码）');
P(/id="history-body"[^>]*\shidden/.test(html), 'history-body 标签带 hidden 属性（默认收起）');
P(/id="btn-history"[^>]*aria-expanded="false"/.test(html), '按钮 aria-expanded="false"');
P(/id="history-list"/.test(html), '列表容器 id="history-list" 存在');
P(/只保留最近 10 局/.test(html), '面板里注明了"只保留最近 10 局"');

console.log('\n【3】点标题展开 / 收起');
el('btn-history').click();
P(!el('history-body').hasAttribute('hidden'), '点一下 → 展开（hidden 被移除）');
P(el('btn-history').getAttribute('aria-expanded') === 'true', 'aria-expanded = true');
el('btn-history').click();
P(el('history-body').hasAttribute('hidden'), '再点一下 → 收起');
P(el('btn-history').getAttribute('aria-expanded') === 'false', 'aria-expanded = false');

console.log('\n【4】玩一局，记录自动追加');
const r1 = playOne();
console.log('      （本局跑了 ' + r1.frames + ' 帧，结算画面：' + r1.overlay.replace(/\s+/g, ' ') + '…）');
P(rowCount() === 1, '列表新增 1 条记录');
P(el('history-count').textContent === '1', '计数变成 1');
console.log('      第 1 行的内容：' + firstRow());

console.log('\n【5】再玩 2 局，看是否继续追加（最新的在最前）');
playOne(); playOne();
P(rowCount() === 3, '列表共 3 条记录');
P(el('history-count').textContent === '3', '计数变成 3');
console.log('      最新一行：' + firstRow());

console.log('\n【6】累计统计是否同步');
const saved = JSON.parse(store.get('snake-stats-v1'));
P(saved.rounds === 3, 'rounds = 3（累计局数）');
P(saved.history.length === 3, 'history 里有 3 条');
P(typeof saved.history[0].score === 'number', '记录里含 score 字段');
P(typeof saved.history[0].len === 'number', '记录里含 len 字段（蛇长）');
P(typeof saved.history[0].result === 'string', '记录里含 result 字段（结果）');
P(typeof saved.history[0].secs === 'number', '记录里含 secs 字段（用时）');
console.log('      原始数据：' + JSON.stringify(saved.history[0]));

console.log('\n【7】上限 10 局：继续玩到 13 局');
for (let i = 0; i < 10; i++) playOne();
const s2 = JSON.parse(store.get('snake-stats-v1'));
P(s2.rounds === 13, '累计局数 = 13');
P(s2.history.length === 10, '战绩列表被截断到 10 条（不是 13）');
P(el('history-count').textContent === '10', '界面计数显示 10');
P(rowCount() === 10, '渲染出来正好 10 行');
console.log('      列表里最新的局号：' + s2.history[0].no + '，最旧的局号：' + s2.history[9].no);
P(s2.history[0].no === 13, '最前面是第 13 局（最新）');
P(s2.history[9].no === 4, '最后面是第 4 局（第 1-3 局已被挤掉）');

console.log('\n【8】刷新页面后记录还在');
const before = el('history-list').innerHTML;
rafQueue = [];
vm.runInContext(code, sandbox, { filename: 'snake.js' });   // 重新执行一遍 = 模拟刷新
P(store.get('snake-stats-v1') !== null, 'localStorage 里数据还在');
const s3 = JSON.parse(store.get('snake-stats-v1'));
P(s3.history.length === 10, '重新加载后仍是 10 条');
P(el('history-count').textContent === '10', '界面计数恢复为 10');

console.log('\n【9】重置统计 → 战绩列表清空');
el('btn-reset-stats').click();
const s4 = JSON.parse(store.get('snake-stats-v1'));
P(s4.rounds === 0, '累计局数归零');
P(s4.history.length === 0, 'history 数组被清空');
P(el('history-count').textContent === '0', '界面计数归零');
P(el('history-list').innerHTML.indexOf('还没有记录') >= 0, '又显示"还没有记录"占位');

console.log('\n══════ 测试结束 ══════');
