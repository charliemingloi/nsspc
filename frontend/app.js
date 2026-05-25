/* ═══════════════════════════════════════════════════
   AgroSmart AI — Application Logic
   ═══════════════════════════════════════════════════ */

const API = '';  // relative to same origin

// ─── App State ────────────────────────────────────────
const state = {
  farms: {},
  activeFarmId: null,
  sensorData: null,
  historicalData: null,
  agriChatHistory: [],
  farmChatHistory: {},
  productChatHistory: [],
  agents: [],
  sensorRefreshInterval: null,
  predictionResult: null,
};

// ─── Init ─────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  checkApiHealth();
  loadFarms();
  loadAgents();
  loadCatalog();
});

async function checkApiHealth() {
  try {
    const res = await fetch(`${API}/api/health`);
    const data = await res.json();
    const dot = document.getElementById('apiStatus').querySelector('.status-dot');
    const text = document.getElementById('apiStatus').querySelector('.status-text');
    if (data.api_key_configured) {
      dot.className = 'status-dot online';
      text.textContent = 'AI Ready';
    } else {
      dot.className = 'status-dot offline';
      text.textContent = 'API Key Missing';
      showToast('⚠️ Set ANTHROPIC_API_KEY to enable AI features', 'error');
    }
  } catch {
    const dot = document.getElementById('apiStatus').querySelector('.status-dot');
    const text = document.getElementById('apiStatus').querySelector('.status-text');
    dot.className = 'status-dot offline';
    text.textContent = 'Server Offline';
  }
}

// ─── Navigation ───────────────────────────────────────
function switchTab(tabName) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`tab-${tabName}`).classList.add('active');
  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

  if (tabName === 'monitor') {
    populateFarmSelects();
    if (state.activeFarmId) loadFarmDashboard();
  }
}

// ─── Farm Management ──────────────────────────────────
async function loadFarms() {
  try {
    const res = await fetch(`${API}/api/farms`);
    const data = await res.json();
    state.farms = data.farms || {};
    populateFarmSelects();
  } catch (e) {
    console.error('Failed to load farms:', e);
  }
}

function populateFarmSelects() {
  const farmIds = Object.keys(state.farms);
  const options = farmIds.map(id =>
    `<option value="${id}" ${id === state.activeFarmId ? 'selected' : ''}>${state.farms[id].name}</option>`
  ).join('');
  const noOption = '<option value="">Select a farm</option>';

  const globalSelect = document.getElementById('globalFarmSelect');
  const monitorSelect = document.getElementById('monitorFarmSelect');

  globalSelect.innerHTML = `<option value="">No farm selected</option>` + options;
  monitorSelect.innerHTML = noOption + options;

  if (state.activeFarmId) {
    globalSelect.value = state.activeFarmId;
    monitorSelect.value = state.activeFarmId;
  }
}

function onGlobalFarmChange() {
  const val = document.getElementById('globalFarmSelect').value;
  state.activeFarmId = val || null;
  populateFarmSelects();
}

