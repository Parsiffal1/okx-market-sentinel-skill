const state = {
  pollHandle: null,
  frontendPollSeconds: 10,
  allHotSymbols: [],
  allNewsCards: [],
};

function qs(id) { return document.getElementById(id); }
function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}
function statusClass(value) {
  const raw = String(value || '').toLowerCase();
  if (['ok', 'bullish', 'low', 'healthy'].includes(raw)) return 'status-ok';
  if (['partial', 'medium', 'stale'].includes(raw)) return 'status-medium';
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
function readableTriggerName(value) {
  const mapping = {
    macro_risk_confluence: '宏观风险共振',
    macro_event_window: '宏观事件窗口',
    held_symbol_pressure: '持仓压力上升',
    held_symbol_event_cluster: '持仓事件簇',
    live_security_event: '实时安全事件',
  };
  return mapping[value] || value || '未知';
}
function riskColor(risk) {
  const raw = String(risk || '').toLowerCase();
  if (raw === 'high' || raw === 'extreme' || raw === 'bearish') return '#ef4444';
  if (raw === 'medium' || raw === 'partial' || raw === 'stale') return '#f59e0b';
  if (raw === 'low' || raw === 'bullish' || raw === 'ok') return '#22c55e';
  return '#7e87ff';
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
function renderWelcomeHero(summary, holdingsMeta, hotSymbols) {
  const holdingsCount = Number(holdingsMeta?.held_symbol_count || 0);
  const shortlistCount = Array.isArray(hotSymbols) ? hotSymbols.length : 0;
  let text = '先防守持仓，再扫描热点，再把真正值得处理的信号推到你面前。';
  if (holdingsCount === 0) {
    text = `当前无持仓，系统会把重点放在全市场风险和 ${shortlistCount || '少量'} 个值得继续观察的标的上。`;
  } else if (summary?.llm_wake_required) {
    text = `当前有 ${holdingsCount} 个持仓需要优先防守，而且已经触发进一步分析条件。`;
  }
  qs('welcome-hero-text').textContent = text;
}
function renderSentimentGauge(marketState, holdingsMeta) {
  const confidence = Math.max(0, Math.min(100, Math.round(Number((marketState?.sentiment_confidence ?? 0) * 100))));
  const sentiment = marketState?.market_sentiment || 'unknown';
  const holdings = holdingsMeta?.held_symbol_count || 0;
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - confidence / 100);
  const toneClass = statusClass(marketState?.risk_state || marketState?.market_sentiment);
  qs('sentiment-gauge').innerHTML = `
    <div class="gauge-wrap">
      <svg class="gauge-svg" viewBox="0 0 210 210" aria-hidden="true">
        <defs>
          <linearGradient id="sentimentGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#65d9ff" />
            <stop offset="100%" stop-color="#7e87ff" />
          </linearGradient>
          <filter id="gaugeGlow">
            <feGaussianBlur stdDeviation="4" result="blur"></feGaussianBlur>
            <feMerge>
              <feMergeNode in="blur"></feMergeNode>
              <feMergeNode in="SourceGraphic"></feMergeNode>
            </feMerge>
          </filter>
        </defs>
        <circle cx="105" cy="105" r="80" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="14"></circle>
        <circle cx="105" cy="105" r="80" fill="none" stroke="url(#sentimentGradient)" stroke-width="14" stroke-linecap="round" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}" filter="url(#gaugeGlow)"></circle>
      </svg>
      <div class="gauge-center">
        <div>
          <span>Market confidence</span>
          <strong class="${toneClass}">${confidence}%</strong>
          <p>${escapeHtml(sentiment)} · 持仓 ${holdings}</p>
        </div>
      </div>
    </div>`;
}
function renderWakeBanner(wakeState, summary) {
  const wakeRequired = Boolean(summary?.llm_wake_required || wakeState?.llm_wake_required);
  const priority = wakeState?.wake_priority || (wakeRequired ? 'high' : 'observe');
  const reasons = (wakeState?.wake_reasons || wakeState?.observe_only_reasons || []).map(readableTriggerName);
  const title = wakeRequired ? '需要进一步分析' : '当前以观察为主';
  const description = wakeRequired
    ? '多因子条件已达到升级阈值，建议进入更深一层的分析或人工复核。'
    : '当前没有达到升级条件，但系统仍会保留观察级别的提醒。';
  qs('wake-banner-body').innerHTML = `
    <div class="wake-main ${statusClass(priority)}">
      <strong>${title}</strong>
      <p>${description}</p>
    </div>
    <div class="wake-pill-row">
      <span class="tag ${statusClass(priority)}">优先级：${escapeHtml(priority)}</span>
      <span class="tag">风险等级：${escapeHtml(summary?.risk_state || '--')}</span>
      <span class="tag">事件窗口：${yesNo(summary?.event_window)}</span>
    </div>
    <div class="rank-meta">${reasons.length ? reasons.join(' ｜ ') : '本轮暂无额外升级原因'}</div>`;
}
function renderMarketState(marketState) {
  const summaryRows = (marketState.summary || []).map(item => `<li>${escapeHtml(item)}</li>`).join('') || '<li>无</li>';
  const macroRows = (marketState.macro_drivers || []).map(item => `<li>${escapeHtml(item)}</li>`).join('') || '<li>无</li>';
  const nativeRows = (marketState.crypto_native_risk_drivers || []).map(item => `<li>${escapeHtml(item)}</li>`).join('') || '<li>无</li>';
  qs('market-state').innerHTML = `
    <div class="metric-block emphasis-block">
      <h3>市场情绪 / 风险</h3>
      <p>市场情绪：<strong class="${statusClass(marketState.market_sentiment)}">${escapeHtml(marketState.market_sentiment || '--')}</strong></p>
      <p>风险等级：<strong class="${statusClass(marketState.risk_state)}">${escapeHtml(marketState.risk_state || '--')}</strong> ｜ 地缘风险：<strong class="${statusClass(marketState.geo_risk)}">${escapeHtml(marketState.geo_risk || '--')}</strong></p>
      <p>事件窗口：<strong>${yesNo(marketState.event_window)}</strong> ｜ 置信度：<strong>${marketState.sentiment_confidence ?? '--'}</strong></p>
    </div>
    <div class="metric-block"><h3>摘要</h3><ul>${summaryRows}</ul></div>
    <div class="metric-block"><h3>宏观驱动</h3><ul>${macroRows}</ul></div>
    <div class="metric-block"><h3>加密原生风险驱动</h3><ul>${nativeRows}</ul></div>`;
}
function renderHoldingsPriorityHero(holdingsState, holdingsMeta) {
  const hasPositions = Boolean(holdingsState?.has_positions);
  if (!hasPositions) {
    qs('holdings-priority-hero').innerHTML = `
      <div class="empty-state-card">
        <div class="empty-state-icon">◎</div>
        <div>
          <h3>当前无持仓</h3>
          <p>系统仍会持续监控全市场风险、热点品种与 OI 异动，但页面会自动保持简洁，不让空模块破坏整体观感。</p>
        </div>
      </div>`;
    return;
  }
  const symbols = (holdingsState.prioritized_symbols || []).join('、') || '无';
  const highest = holdingsMeta?.highest_risk_state || 'unknown';
  qs('holdings-priority-hero').innerHTML = `
    <div class="priority-state-card">
      <div>
        <span class="section-kicker">持仓优先</span>
        <h3>当前持仓：${escapeHtml(symbols)}</h3>
        <p>持仓风险会优先于全市场热榜展示，确保防守决策先于机会扫描。</p>
      </div>
      <div class="priority-risk-chip ${statusClass(highest)}">最高风险：${escapeHtml(highest)}</div>
    </div>`;
}
function renderHoldings(holdingsState, holdingsMeta) {
  renderHoldingsPriorityHero(holdingsState, holdingsMeta);
  const rows = holdingsState?.symbol_risk || [];
  if (!rows.length) {
    qs('holdings-risk-list').innerHTML = '';
    return;
  }
  qs('holdings-risk-list').innerHTML = rows.map(item => `
    <article class="holding-item">
      <div class="rank-item-top"><h3>${escapeHtml(item.symbol)}</h3><span class="tag ${statusClass(item.risk_state)}">${escapeHtml(item.risk_state)}</span></div>
      <div class="rank-meta">事件数：${item.relevant_event_count || 0} ｜ 社媒热度：${item.relevant_social_heat || 0}</div>
      <div class="submeta">${escapeHtml((item.reasons || []).join('；') || '无明确原因')}</div>
    </article>`).join('');
}
function renderHoldingsScatter(holdingsState) {
  const container = qs('holdings-scatter-plot');
  const rows = holdingsState?.symbol_risk || [];
  if (!rows.length) {
    container.innerHTML = '<div class="empty-state-card"><div><h3>暂无持仓散点</h3><p>有持仓后，这里会显示事件数和社媒热度的相对位置。</p></div></div>';
    return;
  }
  const width = 460;
  const height = 260;
  const pad = {left: 44, right: 18, top: 18, bottom: 36};
  const maxEvents = Math.max(...rows.map(item => Number(item.relevant_event_count || 0)), 1);
  const maxHeat = Math.max(...rows.map(item => Number(item.relevant_social_heat || 0)), 1);
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  const points = rows.map(item => {
    const events = Number(item.relevant_event_count || 0);
    const heat = Number(item.relevant_social_heat || 0);
    const x = pad.left + (events / maxEvents) * plotW;
    const y = pad.top + plotH - (heat / maxHeat) * plotH;
    return {item, x, y};
  });
  const gridLines = Array.from({length: 4}, (_, i) => {
    const y = pad.top + (plotH / 3) * i;
    return `<line class="scatter-grid" x1="${pad.left}" y1="${y}" x2="${width - pad.right}" y2="${y}" />`;
  }).join('');
  const labels = `
    <text class="scatter-label" x="${width / 2}" y="${height - 8}" text-anchor="middle">事件数</text>
    <text class="scatter-label" x="14" y="${height / 2}" transform="rotate(-90 14 ${height / 2})" text-anchor="middle">社媒热度</text>
    <text class="scatter-label" x="${pad.left}" y="${height - 16}">0</text>
    <text class="scatter-label" x="${width - pad.right}" y="${height - 16}" text-anchor="end">${maxEvents}</text>`;
  const dots = points.map(({item, x, y}) => `
    <circle class="scatter-point" cx="${x}" cy="${y}" r="7" fill="${riskColor(item.risk_state)}"></circle>
    <text class="scatter-label" x="${x}" y="${Math.max(14, y - 12)}" text-anchor="middle">${escapeHtml(item.symbol)}</text>`).join('');
  const legend = rows.map(item => `<span class="tag ${statusClass(item.risk_state)}">${escapeHtml(item.symbol)} · ${escapeHtml(item.risk_state)}</span>`).join('');
  container.innerHTML = `
    <svg class="scatter-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
      ${gridLines}
      <line class="scatter-axis" x1="${pad.left}" y1="${height - pad.bottom}" x2="${width - pad.right}" y2="${height - pad.bottom}" />
      <line class="scatter-axis" x1="${pad.left}" y1="${pad.top}" x2="${pad.left}" y2="${height - pad.bottom}" />
      ${labels}
      ${dots}
    </svg>
    <div class="scatter-legend">${legend}</div>`;
}
function renderSourceComposition(meta) {
  const container = qs('source-composition-chart');
  const counts = Object.entries(meta?.source_counts || {}).sort((a, b) => b[1] - a[1]);
  if (!counts.length) {
    container.innerHTML = '<div class="composition-item"><div class="submeta">暂无来源构成数据</div></div>';
    return;
  }
  const max = Math.max(...counts.map(([, value]) => Number(value || 0)), 1);
  container.innerHTML = counts.map(([label, value]) => `
    <article class="composition-item">
      <div class="composition-row"><strong>${escapeHtml(label)}</strong><span class="mono">${value}</span></div>
      <div class="composition-bar-track"><div class="composition-bar" style="width:${Math.max(8, (Number(value || 0) / max) * 100)}%"></div></div>
    </article>`).join('');
}
function renderScoreBars(items) {
  const container = qs('score-bar-chart');
  if (!(items || []).length) {
    container.innerHTML = '<div class="score-bar-item"><div class="submeta">暂无分数数据</div></div>';
    return;
  }
  const max = Math.max(...items.map(item => Number(item.score || 0)), 1);
  container.innerHTML = items.slice(0, 6).map(item => `
    <article class="score-bar-item">
      <div class="score-head"><strong>${escapeHtml(item.symbol)}</strong><span class="tag">${prettyAssetClass(item.asset_class)}</span><span class="mono">${item.score}</span></div>
      <div class="score-track"><div class="score-fill" style="width:${Math.max(10, (Number(item.score || 0) / max) * 100)}%"></div></div>
    </article>`).join('');
}
function renderHotSymbols(items) {
  state.allHotSymbols = items || [];
  applySearchFilter();
}
function renderHotSymbolsTable(items) {
  const body = qs('hot-symbols-table-body');
  if (!(items || []).length) {
    body.innerHTML = '<tr><td colspan="6" class="table-empty">暂无热榜数据</td></tr>';
    return;
  }
  body.innerHTML = (items || []).map(item => `
    <tr>
      <td class="mono">#${item.rank}</td>
      <td><strong>${escapeHtml(item.symbol)}</strong></td>
      <td>${prettyAssetClass(item.asset_class)}</td>
      <td class="mono">${item.score}</td>
      <td>${escapeHtml(item.source_summary)}</td>
      <td>${escapeHtml(item.signal_summary)}</td>
    </tr>`).join('');
}
function renderQuadrants(quadrants, quadrantCounts) {
  const mapping = {
    oi_up_price_up: ['OI↑ + 价格↑', '新多头建仓，通常是最强势资金状态'],
    oi_up_price_down: ['OI↑ + 价格↓', '新空头加仓，偏风险压制'],
    oi_down_price_up: ['OI↓ + 价格↑', '空头回补推动价格反弹'],
    oi_down_price_down: ['OI↓ + 价格↓', '多头离场，趋势延续度偏弱'],
  };
  qs('quadrant-grid').innerHTML = Object.entries(mapping).map(([key, [title, desc]]) => {
    const rows = (quadrants[key] || []).map(item => `<li><strong>${escapeHtml(item.symbol)}</strong><span class="mono">${item.score}</span></li>`).join('') || '<li class="empty-list">无</li>';
    return `<article class="quadrant-card"><div class="rank-item-top"><h3>${title}</h3><span class="quadrant-count">${quadrantCounts?.[key] ?? 0}</span></div><p class="submeta">${desc}</p><ul>${rows}</ul></article>`;
  }).join('');
}
function newsList(items) {
  return (items || []).map(item => {
    const chips = [];
    if (item.importance) chips.push(`<span class="news-chip ${statusClass(item.importance)}">${escapeHtml(item.importance)}</span>`);
    for (const symbol of (item.symbols || [])) chips.push(`<span class="news-chip">${escapeHtml(symbol)}</span>`);
    return `<li><strong>${escapeHtml(item.title)}</strong><span class="news-source">来源：${escapeHtml(item.source)}</span>${chips.length ? `<div class="news-chip-row">${chips.join('')}</div>` : ''}</li>`;
  }).join('') || '<li>无</li>';
}
function renderHighImpactNews(news) {
  qs('high-impact-news-list').innerHTML = `<article class="high-impact-card"><ul>${newsList(news.high_impact)}</ul></article>`;
}
function renderNews(news) {
  const groups = [['宏观 / 地缘', news.macro_geo], ['美股风险情绪', news.us_equity], ['安全事件', news.security], ['持续关注新闻', news.watchlist]];
  qs('news-columns').innerHTML = groups.map(([title, items]) => `
    <article class="news-card">
      <h3>${title}</h3>
      <ul>${newsList(items)}</ul>
    </article>`).join('');
}
function renderHealth(health, summary) {
  const counts = {ok: 0, partial: 0, stale: 0, error: 0};
  Object.values(health || {}).forEach(value => {
    const raw = String(value || 'unknown').toLowerCase();
    if (counts[raw] !== undefined) counts[raw] += 1;
  });
  qs('health-overview-chart').innerHTML = `
    <article class="health-overview-item"><span>Overall</span><strong class="${statusClass(summary.health_overview)}">${escapeHtml(summary.health_overview)}</strong></article>
    <article class="health-overview-item"><span>OK</span><strong class="status-ok">${counts.ok}</strong></article>
    <article class="health-overview-item"><span>Partial / Stale</span><strong class="status-medium">${counts.partial + counts.stale}</strong></article>
    <article class="health-overview-item"><span>Error</span><strong class="status-high">${counts.error}</strong></article>`;
  qs('health-list').innerHTML = Object.entries(health || {}).map(([key, value]) => `
    <article class="health-item">
      <div>
        <strong>${escapeHtml(key)}</strong>
        <div class="submeta">${healthText(value)}</div>
      </div>
      <span class="tag ${statusClass(value)}">${escapeHtml(value)}</span>
    </article>`).join('');
}
function renderSemanticCompass(settings) {
  qs('semantic-compass-brief').value = settings.semantic_compass_focus || settings.semantic_compass_last_brief || '';
  qs('semantic-compass-status').textContent = `状态：${settings.semantic_compass_refresh_status || 'idle'}`;
  qs('semantic-compass-updated').textContent = `最近刷新：${settings.semantic_compass_last_updated_at || '--'}`;
}
function applySearchFilter() {
  const keyword = String(qs('dashboard-search')?.value || '').trim().toUpperCase();
  if (!keyword) {
    renderHotSymbolsTable(state.allHotSymbols || []);
    return;
  }
  const filtered = (state.allHotSymbols || []).filter(item => String(item.symbol || '').toUpperCase().includes(keyword) || String(item.source_summary || '').toUpperCase().includes(keyword) || String(item.signal_summary || '').toUpperCase().includes(keyword));
  renderHotSymbolsTable(filtered);
}
async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
async function loadDashboard() {
  const payload = await fetchJson('/api/dashboard');
  renderSummary(payload.summary, payload.generated_at);
  renderWelcomeHero(payload.summary || {}, payload.holdings_meta || {}, payload.hot_symbols || []);
  renderSentimentGauge(payload.market_state || {}, payload.holdings_meta || {});
  renderWakeBanner(payload.wake_state || {}, payload.summary || {});
  renderHoldings(payload.holdings_state || {}, payload.holdings_meta || {});
  renderHoldingsScatter(payload.holdings_state || {});
  renderMarketState(payload.market_state || {});
  renderSourceComposition(payload.hot_symbols_meta || {});
  renderScoreBars(payload.hot_symbols_meta?.score_series || payload.hot_symbols || []);
  renderHotSymbols(payload.hot_symbols || []);
  renderQuadrants(payload.quadrants || {}, payload.quadrant_counts || {});
  renderHighImpactNews(payload.news || {});
  renderNews(payload.news || {});
  renderHealth(payload.health || {}, payload.summary || {});
  qs('backend-refresh-minutes').value = String(payload.settings.backend_refresh_minutes);
  qs('frontend-poll-seconds').value = String(payload.settings.frontend_poll_seconds);
  renderSemanticCompass(payload.settings || {});
  state.frontendPollSeconds = Number(payload.settings.frontend_poll_seconds || 10);
}
async function saveSettings() {
  await fetchJson('/api/config', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      backend_refresh_minutes: Number(qs('backend-refresh-minutes').value),
      frontend_poll_seconds: Number(qs('frontend-poll-seconds').value),
      theme: 'dark',
      compact_mode: false,
      semantic_compass_focus: qs('semantic-compass-brief').value.trim(),
    }),
  });
  restartPolling();
  closeDrawer();
  await loadDashboard();
}
async function refreshNow() {
  const button = qs('refresh-now');
  button.disabled = true;
  button.textContent = '刷新中...';
  try {
    await fetchJson('/api/refresh', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
    await loadDashboard();
  } finally {
    button.disabled = false;
    button.textContent = '立即刷新';
  }
}
async function refreshSemanticCompass() {
  const button = qs('refresh-semantic-compass');
  button.disabled = true;
  button.textContent = '刷新中...';
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
  qs('dashboard-search').addEventListener('input', applySearchFilter);
  await loadDashboard();
  restartPolling();
});
