/**
 * 综合实验 GUI 前端 —— 单文件原生 SPA + hash 路由。
 *
 * 路由表：
 *   #/                     入口页
 *   #/history              历史记录
 *   #/live  /unit          实时·单元测试
 *           /integration   实时·集成测试
 *           /data          实时·数据组合
 *           /performance   实时·性能测试
 *   #/flowchart            业务流程图
 */
'use strict';

const $app = document.getElementById('app');

let META = null;          // /api/meta 缓存
let INT_CATALOG = null;   // /api/integration/catalog 缓存
let MONITOR_TIMER = null; // 首页系统状态卡的轮询 timer；路由切走时必须清掉
let DEMO_TIMER = null;    // 快速 demo 进度轮询 timer；路由切走时必须清掉

const OWNER_ORDER = ['siqi', 'zhiyi', 'yusheng', 'xupeng'];
const MONITOR_INTERVAL_MS = 15_000;

// ============================================================
// 工具
// ============================================================

const h = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstChild; };
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const esc = (s) => String(s ?? '').replace(/[<>&"']/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&#39;'}[c]));

async function api(method, url, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const r = await fetch(url, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
  return data;
}
const apiGet = (url) => api('GET', url);
const apiPost = (url, body) => api('POST', url, body);

function fmtDuration(s) { return s == null ? '—' : (s < 60 ? `${s.toFixed(2)}s` : `${(s/60).toFixed(1)}m`); }
function fmtTime(iso) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString('zh-CN', { hour12: false }); }
  catch { return iso; }
}

function topbar(title) {
  return `
    <div class="topbar">
      <a class="topbar-back" href="#/">← 返回入口</a>
      <div class="topbar-title">${esc(title)}</div>
      <div class="topbar-hint">按 <kbd>Esc</kbd> 返回 · 表单内 <kbd>⏎</kbd> 启动</div>
    </div>
  `;
}

// ============================================================
// 路由
// ============================================================

function parseHash() {
  const raw = location.hash.replace(/^#/, '') || '/';
  return raw.split('?')[0];
}

async function route() {
  // 离开当前页时清掉轮询 timer，避免后台空转拉接口
  if (MONITOR_TIMER) { clearInterval(MONITOR_TIMER); MONITOR_TIMER = null; }
  if (DEMO_TIMER) { clearInterval(DEMO_TIMER); DEMO_TIMER = null; }
  const path = parseHash();
  try {
    if (path === '/' || path === '') return renderEntry();
    if (path === '/history') return renderHistory();
    if (path === '/flowchart') return renderFlowchart();
    if (path === '/demo') return renderDemo();
    if (path === '/live' || path === '/live/') {
      location.hash = '#/live/unit';
      return;
    }
    if (path.startsWith('/live/')) return renderLive(path.slice(6));
    renderNotFound(path);
  } catch (e) {
    $app.innerHTML = `<div class="page"><div class="card">页面加载失败：${esc(e.message)}</div></div>`;
  }
}

window.addEventListener('hashchange', route);

async function boot() {
  try {
    META = await apiGet('/api/meta');
    INT_CATALOG = await apiGet('/api/integration/catalog');
    route();
  } catch (e) {
    $app.innerHTML = `<div class="loading">加载失败：${esc(e.message)}<br>请确认后端已启动（uvicorn）。</div>`;
  }
}
boot();

// ============================================================
// 入口页
// ============================================================

async function renderEntry() {
  let stats = { total: 0, by_category: {} };
  try { stats = await apiGet('/api/history/stats'); } catch {}

  $app.innerHTML = `
    <div class="entry">
      <div class="entry-banner">
        <div class="entry-eyebrow">SOFTWARE QUALITY ENGINEERING</div>
        <h1>QualityHub</h1>
        <p class="entry-tagline">多框架自动化测试编排与可视化平台</p>
        <p class="subtitle">统一接入 Python / Java 测试栈 · 被测站点 automationexercise.com</p>
        <div class="entry-metrics" aria-label="项目概览">
          <span><strong>12</strong> 业务模块</span>
          <span><strong>4</strong> 测试策略</span>
          <span><strong>4</strong> 异构适配器</span>
        </div>
        <img class="team-logo" src="/static/team_logo.svg" alt="team logo" width="90" height="90">
      </div>

      <div class="monitor-card" id="monitor-card">
        <div class="monitor-header">
          <span class="monitor-title">系统状态</span>
          <span class="monitor-meta">
            <span id="monitor-updated">检测中…</span>
            <button class="monitor-refresh" id="monitor-refresh" type="button" title="立即刷新">↻</button>
          </span>
        </div>
        <div class="monitor-grid">
          <div class="monitor-item">
            <span class="dot unknown" id="mon-sut-dot"></span>
            <div class="monitor-item-body">
              <div class="monitor-item-label">被测站点 · automationexercise.com</div>
              <div class="monitor-item-value" id="mon-sut-value">检测中…</div>
            </div>
          </div>
          <div class="monitor-item">
            <span class="dot unknown" id="mon-backend-dot"></span>
            <div class="monitor-item-body">
              <div class="monitor-item-label">本地后端 · FastAPI</div>
              <div class="monitor-item-value" id="mon-backend-value">检测中…</div>
            </div>
          </div>
          <div class="monitor-item">
            <div class="monitor-item-body">
              <div class="monitor-item-label">成员 adapter 可用性</div>
              <div class="monitor-adapters" id="mon-adapters">—</div>
            </div>
          </div>
        </div>
      </div>

      <div class="entry-team">
        <span class="entry-team-label">小组成员</span>
        <div class="entry-team-members">
          <span class="entry-team-member leader">乔思齐</span>
          <span class="entry-team-member">唐知怡</span>
          <span class="entry-team-member">沈徐鹏</span>
          <span class="entry-team-member">曹宇声</span>
        </div>
      </div>

      <div class="entry-cards">
        <div class="entry-card" data-go="#/history">
          <img src="/static/icon_history.svg" alt="history">
          <h3>历史记录</h3>
          <p>按时间回看所有执行结果</p>
          <div class="entry-card-meta">累计 ${stats.total} 次</div>
        </div>
        <div class="entry-card" data-go="#/live/unit">
          <img src="/static/icon_live.svg" alt="live">
          <h3>实时测试</h3>
          <p>在线启动单元 / 集成 / 数据 / 性能测试</p>
          <div class="entry-card-meta">12 模块 · 4 类测试</div>
        </div>
        <div class="entry-card" data-go="#/flowchart">
          <img src="/static/icon_flowchart.svg" alt="flowchart">
          <h3>业务流程图</h3>
          <p>站点全局业务流程</p>
          <div class="entry-card-meta">SVG 总览</div>
        </div>
        <div class="entry-card" data-go="#/demo">
          <img src="/static/icon_demo.svg" alt="demo">
          <h3>快速测试 demo</h3>
          <p>4 人并行 · headless 后台一键演示</p>
          <div class="entry-card-meta">每人 1 单元+1 集成+5 数据</div>
        </div>
      </div>

      <div class="entry-footer">
        技术栈：FastAPI · Playwright · Locust · pytest · TestNG
      </div>
    </div>
  `;
  $$('.entry-card').forEach(c => c.addEventListener('click', async () => {
    const go = c.dataset.go;
    // 实时测试 / 快速 demo 都会访问被测站点，进入前先看免责声明（历史/流程图直接跳转）
    if ((go.startsWith('#/live') || go.startsWith('#/demo')) && needsDisclaimer()) {
      await showDisclaimerModal();
    }
    location.hash = go;
  }));

  // 监控小窗：首屏立刻拉一次，之后每 15s 轮询；手动按钮也走同一个 fetch
  $('#monitor-refresh').addEventListener('click', () => fetchAndRenderMonitor(true));
  fetchAndRenderMonitor(false);
  MONITOR_TIMER = setInterval(() => fetchAndRenderMonitor(false), MONITOR_INTERVAL_MS);
}

// ============================================================
// 首页·系统状态监控
// ============================================================

async function fetchAndRenderMonitor(spin) {
  // 路由已切走（DOM 没了）就别白拉
  if (!document.getElementById('monitor-card')) {
    if (MONITOR_TIMER) { clearInterval(MONITOR_TIMER); MONITOR_TIMER = null; }
    return;
  }
  const $btn = $('#monitor-refresh');
  if (spin && $btn) { $btn.classList.add('spin'); setTimeout(() => $btn.classList.remove('spin'), 500); }
  try {
    const data = await apiGet('/api/monitor');
    renderMonitor(data);
  } catch (e) {
    // 拉不到 monitor 通常意味着后端挂了，把所有点置 fail
    renderMonitor({
      sut: { ok: false, error: 'unreachable' },
      backend: { ok: false },
      adapters: {},
      timestamp: null,
    });
    const $upd = $('#monitor-updated');
    if ($upd) $upd.textContent = '后端不可达';
  }
}

function renderMonitor(data) {
  // SUT
  const sut = data.sut || {};
  const $sd = $('#mon-sut-dot');
  const $sv = $('#mon-sut-value');
  if ($sd && $sv) {
    if (sut.ok) {
      const lat = sut.latency_ms;
      const cls = lat == null ? 'ok' : (lat < 800 ? 'ok' : 'warn');
      $sd.className = `dot ${cls}`;
      $sv.textContent = `在线 · ${lat != null ? lat + ' ms' : '—'} · HTTP ${sut.status_code ?? '—'}`;
    } else {
      $sd.className = 'dot fail';
      $sv.textContent = sut.error ? `离线 · ${sut.error}` : '离线';
    }
  }

  // 后端
  const be = data.backend || {};
  const $bd = $('#mon-backend-dot');
  const $bv = $('#mon-backend-value');
  if ($bd && $bv) {
    if (be.ok) {
      $bd.className = 'dot ok';
      $bv.textContent = data.running ? '存活 · 有测试运行中' : '存活 · 空闲';
    } else {
      $bd.className = 'dot fail';
      $bv.textContent = '不可达';
    }
  }

  // 4 成员 adapter
  const $ad = $('#mon-adapters');
  if ($ad) {
    const a = data.adapters || {};
    $ad.innerHTML = OWNER_ORDER.map(id => {
      const info = a[id];
      const ok = info && info.available;
      const label = (info && info.display) || (META && META.owners.find(o => o.id === id)?.display) || id;
      return `<span class="monitor-adapter"><span class="dot dot-sm ${ok ? 'ok' : 'fail'}"></span>${esc(label)}</span>`;
    }).join('');
  }

  // 更新时间
  const $upd = $('#monitor-updated');
  if ($upd) {
    if (data.timestamp) {
      try { $upd.textContent = `更新于 ${new Date(data.timestamp).toLocaleTimeString('zh-CN', { hour12: false })}`; }
      catch { $upd.textContent = data.timestamp; }
    } else {
      $upd.textContent = '—';
    }
  }
}

// ============================================================
// 实时测试 - 路由 + 顶部分类 tab
// ============================================================

const LIVE_TABS = [
  { id: 'unit',         label: '单元测试' },
  { id: 'integration',  label: '集成测试' },
  { id: 'data',         label: '数据组合' },
  { id: 'performance',  label: '性能测试' },
];

function renderLiveShell(activeSub, innerHtml) {
  $app.innerHTML = `
    ${topbar('实时测试')}
    <div class="page">
      <div class="tabs">
        ${LIVE_TABS.map(t => `
          <div class="tab ${t.id === activeSub ? 'active' : ''}" data-sub="${t.id}">${t.label}</div>
        `).join('')}
      </div>
      <div id="live-body">${innerHtml}</div>
    </div>
  `;
  $$('.tabs .tab').forEach(el => el.addEventListener('click', () => {
    location.hash = `#/live/${el.dataset.sub}`;
  }));
}

async function renderLive(sub) {
  // 免责声明只在从入口卡片首次进入时弹（见 renderEntry 的 click handler）；
  // 子页面之间切 tab、地址栏直达、刷新都不再触发，避免噪音
  if (sub === 'unit')         { renderLiveShell('unit', '<div class="loading">…</div>');         return renderUnitView(); }
  if (sub === 'integration')  { renderLiveShell('integration', '<div class="loading">…</div>');  return renderIntegrationView(); }
  if (sub === 'data')         { renderLiveShell('data', '<div class="loading">…</div>');         return renderDataView(); }
  if (sub === 'performance')  { renderLiveShell('performance', '<div class="loading">…</div>');  return renderPerfView(); }
  location.hash = '#/live/unit';
}

// ============================================================
// 实时·单元测试：12 模块卡片 + 右侧抽屉
// ============================================================

let SELECTED_MODULE = null;   // module id

function renderUnitView() {
  const groups = {};
  META.modules.forEach(m => { (groups[m.group] = groups[m.group] || []).push(m); });

  const html = `
    <div style="display: grid; grid-template-columns: 1fr 380px; gap: 24px;">
      <div>
        ${Object.entries(groups).map(([groupName, mods]) => `
          <div class="module-group">
            <div class="module-group-label">${esc(groupName)}</div>
            <div class="module-grid">
              ${mods.map(m => `
                <div class="module-card ${m.available ? '' : 'disabled'} ${m.id === SELECTED_MODULE ? 'selected' : ''}"
                     data-module="${m.id}" title="${m.available ? '点击选中此模块' : '等待 '+m.owner+' 提交接口'}">
                  <div class="module-card-name">${esc(m.name)}</div>
                  <div class="module-card-owner">
                    <span class="status-pill ${m.available ? 'ok' : 'tbd'}">${m.available ? '可用' : '待接入'}</span>
                    ${esc(m.owner_display)}
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `).join('')}
      </div>
      <div id="unit-panel">${renderUnitPanel()}</div>
    </div>
  `;
  $('#live-body').innerHTML = html;

  $$('.module-card').forEach(card => card.addEventListener('click', () => {
    if (card.classList.contains('disabled')) return;
    SELECTED_MODULE = card.dataset.module;
    $$('.module-card').forEach(c => c.classList.toggle('selected', c.dataset.module === SELECTED_MODULE));
    $('#unit-panel').innerHTML = renderUnitPanel();
    bindUnitPanel();
  }));
  bindUnitPanel();
}

function renderUnitPanel() {
  if (!SELECTED_MODULE) {
    return `<div class="card"><div style="color: var(--color-muted); text-align: center; padding: 40px 0;">← 请从左侧选择一个模块</div></div>`;
  }
  const m = META.modules.find(x => x.id === SELECTED_MODULE);
  const owner = META.owners.find(o => o.id === m.owner);
  const defaults = owner.default_params.unit || {};
  const supports = (owner.test_cases.unit && owner.test_cases.unit[m.id] && owner.test_cases.unit[m.id].supports) || [];

  let formHtml = '';
  if (supports.includes('keyword')) {
    formHtml += `
      <div class="form-row">
        <label>搜索关键词</label>
        <input type="text" id="param-keyword" value="${esc(defaults.keyword || '')}" placeholder="如 dress">
      </div>`;
  }
  if (supports.includes('product_index')) {
    formHtml += `
      <div class="form-row">
        <label>商品序号</label>
        <input type="number" id="param-product-index" value="${defaults.product_index ?? 0}" min="0">
      </div>`;
  }
  if (!formHtml) formHtml = '<div class="form-row"><span class="hint">该模块无需额外参数</span></div>';

  return `
    <div class="card">
      <h3 style="margin-top: 0;">${esc(m.name)}</h3>
      <div style="color: var(--color-muted); margin-bottom: 16px;">负责成员：${esc(m.owner_display)}</div>
      ${formHtml}
      <button class="btn btn-large" id="btn-run-unit" style="width: 100%; justify-content: center;">🚀 开始测试</button>
      <div id="unit-result" style="margin-top: 16px;"></div>
    </div>
  `;
}

function bindUnitPanel() {
  const btn = $('#btn-run-unit');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const body = { module: SELECTED_MODULE };
    const kw = $('#param-keyword'); if (kw) body.keyword = kw.value || null;
    const pi = $('#param-product-index'); if (pi) body.product_index = Number(pi.value);

    showRunning(btn, '#unit-result', '运行中（pytest 启动 + Playwright 打开浏览器，约 10–20s）');
    try {
      const data = await apiPost('/api/run/unit', body);
      renderResultCard('#unit-result', data.entry);
    } catch (e) {
      renderErrorCard('#unit-result', e.message);
    } finally {
      btn.disabled = false; btn.innerHTML = '🚀 开始测试';
    }
  });
}

// ============================================================
// 实时·集成测试：5 槽位 + 白名单匹配
// ============================================================

let INT_SLOTS = [null, null, null, null, null];

function renderIntegrationView() {
  const options = `
    <option value="">（无）</option>
    ${META.modules.map(m => `<option value="${m.id}">${esc(m.name)}</option>`).join('')}
  `;
  const html = `
    <div class="card">
      <h3 style="margin-top: 0;">集成路径组合</h3>
      <p style="color: var(--color-muted); margin-top: 0;">在 5 个深度里选模块（深度 4/5 可留空 → 形成深度 ≤5 的路径）。请注意目标网站的实际结构，以防逻辑无法实现。</p>
      <div class="integration-slots">
        ${[1,2,3,4,5].map(d => `
          <div class="integration-slot">
            <label>深度 ${d}</label>
            <select data-slot="${d-1}">${options}</select>
          </div>
        `).join('')}
      </div>
      <div class="integration-match" id="int-match"></div>
      <div style="margin-top: 16px;">
        <button class="btn btn-large" id="btn-run-int" disabled>🚀 运行此组合</button>
      </div>
      <div id="int-result" style="margin-top: 16px;"></div>
    </div>
  `;
  $('#live-body').innerHTML = html;

  // 还原选择
  $$('.integration-slot select').forEach((sel, idx) => {
    sel.value = INT_SLOTS[idx] || '';
    sel.addEventListener('change', () => {
      INT_SLOTS[idx] = sel.value || null;
      updateIntegrationMatch();
    });
  });
  updateIntegrationMatch();

  $('#btn-run-int').addEventListener('click', async () => {
    const btn = $('#btn-run-int');
    showRunning(btn, '#int-result', '运行中…');
    try {
      const data = await apiPost('/api/run/integration', { slots: INT_SLOTS });
      if (data.ok) renderResultCard('#int-result', data.entry, { extraLabel: `匹配：${data.matched.label}（深度 ${data.matched.depth}）` });
      else renderErrorCard('#int-result', data.reason || '未命中白名单');
    } catch (e) {
      renderErrorCard('#int-result', e.message);
    } finally {
      btn.disabled = false; btn.innerHTML = '🚀 运行此组合';
    }
  });
}

function updateIntegrationMatch() {
  const match = lookupIntegration(INT_SLOTS);
  const $m = $('#int-match');
  const $btn = $('#btn-run-int');
  if (match) {
    $m.className = 'integration-match hit';
    $m.innerHTML = `✅ 已命中：${esc(match.label)}（深度 ${match.depth}，由 ${esc(match.owner)} 实现）`;
    $btn.disabled = false;
  } else {
    const nonEmpty = INT_SLOTS.filter(s => s);
    if (nonEmpty.length === 0) {
      $m.className = 'integration-match miss';
      $m.innerHTML = '请至少在深度 1 选一个模块';
    } else {
      $m.className = 'integration-match miss';
      $m.innerHTML = `❌ 当前组合（${nonEmpty.map(s => META.modules.find(m=>m.id===s).name).join(' → ')}）在目标网站无对应逻辑`;
    }
    $btn.disabled = true;
  }
}

function lookupIntegration(slots) {
  let arr = [...slots];
  while (arr.length && !arr[arr.length-1]) arr.pop();
  if (!arr.length) return null;
  if (arr.some(s => !s)) return null;  // 中间有空
  return INT_CATALOG.available.find(a => JSON.stringify(a.modules) === JSON.stringify(arr)) || null;
}

// ============================================================
// 实时·数据组合：成员 tab + 25 行表
// ============================================================

let DATA_OWNER = 'siqi';

async function renderDataView() {
  const html = `
    ${renderOwnerTabs(DATA_OWNER, 'data')}
    <div id="data-body"></div>
  `;
  $('#live-body').innerHTML = html;
  bindOwnerTabs('data', (ownerId) => { DATA_OWNER = ownerId; renderDataView(); });
  await renderDataBody();
}

async function renderDataBody() {
  const owner = META.owners.find(o => o.id === DATA_OWNER);
  if (!owner.available) {
    $('#data-body').innerHTML = `<div class="card" style="text-align: center; color: var(--color-muted); padding: 40px;">🚧 ${esc(owner.display)} 的接口尚未提交</div>`;
    return;
  }

  $('#data-body').innerHTML = '<div class="card">加载用例…</div>';
  let casesResp;
  try { casesResp = await apiGet(`/api/data/cases/${DATA_OWNER}`); }
  catch (e) { $('#data-body').innerHTML = `<div class="card">加载失败：${esc(e.message)}</div>`; return; }

  const cases = casesResp.cases || [];
  $('#data-body').innerHTML = `
    <div class="card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <div>
          <h3 style="margin:0;">数据组合测试（共 ${cases.length} 组）</h3>
          <div style="color: var(--color-muted); font-size:13px;">负责成员：${esc(owner.display)}</div>
        </div>
        <div>
          <label style="margin-right: 12px;"><input type="checkbox" id="data-regen"> 重新生成 CSV</label>
          <button class="btn" id="btn-run-data">🚀 跑全部</button>
        </div>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead><tr><th>#</th><th>关键词</th><th>期望命中</th><th>实际</th><th>结果</th><th>备注</th></tr></thead>
          <tbody>
            ${cases.map(c => `
              <tr class="pending" data-id="${esc(c.id)}" data-expected="${c.expected_hit ? '1' : '0'}">
                <td title="${esc(c.id)}">${esc(c.id)}</td>
                <td title="${esc(c.keyword)}"><code>${esc(c.keyword)}</code></td>
                <td>${c.expected_hit ? '是' : '否'}</td>
                <td class="cell-actual">—</td>
                <td class="cell-status">—</td>
                <td title="${esc(c.note)}" style="color: var(--color-muted);">${esc(c.note)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
      <div id="data-result" style="margin-top: 16px;"></div>
    </div>
  `;

  $('#btn-run-data').addEventListener('click', async () => {
    const btn = $('#btn-run-data');
    const regen = $('#data-regen').checked;
    showRunning(btn, '#data-result', `运行中（25 组 × 每组 ~7s ≈ 3 分钟，请耐心；浏览器会反复打开）`);
    try {
      const data = await apiPost('/api/run/data', { owner: DATA_OWNER, regenerate: regen });
      updateDataTable(data.entry);
      renderResultCard('#data-result', data.entry);
    } catch (e) {
      renderErrorCard('#data-result', e.message);
    } finally {
      btn.disabled = false; btn.innerHTML = '🚀 跑全部';
    }
  });
}

/** 跑完后把每一行的"实际/结果"列按 pytest 结果填回去。 */
function updateDataTable(entry) {
  const perCase = (entry && entry.extra && entry.extra.per_case) || {};
  $$('.data-table tbody tr').forEach(row => {
    const id = row.dataset.id;
    const pc = perCase[id];
    const expected = row.dataset.expected === '1';
    const $actual = row.querySelector('.cell-actual');
    const $status = row.querySelector('.cell-status');
    if (!pc) {
      $actual.textContent = '—';
      $status.innerHTML = '<span class="status-pill tbd">未跑</span>';
      return;
    }
    row.classList.remove('pending');
    if (pc.status === 'passed') {
      // 通过 = actual === expected
      $actual.textContent = expected ? '是' : '否';
      $status.innerHTML = '<span class="status-pill ok">通过</span>';
    } else if (pc.status === 'failed') {
      // 失败 = actual !== expected
      $actual.textContent = expected ? '否' : '是';
      $status.innerHTML = '<span class="status-pill fail">失败</span>';
    } else {
      $actual.textContent = '—';
      $status.innerHTML = `<span class="status-pill tbd">${esc(pc.status)}</span>`;
    }
  });
}

// ============================================================
// 实时·性能测试：成员 tab + 动态参数表单
// ============================================================

let PERF_OWNER = 'siqi';

async function renderPerfView() {
  const html = `
    ${renderOwnerTabs(PERF_OWNER, 'performance')}
    <div id="perf-body"></div>
  `;
  $('#live-body').innerHTML = html;
  bindOwnerTabs('performance', (ownerId) => { PERF_OWNER = ownerId; renderPerfView(); });
  renderPerfBody();
}

// 每个成员的性能模型描述（工具 + 任务规格 + 运行提示文案）
const PERF_PROFILES = {
  siqi:    { tool: 'Locust',           spec: '120 并发 / 60s / 2s SLA', hint: (b) => `运行中（${b.run_time || '?'} + 收尾）` },
  xupeng:  { tool: 'Locust',           spec: '120 并发 / 60s / 2s SLA', hint: (b) => `运行中（${b.run_time || '?'} + 收尾）` },
  yusheng: { tool: 'Locust',           spec: '120 并发 / 60s / 2s SLA', hint: (b) => `运行中（${b.run_time || '?'} + 收尾）` },
  zhiyi:   { tool: 'Java HttpClient',  spec: '固定并发线程数 × 每线程请求数', hint: (b) => `运行中（${b.users} 线程 × ${b.requests_per_thread} 请求，含 mvn 启动）` },
};

// 表单字段元数据。每个 owner 通过 owner.test_cases.performance.supports 申明自己需要哪些字段。
const PERF_FIELD_META = {
  users:      { label: '并发用户数',  type: 'number', min: 1,   suffix: '人' },
  spawn_rate: { label: '每秒新增',    type: 'number', min: 1,   suffix: '人/秒' },
  run_time: {
    label: '持续时长', type: 'number', min: 1, suffix: '秒',
    defaultDisplay: (raw) => String(raw || '').replace(/s$/i, '') || '60',
    format: (raw) => `${Number(raw)}s`,
  },
  // zhiyi 专用字段
  requests_per_thread: { label: '每线程请求数', type: 'number', min: 1, suffix: '次' },
};

// zhiyi 的 users 字段在前端覆盖 label：含义不是"用户数"而是"并发线程数"，且最小值 101（>100 是 Java 侧硬断言）
const PERF_FIELD_OVERRIDES = {
  zhiyi: {
    users: { label: '并发线程数', min: 101, suffix: '线程', hint: '实验要求 >100' },
  },
};

function renderPerfBody() {
  const owner = META.owners.find(o => o.id === PERF_OWNER);
  if (!owner.available) {
    $('#perf-body').innerHTML = `<div class="card" style="text-align: center; color: var(--color-muted); padding: 40px;">🚧 ${esc(owner.display)} 的接口尚未提交</div>`;
    return;
  }
  const profile = PERF_PROFILES[PERF_OWNER] || { tool: '—', spec: '—', hint: () => '运行中…' };
  const defaults = owner.default_params.performance || {};
  const supports = (owner.test_cases.performance && owner.test_cases.performance.supports) || Object.keys(defaults);
  const overrides = PERF_FIELD_OVERRIDES[PERF_OWNER] || {};

  const fields = supports.map(k => {
    const baseMeta = PERF_FIELD_META[k] || { label: k, type: 'text' };
    const meta = { ...baseMeta, ...(overrides[k] || {}) };
    const rawDefault = defaults[k];
    const displayValue = meta.defaultDisplay ? meta.defaultDisplay(rawDefault) : (rawDefault ?? '');
    return `
      <div class="form-row">
        <label>${esc(meta.label)}</label>
        <input type="${meta.type}" id="perf-${k}" value="${esc(displayValue)}"
               ${meta.min != null ? `min="${meta.min}"` : ''}>
        ${meta.suffix ? `<span class="hint">${esc(meta.suffix)}</span>` : ''}
        ${meta.hint ? `<span class="hint" style="color: var(--color-accent);">${esc(meta.hint)}</span>` : ''}
      </div>`;
  }).join('');

  $('#perf-body').innerHTML = `
    <div class="card">
      <h3 style="margin-top: 0;">性能测试</h3>
      <div style="color: var(--color-muted); font-size:13px; margin-bottom: 16px;">
        负责成员：${esc(owner.display)}　·　工具：${esc(profile.tool)}　·　任务规格：${esc(profile.spec)}
      </div>
      ${fields}
      <button class="btn btn-large" id="btn-run-perf">🚀 开始压测</button>
      <div id="perf-result" style="margin-top: 16px;"></div>
    </div>
  `;

  $('#btn-run-perf').addEventListener('click', async () => {
    const btn = $('#btn-run-perf');
    const body = { owner: PERF_OWNER };
    supports.forEach(k => {
      const v = $(`#perf-${k}`).value;
      if (v === '') return;
      const meta = PERF_FIELD_META[k] || {};
      body[k] = meta.format ? meta.format(v) : v;
    });
    showRunning(btn, '#perf-result', profile.hint(body));
    try {
      const data = await apiPost('/api/run/performance', body);
      renderResultCard('#perf-result', data.entry);
    } catch (e) {
      renderErrorCard('#perf-result', e.message);
    } finally {
      btn.disabled = false; btn.innerHTML = '🚀 开始压测';
    }
  });
}

// ============================================================
// 历史记录页
// ============================================================

let HISTORY_FILTERS = { from: '', to: '', category: '', owner: '' };

async function renderHistory() {
  $app.innerHTML = `
    ${topbar('历史记录')}
    <div class="page">
      <div class="card" style="margin-bottom: 16px;">
        <div style="display: flex; gap: 16px; flex-wrap: wrap; align-items: center;">
          <span>时间</span>
          <input type="date" id="hist-from" value="${HISTORY_FILTERS.from}">
          <span>~</span>
          <input type="date" id="hist-to" value="${HISTORY_FILTERS.to}">
          <span>类别</span>
          <select id="hist-category">
            <option value="">全部</option>
            <option value="unit"${HISTORY_FILTERS.category==='unit'?' selected':''}>单元</option>
            <option value="integration"${HISTORY_FILTERS.category==='integration'?' selected':''}>集成</option>
            <option value="data"${HISTORY_FILTERS.category==='data'?' selected':''}>数据组合</option>
            <option value="performance"${HISTORY_FILTERS.category==='performance'?' selected':''}>性能</option>
          </select>
          <span>成员</span>
          <select id="hist-owner">
            <option value="">全部</option>
            ${OWNER_ORDER.map(o => `<option value="${o}"${HISTORY_FILTERS.owner===o?' selected':''}>${esc(META.owners.find(x=>x.id===o).display)}</option>`).join('')}
          </select>
          <button class="btn btn-secondary" id="hist-apply">应用筛选</button>
          <button class="btn btn-secondary" id="hist-reset">重置</button>
        </div>
      </div>
      <div id="hist-body"></div>
    </div>
  `;
  $('#hist-apply').addEventListener('click', () => {
    HISTORY_FILTERS = {
      from: $('#hist-from').value,
      to: $('#hist-to').value,
      category: $('#hist-category').value,
      owner: $('#hist-owner').value,
    };
    loadHistory();
  });
  $('#hist-reset').addEventListener('click', () => {
    HISTORY_FILTERS = { from: '', to: '', category: '', owner: '' };
    renderHistory();
  });
  await loadHistory();
}

async function loadHistory() {
  $('#hist-body').innerHTML = '<div class="card">加载中…</div>';
  const params = new URLSearchParams();
  if (HISTORY_FILTERS.from) params.set('from', HISTORY_FILTERS.from + 'T00:00:00');
  if (HISTORY_FILTERS.to)   params.set('to',   HISTORY_FILTERS.to   + 'T23:59:59');
  if (HISTORY_FILTERS.category) params.set('category', HISTORY_FILTERS.category);
  if (HISTORY_FILTERS.owner)    params.set('owner',    HISTORY_FILTERS.owner);
  const q = params.toString();
  const data = await apiGet('/api/history' + (q ? `?${q}` : ''));

  if (!data.entries.length) {
    $('#hist-body').innerHTML = `<div class="card" style="text-align:center; color: var(--color-muted); padding: 40px;">无记录。先去<a href="#/live/unit"> 实时测试 </a>跑一个吧。</div>`;
    return;
  }

  const CATEGORY_CN = { unit: '单元', integration: '集成', data: '数据', performance: '性能' };

  $('#hist-body').innerHTML = `
    <table class="history-table">
      <thead><tr>
        <th>时间</th><th>类别</th><th>用例</th><th>成员</th><th>结果</th><th>用时</th><th></th>
      </tr></thead>
      <tbody>
        ${data.entries.map((e, idx) => `
          <tr class="history-row" data-idx="${idx}">
            <td>${esc(fmtTime(e.started_at))}</td>
            <td>${esc(CATEGORY_CN[e.category] || e.category)}</td>
            <td>${esc(e.case_name)}<br><span style="font-size:11px; color: var(--color-muted);">${esc(e.case_id)}</span></td>
            <td>${esc(META.owners.find(o=>o.id===e.owner)?.display || e.owner)}</td>
            <td><span class="status-pill ${e.success?'ok':'fail'}">${e.success?'通过':'失败'}</span> ${e.passed}/${e.passed+e.failed}</td>
            <td>${fmtDuration(e.duration_sec)}</td>
            <td style="color: var(--color-muted);">展开 ▾</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  $$('.history-row').forEach(row => row.addEventListener('click', () => {
    const idx = Number(row.dataset.idx);
    const e = data.entries[idx];
    const next = row.nextElementSibling;
    if (next && next.classList.contains('history-detail-row')) {
      next.remove(); return;
    }
    const detail = h(`
      <tr class="history-detail-row">
        <td colspan="7">
          <div class="history-detail">
            <div style="margin-bottom: 8px;"><strong>参数：</strong> ${esc(JSON.stringify(e.params))}</div>
            ${e.report_url ? `<div style="margin-bottom: 8px;"><a href="${esc(e.report_url)}" target="_blank">📄 打开 HTML 报告</a></div>` : ''}
            <details>
              <summary style="cursor:pointer; color: var(--color-primary);">查看日志（${e.raw_output.length} 字符）</summary>
              <div class="log-wrap">
                <button class="log-copy-btn" type="button">复制</button>
                <div class="log-box">${esc(e.raw_output)}</div>
              </div>
            </details>
          </div>
        </td>
      </tr>
    `);
    row.after(detail);
  }));
}

// reportRelPath 已删除：报告 URL 现在由后端 _enrich() 直接给 entry.report_url。

// ============================================================
// 业务流程图
// ============================================================

function renderFlowchart() {
  $app.innerHTML = `
    ${topbar('业务流程图')}
    <div class="page">
      <div class="card" style="text-align: center;">
        <p style="color: var(--color-muted); margin-top: 0;">
          UI/web/static/flowchart.png
        </p>
        <img src="/static/flowchart.png"
             onerror="this.onerror=null; this.src='/static/flowchart.svg';"
             style="max-width: 100%; height: auto;" alt="business flowchart">
      </div>
    </div>
  `;
}

// ============================================================
// 快速测试 demo：4 人并行进度框
// ============================================================

const DEMO_STATE_CN = {
  passed: '全部通过', failed: '有失败用例', error: '运行出错',
  skipped: '已跳过', running: '运行中', pending: '等待',
};
const DEMO_PILL = {
  passed: 'ok', failed: 'fail', error: 'fail', skipped: 'tbd', running: 'run', pending: 'tbd',
};

function fmtMMSS(sec) {
  const s = Math.max(0, Math.floor(sec || 0));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

async function renderDemo() {
  $app.innerHTML = `
    ${topbar('快速测试 demo')}
    <div class="page">
      <div class="card demo-intro">
        <div>
          <h3 style="margin:0 0 4px;">4 人并行 · headless 后台一键演示</h3>
          <div style="color:var(--color-muted); font-size:13px;">
            每人 1 单元 + 1 集成 + 5 条数据组合（不含性能）。测试在后台无头运行，不会弹出浏览器窗口。
            产物与分析报告落到 <code>outputs/quick-demo/</code>。
          </div>
        </div>
        <div class="demo-actions">
          <span id="demo-overall" class="demo-overall"></span>
          <a id="demo-report-link" class="btn btn-secondary" style="display:none;" target="_blank">📄 查看分析报告</a>
          <button class="btn btn-large" id="btn-demo-start">▶ 开始 demo</button>
        </div>
      </div>
      <div class="demo-grid" id="demo-grid"><div class="loading">加载中…</div></div>
    </div>
  `;
  $('#btn-demo-start').addEventListener('click', startDemo);
  await refreshDemo();   // 首屏拉一次；若已有批次在跑会自动开始轮询
}

async function startDemo() {
  const btn = $('#btn-demo-start');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 启动中…';
  try {
    await apiPost('/api/demo/start');
    toast('demo 已启动，4 人并行后台运行中', 'ok');
  } catch (e) {
    toast('启动失败：' + e.message, 'fail', 5000);
    btn.disabled = false;
    btn.innerHTML = '▶ 开始 demo';
    return;
  }
  ensureDemoPolling();
  await refreshDemo();
}

function ensureDemoPolling() {
  if (!DEMO_TIMER) DEMO_TIMER = setInterval(refreshDemo, 1200);
}

async function refreshDemo() {
  // 路由切走（DOM 没了）就停掉轮询
  if (!document.getElementById('demo-grid')) {
    if (DEMO_TIMER) { clearInterval(DEMO_TIMER); DEMO_TIMER = null; }
    return;
  }
  let data;
  try { data = await apiGet('/api/demo/status'); }
  catch { return; }

  renderDemoBoxes(data);

  const btn = $('#btn-demo-start');
  const overall = $('#demo-overall');
  const link = $('#demo-report-link');

  if (data.status === 'running') {
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> 运行中…'; }
    if (overall) overall.textContent = `已用 ${fmtMMSS(data.elapsed_sec)}`;
    if (link) link.style.display = 'none';
    ensureDemoPolling();
  } else {
    if (DEMO_TIMER) { clearInterval(DEMO_TIMER); DEMO_TIMER = null; }
    if (btn) { btn.disabled = false; btn.innerHTML = '▶ 开始 demo'; }
    if (data.status === 'done') {
      if (overall) overall.textContent = `本批用时 ${fmtMMSS(data.elapsed_sec)}`;
      if (link && data.report_url) { link.href = data.report_url; link.style.display = ''; }
    } else if (overall) {
      overall.textContent = '';
    }
  }
}

function renderDemoBoxes(data) {
  const grid = $('#demo-grid');
  if (!grid) return;
  const owners = data.owners || [];
  if (!owners.length) {
    grid.innerHTML = `<div class="card" style="text-align:center; color:var(--color-muted); padding:40px;">点击右上角「开始 demo」启动 4 人并行测试</div>`;
    return;
  }
  grid.innerHTML = owners.map(o => {
    const pct = o.step_total ? Math.round((o.step_done / o.step_total) * 100) : 0;
    const stateCN = DEMO_STATE_CN[o.state] || o.state;
    const pill = DEMO_PILL[o.state] || 'tbd';
    const spin = o.state === 'running' ? '<span class="spinner"></span> ' : '';
    const steps = (o.steps || []).map(s =>
      `<li>${s.success ? '✅' : '❌'} ${esc(s.name)} <span class="demo-muted">${s.passed}/${s.passed + s.failed} · ${s.duration}s</span></li>`
    ).join('');
    const logs = (o.log_tail || []).slice(-6).map(l => esc(l)).join('<br>');
    const report = o.report_url
      ? `<a class="demo-box-report" href="${esc(o.report_url)}" target="_blank">查看报告 →</a>` : '';
    return `
      <div class="demo-box demo-box-${o.state}">
        <div class="demo-box-head">
          <span class="demo-box-name">${esc(o.display)}</span>
          <span class="status-pill ${pill}">${spin}${esc(stateCN)}</span>
        </div>
        <div class="demo-progress"><div class="demo-progress-bar" style="width:${pct}%"></div></div>
        <div class="demo-box-meta">
          <span>${o.step_done}/${o.step_total} 步</span>
          <span>通过 ${o.passed} · 失败 ${o.failed}</span>
          <span>${fmtMMSS(o.elapsed_sec)}</span>
        </div>
        <div class="demo-box-current">${esc(o.current_label)}</div>
        ${steps ? `<ul class="demo-steps">${steps}</ul>` : ''}
        ${logs ? `<div class="demo-log">${logs}</div>` : ''}
        ${report}
      </div>`;
  }).join('');
}

// ============================================================
// 通用：成员 tab / 运行中状态 / 结果卡片
// ============================================================

function renderOwnerTabs(activeId, scope) {
  return `
    <div class="tabs" id="owner-tabs-${scope}">
      ${OWNER_ORDER.map(id => {
        const o = META.owners.find(x => x.id === id);
        return `<div class="tab ${id === activeId ? 'active' : ''} ${o.available ? '' : 'disabled'}" data-owner="${id}">${esc(o.display)} <span class="badge">${o.available?'OK':'TBD'}</span></div>`;
      }).join('')}
    </div>
  `;
}

function bindOwnerTabs(scope, onSwitch) {
  $$(`#owner-tabs-${scope} .tab`).forEach(el => el.addEventListener('click', () => {
    if (el.classList.contains('disabled') || el.classList.contains('active')) return;
    onSwitch(el.dataset.owner);
  }));
}

function showRunning(btn, resultSel, hint) {
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 运行中…';
  $(resultSel).innerHTML = `
    <div class="result-card card run">
      <div>
        <span class="spinner spinner-on-light"></span>
        ${esc(hint)}
        <span class="run-timer" id="run-timer">已用 0:00</span>
      </div>
    </div>
  `;
  // 实时秒数滚动。result-card 一旦被 renderResultCard / renderErrorCard 替换，#run-timer 就找不到了，
  // setInterval 自动 self-clear，不需要在每个 handler 的 finally 里手动 clear。
  const start = Date.now();
  const tick = setInterval(() => {
    const el = $('#run-timer');
    if (!el) { clearInterval(tick); return; }
    const s = Math.floor((Date.now() - start) / 1000);
    el.textContent = `已用 ${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
  }, 1000);
}

function renderResultCard(sel, entry, opts = {}) {
  const $target = $(sel);
  const cls = entry.success ? 'ok' : 'fail';
  const pill = entry.success ? 'ok' : 'fail';
  let extraHtml = '';

  if (entry.category === 'performance') {
    const x = entry.extra || {};
    const cards = [
      metric('总请求', x.total_requests ?? '—'),
      metric('总失败', x.total_failures ?? '—'),
      metric('失败率', x.failure_rate_percent != null ? x.failure_rate_percent + '%' : '—'),
      metric('用时', fmtDuration(entry.duration_sec)),
    ];
    // 可选的延迟指标（zhiyi 的 Java HttpClient 模型会带这些字段；Locust 不带，自动不显示）
    if (x.avg_latency_ms != null) cards.push(metric('平均延迟', x.avg_latency_ms + ' ms'));
    if (x.p95_latency_ms != null) cards.push(metric('P95 延迟', x.p95_latency_ms + ' ms'));
    if (x.max_latency_ms != null) cards.push(metric('最大延迟', x.max_latency_ms + ' ms'));
    extraHtml = `<div class="metric-grid">${cards.join('')}</div>`;
  }
  $target.innerHTML = `
    <div class="result-card card ${cls}">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div>
          <span class="status-pill ${pill}">${entry.success ? '✅ 通过' : '❌ 失败'}</span>
          <strong style="margin-left: 8px;">${esc(entry.case_name)}</strong>
        </div>
        <span style="color: var(--color-muted); font-size: 13px;">${fmtDuration(entry.duration_sec)}</span>
      </div>
      <div style="color: var(--color-muted); font-size: 13px;">
        通过 ${entry.passed} · 失败 ${entry.failed} · 跳过 ${entry.skipped} ${opts.extraLabel ? '· ' + esc(opts.extraLabel) : ''}
      </div>
      ${extraHtml}
      ${entry.report_url ? `<div style="margin-top: 10px;"><a href="${esc(entry.report_url)}" target="_blank">📄 打开 HTML 报告</a></div>` : ''}
      <details style="margin-top: 10px;">
        <summary style="cursor: pointer; color: var(--color-primary);">查看完整日志</summary>
        <div class="log-wrap">
          <button class="log-copy-btn" type="button">复制</button>
          <div class="log-box">${esc(entry.raw_output)}</div>
        </div>
      </details>
    </div>
  `;
  // 自动滚到结果卡片，避免用户在长页面里没注意到（性能/集成跑完时尤其重要）
  try { $target.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch {}
  // 右上角 toast 补一条，结果卡片如果滚走了也不会错过
  toast(`${entry.case_name} ${entry.success ? '通过' : '失败'}`, entry.success ? 'ok' : 'fail');
}

function metric(label, value) {
  return `<div class="metric-card"><div class="label">${esc(label)}</div><div class="value">${esc(value)}</div></div>`;
}

function renderErrorCard(sel, msg) {
  $(sel).innerHTML = `
    <div class="result-card card fail">
      <span class="status-pill fail">错误</span>
      <span style="margin-left: 8px;">${esc(msg)}</span>
    </div>
  `;
  toast(`运行失败：${msg}`, 'fail', 5000);
}

function renderNotFound(path) {
  $app.innerHTML = `
    ${topbar('找不到页面')}
    <div class="page"><div class="card">未知路由：<code>${esc(path)}</code></div></div>
  `;
}

// ============================================================
// 免责声明 modal（首次进入实时测试时弹出）
// ============================================================

const DISCLAIMER_KEY = 'agreed_disclaimer_v1';

function needsDisclaimer() {
  try { return !localStorage.getItem(DISCLAIMER_KEY); }
  catch { return false; }   // 隐私模式 localStorage 不可用时直接放行，不阻塞
}

function showDisclaimerModal() {
  // hashchange 在 modal 已存在时可能重入；直接返回已有 promise 由原始那次解决
  if (document.getElementById('disclaimer-modal')) return Promise.resolve();
  return new Promise(resolve => {
    const $modal = h(`
      <div class="modal-backdrop" id="disclaimer-modal" role="dialog" aria-labelledby="disclaimer-title" aria-modal="true">
        <div class="modal-card">
          <div class="modal-header">
            <h3 id="disclaimer-title">⚠️ 使用须知</h3>
          </div>
          <div class="modal-body">
            <ul>
              <li>被测站点：<strong>automationexercise.com</strong>（公开自动化测试 demo 站）</li>
              <li>测试运行期间会<strong>自动打开浏览器</strong>并访问被测站点</li>
              <li>性能测试会以高并发向被测站点发起请求，请勿在生产环境运行</li>
              <li>本工具仅用于《软件质量保证与测试》课程教学与演示</li>
              <li>测试一旦启动<strong>无法中途终止</strong>，请确认参数后再运行</li>
            </ul>
          </div>
          <div class="modal-footer">
            <label class="modal-checkbox"><input type="checkbox" id="disclaimer-remember"> 不再显示此提示</label>
            <button class="btn" id="disclaimer-confirm" type="button">我已知悉，继续</button>
          </div>
        </div>
      </div>
    `);
    document.body.appendChild($modal);

    const close = () => {
      const cb = $('#disclaimer-remember');
      if (cb && cb.checked) {
        try { localStorage.setItem(DISCLAIMER_KEY, '1'); } catch {}
      }
      $modal.remove();
      document.removeEventListener('keydown', onKey, true);
      resolve();
    };
    const onKey = (e) => {
      if (e.key === 'Escape') { e.stopPropagation(); close(); }
      else if (e.key === 'Enter') { e.stopPropagation(); close(); }
    };
    $('#disclaimer-confirm').addEventListener('click', close);
    // 点 backdrop（modal 外区域）也关
    $modal.addEventListener('click', (e) => { if (e.target === $modal) close(); });
    // capture 阶段挂，免得被全局 ESC handler 抢走
    document.addEventListener('keydown', onKey, true);
    setTimeout(() => $('#disclaimer-confirm').focus(), 0);
  });
}

// ============================================================
// 全局 toast（右上角 3s 自动消失，可手动关）
// ============================================================

function ensureToastContainer() {
  let c = document.getElementById('toast-container');
  if (!c) {
    c = h('<div class="toast-container" id="toast-container" aria-live="polite"></div>');
    document.body.appendChild(c);
  }
  return c;
}

function toast(msg, type = 'info', timeout = 3000) {
  const c = ensureToastContainer();
  const icon = type === 'ok' ? '✅' : type === 'fail' ? '❌' : 'ℹ️';
  const t = h(`
    <div class="toast ${type}" role="status">
      <span class="toast-icon">${icon}</span>
      <span class="toast-msg">${esc(msg)}</span>
      <button class="toast-close" type="button" aria-label="关闭">×</button>
    </div>
  `);
  c.appendChild(t);
  const remove = () => {
    t.classList.add('leaving');
    setTimeout(() => t.remove(), 200);
  };
  t.querySelector('.toast-close').addEventListener('click', remove);
  if (timeout) setTimeout(remove, timeout);
}

// ============================================================
// 全局键盘（ESC 返回 / Enter 触发主按钮 / 日志一键复制）
// ============================================================

document.addEventListener('keydown', (e) => {
  // 弹窗自己处理 ESC（capture 阶段已截走），这里只做 live → 入口的返回
  if (e.key === 'Escape' && !document.querySelector('.modal-backdrop')) {
    if (parseHash().startsWith('/live')) {
      location.hash = '#/';
    } else if (parseHash() === '/history' || parseHash() === '/flowchart' || parseHash() === '/demo') {
      location.hash = '#/';
    }
    return;
  }
  // 表单内 Enter → 触发同卡片里的主按钮（仅文本/数字/select 聚焦；checkbox/textarea 跳过避免误触）
  if (e.key === 'Enter') {
    const tag = e.target.tagName;
    if (tag !== 'INPUT' && tag !== 'SELECT') return;
    const t = (e.target.type || '').toLowerCase();
    if (t === 'checkbox' || t === 'radio' || t === 'textarea') return;
    if (document.querySelector('.modal-backdrop')) return;
    const card = e.target.closest('.card');
    if (!card) return;
    const btn = card.querySelector('button.btn-large:not(:disabled), button.btn:not(:disabled)');
    if (btn) {
      e.preventDefault();
      btn.click();
    }
  }
});

// 委托：点 log-wrap 里的复制按钮 → 复制兄弟 log-box 的文本
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.log-copy-btn');
  if (!btn) return;
  const wrap = btn.closest('.log-wrap');
  if (!wrap) return;
  const box = wrap.querySelector('.log-box');
  if (!box) return;
  const text = box.textContent || '';
  const done = () => {
    btn.classList.add('copied');
    btn.textContent = '已复制 ✓';
    setTimeout(() => { btn.classList.remove('copied'); btn.textContent = '复制'; }, 1500);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done).catch(() => {
      // fallback: 旧浏览器或非 https
      fallbackCopy(text); done();
    });
  } else {
    fallbackCopy(text); done();
  }
});

function fallbackCopy(text) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); } catch {}
  ta.remove();
}