// ─── Land Prediction ──────────────────────────────────
async function submitLandPrediction(e) {
  e.preventDefault();

  const landData = {
    location: document.getElementById('location').value,
    area: document.getElementById('area').value,
    soil_type: document.getElementById('soilType').value,
    soil_ph: document.getElementById('soilPh').value,
    climate: document.getElementById('climate').value,
    rainfall: document.getElementById('rainfall').value,
    water_source: document.getElementById('waterSource').value,
    topography: document.getElementById('topography').value,
    budget: document.getElementById('budget').value,
    experience: document.getElementById('experience').value,
    preferred_crops: document.getElementById('preferredCrops').value,
    goals: document.getElementById('goals').value,
  };

  const farmName = document.getElementById('farmName').value;

  showPredictionLoading(true);
  document.getElementById('predictBtn').disabled = true;

  try {
    // Run prediction and create farm in parallel
    const [predRes, _] = await Promise.all([
      fetch(`${API}/api/predict-land`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(landData)
      }),
      fetch(`${API}/api/farms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: farmName,
          location: landData.location,
          area: landData.area,
          crops: landData.preferred_crops,
          growth_stage: 'Planning',
          experience: landData.experience
        })
      }).then(r => r.json()).then(d => {
        if (d.farm_id) {
          state.activeFarmId = d.farm_id;
          loadFarms();
        }
      })
    ]);

    const prediction = await predRes.json();
    state.predictionResult = prediction;
    renderPrediction(prediction, farmName, landData);

  } catch (err) {
    showToast('Failed to get prediction: ' + err.message, 'error');
  } finally {
    showPredictionLoading(false);
    document.getElementById('predictBtn').disabled = false;
  }
}

function showPredictionLoading(show) {
  document.getElementById('predictionLoading').style.display = show ? 'flex' : 'none';
}

function renderPrediction(pred, farmName, landData) {
  document.getElementById('predictionResults').style.display = 'block';

  // Score card
  const score = pred.overall_suitability_score || 0;
  document.getElementById('scoreValue').textContent = Math.round(score);
  document.getElementById('scoreFarmName').textContent = farmName || 'Farm Analysis';
  document.getElementById('scoreSummary').textContent = pred.summary || '';
  const scoreCircle = document.getElementById('scoreCircle');
  scoreCircle.style.borderColor = score >= 75 ? '#52b788' : score >= 50 ? '#f59e0b' : '#ef4444';

  // Quick wins
  const wins = pred.quick_wins || [];
  document.getElementById('quickWins').innerHTML = wins.map(w =>
    `<span class="win-badge">✓ ${w}</span>`
  ).join('');

  // Recommended crops
  const crops = pred.recommended_crops || [];
  document.getElementById('cropCards').innerHTML = crops.map((c, i) => `
    <div class="crop-card">
      <div class="crop-card-rank">${i + 1}</div>
      <div class="crop-name">${c.name}</div>
      <div class="crop-confidence">${c.confidence}% confidence</div>
      <div class="confidence-bar"><div class="confidence-fill" style="width:${c.confidence}%"></div></div>
      <div class="crop-stat"><span>Yield/ha</span><span>${c.yield_per_hectare}</span></div>
      <div class="crop-stat"><span>Revenue/year</span><span>${c.annual_revenue_estimate}</span></div>
      <div class="crop-stat"><span>Season</span><span>${c.growing_season_months} months</span></div>
      <span class="difficulty-badge difficulty-${c.difficulty}">${c.difficulty}</span>
    </div>
  `).join('');

  // ROI Analysis
  const roi = pred.roi_analysis || {};
  document.getElementById('roiGrid').innerHTML = `
    <div class="roi-item"><div class="roi-label">Initial Investment</div><div class="roi-value">${roi.initial_investment || '--'}</div></div>
    <div class="roi-item"><div class="roi-label">Monthly Operating</div><div class="roi-value">${roi.monthly_operating_cost || '--'}</div></div>
    <div class="roi-item"><div class="roi-label">Expected Revenue/mo</div><div class="roi-value positive">${roi.expected_monthly_revenue || '--'}</div></div>
    <div class="roi-item"><div class="roi-label">Payback Period</div><div class="roi-value">${roi.payback_period_months ? roi.payback_period_months + ' months' : '--'}</div></div>
    <div class="roi-item"><div class="roi-label">Year 1 ROI</div><div class="roi-value positive">${roi.year1_roi_percent ? roi.year1_roi_percent + '%' : '--'}</div></div>
    <div class="roi-item"><div class="roi-label">Year 3 ROI</div><div class="roi-value positive">${roi.year3_roi_percent ? roi.year3_roi_percent + '%' : '--'}</div></div>
  `;

  // Soil amendments
  const amendments = pred.soil_amendments || [];
  document.getElementById('soilAmendments').innerHTML = amendments.map(a => `
    <div class="amendment-row ${a.priority}">
      <span class="amendment-name">${a.amendment}</span>
      <span class="amendment-qty">${a.quantity}</span>
      <span class="amendment-cost">${a.estimated_cost}</span>
      <span class="priority-badge priority-${a.priority}">${a.priority}</span>
    </div>
  `).join('');

  // Irrigation
  const irr = pred.irrigation_recommendation || {};
  document.getElementById('irrigationInfo').innerHTML = `
    <div class="irr-item"><div class="irr-label">System Type</div><div class="irr-value">${irr.system_type || '--'}</div></div>
    <div class="irr-item"><div class="irr-label">Est. Cost</div><div class="irr-value">${irr.estimated_cost || '--'}</div></div>
    <div class="irr-item"><div class="irr-label">Daily Water Need</div><div class="irr-value">${irr.water_requirement_daily || '--'}</div></div>
    <div class="irr-item"><div class="irr-label">Efficiency Rating</div><div class="irr-value">${irr.efficiency_rating || '--'}</div></div>
  `;

  // Risk factors
  const risks = pred.risk_factors || [];
  document.getElementById('riskFactors').innerHTML = risks.map(r => `
    <div class="risk-row ${r.severity}">
      <div class="risk-header">
        <span class="risk-name">${r.risk}</span>
        <span class="priority-badge priority-${r.severity}">${r.severity}</span>
      </div>
      <div class="risk-mitigation">↳ ${r.mitigation}</div>
    </div>
  `).join('');

  // Planting calendar
  const cal = pred.planting_calendar || [];
  document.getElementById('plantingCalendar').innerHTML = cal.map(m => `
    <div class="cal-month">
      <div class="cal-month-name">${m.month}</div>
      ${(m.activities || []).map(a => `<div class="cal-activity">${a}</div>`).join('')}
    </div>
  `).join('');

  // Scroll to results
  document.getElementById('predictionResults').scrollIntoView({ behavior: 'smooth' });
  showToast('✅ Farm analysis complete!', 'success');
}

async function getAIAnalysis() {
  const btn = document.getElementById('getAnalysisBtn');
  btn.disabled = true;
  btn.textContent = 'Getting analysis...';

  const landData = {
    location: document.getElementById('location').value,
    area: document.getElementById('area').value,
    soil_type: document.getElementById('soilType').value,
    climate: document.getElementById('climate').value,
    water_source: document.getElementById('waterSource').value,
    budget: document.getElementById('budget').value,
    experience: document.getElementById('experience').value,
    goals: document.getElementById('goals').value,
  };

  const narrative = document.getElementById('aiNarrative');
  narrative.textContent = '';
  narrative.classList.add('streaming');

  try {
    const res = await fetch(`${API}/api/predict-land/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(landData)
    });

    await consumeSSE(res, (text) => {
      narrative.textContent += text;
    });
  } catch (err) {
    narrative.textContent = 'Failed to get analysis: ' + err.message;
  } finally {
    narrative.classList.remove('streaming');
    btn.disabled = false;
    btn.textContent = 'Get Detailed Expert Analysis';
  }
}

