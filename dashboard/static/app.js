const state = {
  pollHandle: null,
  frontendPollSeconds: 10,
  drawerOpen: false,
};

function qs(id) { return document.getElementById(id); }
function statusClass(value) {
  const raw = String(value || '').toLowerCase();
  if (['ok', 'bullish', 'low'].includes(raw)) return 'status-ok';
  if (['partial', 'medium'].includes(raw)) return 'status-medium';
  if (['high', 'error', 'extreme', 'bearish'].includes(raw)) return 'status-high';
  return 'status-neutral';
}
function yesNo(v) { return v ? '是' : '否'; }
function prettyAssetClass(v) {
  const mapping = {crypto: '加密', us_equity: '美股', precious_metal: '贵金属', commodity: '大宗商品'};
  return mapping[v] || v || '--';
}
function healthText(value) {
  const mapping = {ok: '数据正常', partial: '部分异常', error: '数据异常', stale: '数据过期', unknown: '状态未知'};
  return mapping[value] || value || '--';
}
function openDrawer() {
  qs('settings-drawer').classList.add('open');
  qs('settings-drawer').setAttribute('aria-hidden', 'false');
}
function closeDrawer() {
  qs('settings-drawer').classList.remove('open');
  qs('settings-drawer').setAttribute('aria-hidden', 'true');
}
function renderSummary(summary, generatedAt) {
  qs('regime-bias').textContent = summary.regime_bias || '--';
  qs('regime-bias').className = statusClass(summary.regime_bias);
  qs('risk-state').textContent = summary.risk_state || '--';
  qs('risk-state').className = statusClass(summary.risk_state);
  qs('llm-wake').textContent = yesNo(summary.llm_wake_required);
  qs('event-window').textContent = yesNo(summary.event_window);
  qs('health-overview').textContent = healthText(summary.health_overview);
  qs('health-overview').className = statusClass(summary.health_overview);
  qs('generated-at').textContent = generatedAt || '--';
  qs('generated-at').className = 'mono';
  qs('top-health-text').textContent = healthText(summary.health_overview);
  qs('top-health-dot').className = `dot ${statusClass(summary.health_overview)}`;
}
function renderMarketState(marketState) {
  qs('market-state').innerHTML = `
    <div class="metric-block emphasis-block">
      <h3>市场情绪 / 风险</h3>
      <p>市场情绪：<strong class="${statusClass(marketState.market_sentiment)}">${marketState.market_sentiment || '--'}</strong></p>
      <p>风险等级：<strong class="${statusClass(marketState.risk_state)}">${marketState.risk_state || '--'}</strong> ｜ 地缘风险：<strong class="${statusClass(marketState.geo_risk)}">${marketState.geo_risk || '--'}</strong></p>
      <p>事件窗口：<strong>${yesNo(marketState.event_window)}</strong> ｜ 置信度：<strong>${marketState.sentiment_confidence ?? '--'}</strong></p>
    </div>
    <div class="metric-block"><h3>宏观驱动</h3><ul>${(marketState.macro_drivers || []).map(item => `<li>${item}</li>`).join('') || '<li>无</li>'}</ul></div>
    <div class="metric-block"><h3>加密原生风险驱动</h3><ul>${(marketState.crypto_native_risk_drivers || []).map(item => `<li>${item}</li>`).join('') || '<li>无</li>'}</ul></div>`;
}
function renderHoldingsPriorityHero(holdingsState) {
  const hasPositions = Boolean(holdingsState?.has_positions);
  if (!hasPositions) {
    qs('holdings-priority-hero').innerHTML = `
      <div class="empty-state-card">
        <div class="empty-state-icon">◎</div>
        <div>
          <h3>当前无持仓</h3>
          <p>系统仍会持续监控全市场风险、热点品种与 OI 异动，但页面视觉会自动保持简洁，不让空模块破坏整体观感。</p>
        </div>
      </div>`;
    return;
  }
  const symbols = (holdingsState.prioritized_symbols || []).join('、') || '无';
  const highest = (holdingsState.symbol_risk || []).map(item => item.risk_state || 'unknown')[0] || 'unknown';
  qs('holdings-priority-hero').innerHTML = `
    <div class="priority-state-card">
      <div>
        <span class="section-kicker">持仓优先</span>
        <h3>当前持仓：${symbols}</h3>
        <p>持仓风险会优先于全市场热榜展示，确保防守决策先于机会扫描。</p>
      </div>
      <div class="priority-risk-chip ${statusClass(highest)}">最高风险：${highest}</div>
    </div>`;
}
function renderHoldings(holdingsState) {
  renderHoldingsPriorityHero(holdingsState);
  const rows = holdingsState?.symbol_risk || [];
  if (!rows.length) {
    qs('holdings-risk-list').innerHTML = '';
    return;
  }
  qs('holdings-risk-list').innerHTML = rows.map(item => `
    <article class="holding-item">
      <div class="rank-item-top"><h3>${item.symbol}</h3><span class="tag ${statusClass(item.risk_state)}">${item.risk_state}</span></div>
      <div class="rank-meta">事件数：${item.relevant_event_count || 0} ｜ 社媒热度：${item.relevant_social_heat || 0}</div>
      <div class="submeta">${(item.reasons || []).join('；') || '无明确原因'}</div>
    </article>`).join('');
}
function renderHotSymbols(items) {
  const body = qs('hot-symbols-table-body');
  if (!(items || []).length) {
    body.innerHTML = '<tr><td colspan="6" class="table-empty">暂无热榜数据</td></tr>';
    return;
  }
  body.innerHTML = (items || []).map(item => `
    <tr>
      <td class="mono">#${item.rank}</td>
      <td><strong>${item.symbol}</strong></td>
      <td>${prettyAssetClass(item.asset_class)}</td>
      <td class="mono">${item.score}</td>
      <td>${item.source_summary}</td>
      <td>${item.signal_summary}</td>
    </tr>`).join('');
}
function renderQuadrants(quadrants) {
  const mapping = {
    oi_up_price_up: ['OI↑ + 价格↑', '新多头建仓，通常是最强势资金状态'],
    oi_up_price_down: ['OI↑ + 价格↓', '新空头加仓，偏风险压制'],
    oi_down_price_up: ['OI↓ + 价格↑', '空头回补推动价格反弹'],
    oi_down_price_down: ['OI↓ + 价格↓', '多头离场，趋势延续度偏弱'],
  };
  qs('quadrant-grid').innerHTML = Object.entries(mapping).map(([key, [title, desc]]) => {
    const rows = (quadrants[key] || []).map(item => `<li><strong>${item.symbol}</strong><span class="mono">${item.score}</span></li>`).join('') || '<li class="empty-list">无</li>';
    return `<article class="quadrant-card"><h3>${title}</h3><p class="submeta">${desc}</p><ul>${rows}</ul></article>`;
  }).join('');
}
function renderNews(news) {
  const groups = [['宏观 / 地缘', news.macro_geo], ['美股风险情绪', news.us_equity], ['安全事件', news.security], ['持续关注新闻', news.watchlist]];
  qs('news-columns').innerHTML = groups.map(([title, items]) => `
    <article class="news-card">
      <h3>${title}</h3>
      <ul>${(items || []).map(item => `<li><strong>${item.title}</strong><span class="news-source">来源：${item.source}</span></li>`).join('') || '<li>无</li>'}</ul>
    </article>`).join('');
}
function renderHealth(health) {
  qs('health-list').innerHTML = Object.entries(health || {}).map(([key, value]) => `
    <article class="health-item">
      <div class="rank-item-top"><h3>${key}</h3><span class="tag ${statusClass(value)}">${value}</span></div>
      <div class="submeta">${healthText(value)}</div>
    </article>`).join('');
}
function renderSemanticCompass(settings) {
  qs('semantic-compass-brief').value = settings.semantic_compass_focus || settings.semantic_compass_last_brief || '';
  qs('semantic-compass-status').textContent = `状态：${settings.semantic_compass_refresh_status || 'idle'}`;
  qs('semantic-compass-updated').textContent = `最近刷新：${settings.semantic_compass_last_updated_at || '--'}`;
}
async function fetchJson(url, options = {}) { const res = await fetch(url, options); if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json(); }
async function loadDashboard() {
  const payload = await fetchJson('/api/dashboard');
  renderSummary(payload.summary, payload.generated_at);
  renderHoldings(payload.holdings_state || {});
  renderMarketState(payload.market_state || {});
  renderHotSymbols(payload.hot_symbols || []);
  renderQuadrants(payload.quadrants || {});
  renderNews(payload.news || {});
  renderHealth(payload.health || {});
  qs('backend-refresh-minutes').value = String(payload.settings.backend_refresh_minutes);
  qs('frontend-poll-seconds').value = String(payload.settings.frontend_poll_seconds);
  renderSemanticCompass(payload.settings || {});
  state.frontendPollSeconds = Number(payload.settings.frontend_poll_seconds || 10);
}
async function saveSettings() {
  await fetchJson('/api/config', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({backend_refresh_minutes: Number(qs('backend-refresh-minutes').value), frontend_poll_seconds: Number(qs('frontend-poll-seconds').value), theme: 'dark', compact_mode: false, semantic_compass_focus: qs('semantic-compass-brief').value.trim()})});
  restartPolling();
  closeDrawer();
  await loadDashboard();
}
async function refreshNow() {
  const button = qs('refresh-now'); button.disabled = true; button.textContent = '刷新中...';
  try { await fetchJson('/api/refresh', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'}); await loadDashboard(); }
  finally { button.disabled = false; button.textContent = '立即刷新'; }
}
async function refreshSemanticCompass() {
  const button = qs('refresh-semantic-compass'); button.disabled = true; button.textContent = '刷新中...';
  try {
    await fetchJson('/api/semantic-compass/refresh', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({brief: qs('semantic-compass-brief').value.trim()}),
    });
    await loadDashboard();
  } finally {
    button.disabled = false;
    button.textContent = '刷新 Semantic Compass';
  }
}
function restartPolling() {
  if (state.pollHandle) clearInterval(state.pollHandle);
  const seconds = Number(qs('frontend-poll-seconds').value || state.frontendPollSeconds || 10);
  state.pollHandle = setInterval(() => loadDashboard().catch(console.error), seconds * 1000);
}
document.addEventListener('DOMContentLoaded', async () => {
  qs('save-settings').addEventListener('click', () => saveSettings().catch(console.error));
  qs('refresh-now').addEventListener('click', () => refreshNow().catch(console.error));
  qs('refresh-semantic-compass').addEventListener('click', () => refreshSemanticCompass().catch(console.error));
  qs('open-settings').addEventListener('click', openDrawer);
  qs('close-settings').addEventListener('click', closeDrawer);
  qs('drawer-backdrop').addEventListener('click', closeDrawer);
  await loadDashboard();
  restartPolling();
});