// ─── Farm Monitor ─────────────────────────────────────
async function loadFarmDashboard() {
  const farmId = document.getElementById('monitorFarmSelect').value;
  if (!farmId) {
    document.getElementById('monitorNoFarm').style.display = 'block';
    document.getElementById('monitorDashboard').style.display = 'none';
    return;
  }

  state.activeFarmId = farmId;
  document.getElementById('globalFarmSelect').value = farmId;
  document.getElementById('monitorNoFarm').style.display = 'none';
  document.getElementById('monitorDashboard').style.display = 'block';

  await refreshSensorData();

  // Auto refresh every 30 seconds
  if (state.sensorRefreshInterval) clearInterval(state.sensorRefreshInterval);
  state.sensorRefreshInterval = setInterval(refreshSensorData, 30000);
}

async function refreshSensorData() {
  if (!state.activeFarmId) return;

  try {
    const res = await fetch(`${API}/api/farms/${state.activeFarmId}/sensors`);
    const data = await res.json();
    state.sensorData = data.sensor_data;
    state.historicalData = data.historical;
    updateSensorUI(data.sensor_data);
    renderTrendChart(data.historical);
  } catch (err) {
    console.error('Failed to refresh sensors:', err);
  }
}

function updateSensorUI(s) {
  const set = (id, value, unit = '') => {
    const el = document.getElementById(id);
    if (el) el.textContent = value + unit;
  };
  const setBar = (id, pct) => {
    const el = document.getElementById(id);
    if (el) el.style.width = Math.min(100, Math.max(0, pct)) + '%';
  };

  set('val-temp', s.temperature_c, '°C');
  set('val-humidity', s.humidity_percent, '%');
  set('val-soil', s.soil_moisture_percent, '%');
  set('val-ph', s.soil_ph);
  set('val-light', (s.light_lux / 1000).toFixed(1), 'k lux');
  set('val-health', s.plant_health_index, '/100');
  set('val-nitrogen', s.nitrogen_ppm, ' ppm');
  set('val-pest', s.pest_pressure_index + '/10');

  set('val-wind', s.wind_speed_ms + ' m/s');
  set('val-rain', s.rainfall_24h_mm + ' mm');
  set('val-co2', s.co2_ppm + ' ppm');
  set('val-signal', s.signal_strength);

  // NPK bars and values
  set('npk-n-val', s.nitrogen_ppm + ' ppm');
  set('npk-p-val', s.phosphorus_ppm + ' ppm');
  set('npk-k-val', s.potassium_ppm + ' ppm');

  const el = (id) => document.getElementById(id);
  if (el('npk-n')) el('npk-n').style.width = Math.min(100, s.nitrogen_ppm / 3) + '%';
  if (el('npk-p')) el('npk-p').style.width = Math.min(100, s.phosphorus_ppm / 1) + '%';
  if (el('npk-k')) el('npk-k').style.width = Math.min(100, s.potassium_ppm / 2.5) + '%';

  setBar('bar-temp', (s.temperature_c / 45) * 100);
  setBar('bar-humidity', s.humidity_percent);
  setBar('bar-soil', s.soil_moisture_percent);
  setBar('bar-ph', ((s.soil_ph - 4) / 5) * 100);
  setBar('bar-light', (s.light_lux / 100000) * 100);
  setBar('bar-health', s.plant_health_index);
  setBar('bar-nitrogen', Math.min(100, s.nitrogen_ppm / 3));
  setBar('bar-pest', s.pest_pressure_index * 10);

  // Color code pest bar
  const pestFill = document.getElementById('bar-pest');
  if (pestFill) {
    pestFill.style.background = s.pest_pressure_index >= 7 ? '#ef4444' :
                                 s.pest_pressure_index >= 4 ? '#f59e0b' : '#10b981';
  }
}

// ─── Trend Chart (vanilla canvas) ─────────────────────
let chartInstance = null;

function renderTrendChart(historical) {
  const canvas = document.getElementById('trendChart');
  if (!canvas || !historical?.length) return;

  const ctx = canvas.getContext('2d');
  canvas.width = canvas.parentElement.offsetWidth - 2;
  canvas.height = 200;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const W = canvas.width;
  const H = canvas.height;
  const pad = { top: 20, right: 20, bottom: 40, left: 50 };
  const innerW = W - pad.left - pad.right;
  const innerH = H - pad.top - pad.bottom;
  const n = historical.length;

  // Grid
  ctx.strokeStyle = '#e5e7eb';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (innerH * i / 4);
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(W - pad.right, y); ctx.stroke();
  }

  // Draw series
  const series = [
    { key: 'avg_temp', color: '#ef4444', label: 'Temp °C', max: 45 },
    { key: 'avg_humidity', color: '#3b82f6', label: 'Humidity %', max: 100 },
    { key: 'avg_soil_moisture', color: '#10b981', label: 'Soil %', max: 100 },
    { key: 'avg_health', color: '#8b5cf6', label: 'Health', max: 100 },
  ];

  series.forEach(s => {
    ctx.strokeStyle = s.color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    historical.forEach((d, i) => {
      const x = pad.left + (i / (n - 1)) * innerW;
      const y = pad.top + innerH - (d[s.key] / s.max) * innerH;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Dots
    historical.forEach((d, i) => {
      const x = pad.left + (i / (n - 1)) * innerW;
      const y = pad.top + innerH - (d[s.key] / s.max) * innerH;
      ctx.fillStyle = s.color;
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });
  });

  // X labels
  ctx.fillStyle = '#6b7280';
  ctx.font = '11px Inter, sans-serif';
  ctx.textAlign = 'center';
  historical.forEach((d, i) => {
    if (i % 2 === 0) {
      const x = pad.left + (i / (n - 1)) * innerW;
      ctx.fillText(d.date.slice(5), x, H - 10);
    }
  });

  // Legend
  ctx.textAlign = 'left';
  ctx.font = '11px Inter, sans-serif';
  series.forEach((s, i) => {
    const lx = pad.left + i * 120;
    ctx.fillStyle = s.color;
    ctx.fillRect(lx, H - 26, 12, 3);
    ctx.fillStyle = '#6b7280';
    ctx.fillText(s.label, lx + 16, H - 20);
  });
}

// ─── Farm AI Analysis ─────────────────────────────────
async function runFarmAnalysis() {
  if (!state.activeFarmId) { showToast('Select a farm first', 'error'); return; }

  const observations = document.getElementById('farmObservations').value;
  const output = document.getElementById('farmAnalysisOutput');
  output.textContent = '';

  try {
    const res = await fetch(`${API}/api/farms/${state.activeFarmId}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ farm_id: state.activeFarmId, observations })
    });
    await consumeSSE(res, (text) => { output.textContent += text; });
  } catch (err) {
    output.textContent = 'Analysis failed: ' + err.message;
  }
}

// ─── Farm Chat ────────────────────────────────────────
async function sendFarmChat() {
  if (!state.activeFarmId) { showToast('Select a farm first', 'error'); return; }

  const input = document.getElementById('farmChatInput');
  const message = input.value.trim();
  if (!message) return;
  input.value = '';

  const container = document.getElementById('farmChatMessages');
  appendMessage(container, message, 'user');

  const convId = 'farm_default';
  if (!state.farmChatHistory[convId]) state.farmChatHistory[convId] = [];

  const assistantDiv = appendStreamingMessage(container, '');

  try {
    const res = await fetch(`${API}/api/farms/${state.activeFarmId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, farm_id: state.activeFarmId, conversation_id: convId })
    });

    let fullText = '';
    await consumeSSE(res, (text) => {
      fullText += text;
      assistantDiv.querySelector('.bubble-text').textContent = fullText;
      container.scrollTop = container.scrollHeight;
    });
  } catch (err) {
    assistantDiv.querySelector('.bubble-text').textContent = 'Error: ' + err.message;
  }
}

// ─── AgriChat ─────────────────────────────────────────
async function loadAgents() {
  try {
    const res = await fetch(`${API}/api/agri-chat/agents`);
    const data = await res.json();
    state.agents = data.agents || [];
    renderAgentRoster(state.agents);
  } catch (e) {
    console.error('Failed to load agents:', e);
  }
}

function renderAgentRoster(agents) {
  const roster = document.getElementById('agentRoster');
  if (!roster) return;
  roster.innerHTML = agents.map(a => `
    <div class="agent-card" id="agent-card-${a.id}" style="border-left: 4px solid ${a.color}">
      <span class="agent-emoji">${a.emoji}</span>
      <div class="agent-info">
        <div class="agent-name">${a.name}</div>
        <div class="agent-role">${a.title}</div>
      </div>
    </div>
  `).join('');
}

function highlightActiveAgents(agentIds) {
  document.querySelectorAll('.agent-card').forEach(card => card.classList.remove('active'));
  agentIds.forEach(id => {
    const card = document.getElementById(`agent-card-${id}`);
    if (card) card.classList.add('active');
  });
}

async function sendAgriChat() {
  const input = document.getElementById('agriChatInput');
  const message = input.value.trim();
  if (!message) return;
  input.value = '';

  await sendAgriMessage(message);
}

async function sendAgriMessage(message) {
  const container = document.getElementById('agriChatMessages');
  appendMessage(container, message, 'user');

  const convId = 'agri_default';
  const assistantDiv = appendStreamingMessage(container, '', null, 'Routing to experts...');

  try {
    const res = await fetch(`${API}/api/agri-chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_id: convId })
    });

    let currentAgentId = null;
    let agentTexts = {};
    let activeAgents = [];

    for await (const event of parseSSE(res)) {
      const data = JSON.parse(event);

      if (data.type === 'agent_start') {
        currentAgentId = data.agent_id;
        activeAgents.push(data.agent_id);
        agentTexts[currentAgentId] = '';
        highlightActiveAgents(activeAgents);

        const agent = state.agents.find(a => a.id === data.agent_id);
        const agentName = agent ? `${agent.emoji} ${agent.name}` : data.agent_id;

        if (Object.keys(agentTexts).length === 1) {
          // First agent - update the placeholder bubble
          assistantDiv.querySelector('.bubble-text').innerHTML =
            `<div class="agent-label">${agentName}</div><span class="agent-response"></span>`;
        } else {
          // Additional agent - add new block
          const existing = assistantDiv.querySelector('.bubble-text');
          existing.innerHTML += `<hr style="margin:10px 0; border-color:#e5e7eb">
            <div class="agent-label">${agentName}</div>
            <span class="agent-response-${currentAgentId}"></span>`;
        }

      } else if (data.type === 'text' && data.agent_id) {
        agentTexts[data.agent_id] = (agentTexts[data.agent_id] || '') + data.text;
        const target = assistantDiv.querySelector(`.agent-response-${data.agent_id}`) ||
                       assistantDiv.querySelector('.agent-response');
        if (target) {
          target.textContent = agentTexts[data.agent_id];
          container.scrollTop = container.scrollHeight;
        }

      } else if (data.type === 'agent_end') {
        // done with this agent
      }
    }

    highlightActiveAgents([]);
  } catch (err) {
    assistantDiv.querySelector('.bubble-text').textContent = 'Error: ' + err.message;
  }
}

function clearAgriChat() {
  const container = document.getElementById('agriChatMessages');
  container.innerHTML = `
    <div class="chat-bubble assistant-bubble agri-welcome">
      <div class="bubble-avatar">🌾</div>
      <div class="bubble-text">
        <strong>Welcome to AgriChat!</strong> Our team of AI specialists is ready to help.<br><br>
        Ask about soil health, crop diseases, weather planning, market prices, irrigation systems, or anything else farming-related!
        <div class="suggestion-chips">
          <button class="chip" onclick="sendAgriMessage('My tomato leaves are turning yellow with brown spots. What disease is this?')">Tomato leaf disease</button>
          <button class="chip" onclick="sendAgriMessage('What is the best soil pH for growing rice and how do I adjust it?')">Rice soil pH</button>
          <button class="chip" onclick="sendAgriMessage('How do I set up drip irrigation for 2 hectares of vegetables?')">Drip irrigation setup</button>
          <button class="chip" onclick="sendAgriMessage('When is the best time to sell my corn harvest to maximize profit?')">Best time to sell corn</button>
        </div>
      </div>
    </div>`;
}

// ─── Product Bot ──────────────────────────────────────
async function loadCatalog() {
  try {
    const res = await fetch(`${API}/api/products/catalog`);
    const data = await res.json();
    const catLabels = {
      seeds: '🌱 Seeds', fertilizers: '🧪 Fertilizers',
      pesticides: '🛡️ Pest Control', irrigation: '💧 Irrigation',
      soil_amendments: '🌍 Soil Amendments', equipment: '🔧 Equipment'
    };
    document.getElementById('catalogSummary').innerHTML = Object.entries(data).map(([cat, info]) => `
      <div class="catalog-item">
        <span class="catalog-cat">${catLabels[cat] || cat}</span>
        <span class="catalog-count">${info.count} items</span>
      </div>
    `).join('');
  } catch (err) {
    document.getElementById('catalogSummary').innerHTML = '<div class="catalog-loading">Failed to load catalog</div>';
  }
}

async function sendProductChat() {
  const input = document.getElementById('productChatInput');
  const message = input.value.trim();
  if (!message) return;
  input.value = '';
  await sendProductMessage(message);
}

async function sendProductMessage(message) {
  const container = document.getElementById('productChatMessages');
  appendMessage(container, message, 'user');

  const convId = 'product_default';
  const assistantDiv = appendStreamingMessage(container, '');

  try {
    const payload = { message, conversation_id: convId };
    if (state.activeFarmId) payload.farm_id = state.activeFarmId;

    const res = await fetch(`${API}/api/products/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    let fullText = '';
    await consumeSSE(res, (text) => {
      fullText += text;
      assistantDiv.querySelector('.bubble-text').textContent = fullText;
      container.scrollTop = container.scrollHeight;
    });
  } catch (err) {
    assistantDiv.querySelector('.bubble-text').textContent = 'Error: ' + err.message;
  }
}

function clearProductChat() {
  const container = document.getElementById('productChatMessages');
  container.innerHTML = `
    <div class="chat-bubble assistant-bubble">
      <div class="bubble-avatar">🤖</div>
      <div class="bubble-text">
        Hi! I'm AgriBot, your smart farming product advisor. 🌾<br><br>
        I have access to our full catalog of <strong>seeds, fertilizers, pesticides, irrigation systems, soil amendments,</strong> and <strong>farm equipment</strong>.<br><br>
        Tell me what you need or describe your farming challenge, and I'll find the best products for you!
      </div>
    </div>`;
}

// ─── Chat Helpers ─────────────────────────────────────
function appendMessage(container, text, role) {
  const div = document.createElement('div');
  div.className = `chat-bubble ${role === 'user' ? 'user-bubble' : 'assistant-bubble'}`;
  div.innerHTML = `
    <div class="bubble-avatar">${role === 'user' ? '👤' : '🤖'}</div>
    <div class="bubble-text">${escapeHtml(text)}</div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function appendStreamingMessage(container, text, agentId = null, placeholder = '') {
  const div = document.createElement('div');
  div.className = 'chat-bubble assistant-bubble';
  const emoji = agentId ? (state.agents.find(a => a.id === agentId)?.emoji || '🤖') : '🤖';
  div.innerHTML = `
    <div class="bubble-avatar">${emoji}</div>
    <div class="bubble-text">${placeholder || text}</div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// ─── SSE Streaming ────────────────────────────────────
async function consumeSSE(response, onChunk) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const raw = line.slice(6).trim();
        if (raw === '[DONE]') return;
        try {
          const parsed = JSON.parse(raw);
          if (parsed.text) onChunk(parsed.text);
        } catch { /* ignore */ }
      }
    }
  }
}

async function* parseSSE(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const raw = line.slice(6).trim();
        if (raw === '[DONE]') return;
        yield raw;
      }
    }
  }
}

// ─── Toast Notifications ─────────────────────────────
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}
