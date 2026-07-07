// dashboard.js — live polling for the SAGE dashboard (Module 1)

const GAUGE_CIRCUMFERENCE = 2 * Math.PI * 52;

async function refreshDashboard() {
  try {
    const res = await fetch('/api/dashboard');
    if (!res.ok) throw new Error('bad response');
    const data = await res.json();
    renderDashboard(data);
    updateConnectionPill(data.deviceStatus === 'online' ? 'online' : 'offline');
  } catch (e) {
    updateConnectionPill('offline');
  }
}

function renderDashboard(data) {
  // Kitchen status badge
  const badge = document.getElementById('kitchenStatusBadge');
  const statusText = document.getElementById('kitchenStatusText');
  badge.textContent = data.riskLevel;
  badge.className = 'status-badge ' + (
    data.riskLevel === 'EMERGENCY' ? 'status-emergency' :
    data.riskLevel === 'WARNING' ? 'status-warning' : 'status-safe'
  );
  statusText.textContent = data.riskLevel === 'SAFE' ? 'All Clear' : data.riskLevel === 'WARNING' ? 'Needs Attention' : 'Take Action Now';

  // Temperature
  document.getElementById('tempValue').textContent = `${Math.round(data.temperature)}°C`;
  document.getElementById('tempValue').classList.remove('skeleton');

  // Gas level
  const gasLabel = data.gas >= 400 ? 'Critical' : data.gas >= 200 ? 'Warning' : 'Normal';
  const gasEl = document.getElementById('gasValue');
  gasEl.innerHTML = `${gasLabel} <span class="text-muted small">(${Math.round(data.gas)} ppm)</span>`;
  gasEl.classList.remove('skeleton');

  // Flame
  const flameEl = document.getElementById('flameValue');
  flameEl.textContent = data.flame ? 'ON' : 'OFF';
  flameEl.classList.remove('skeleton');
  flameEl.style.color = data.flame ? 'var(--sage-orange)' : 'inherit';

  // Motion
  const motionEl = document.getElementById('motionValue');
  motionEl.textContent = data.motion ? 'Detected' : 'Not Detected';
  motionEl.classList.remove('skeleton');

  // Valve
  const valveEl = document.getElementById('valveValue');
  valveEl.textContent = data.gasValve;
  valveEl.classList.remove('skeleton');
  valveEl.style.color = data.gasValve === 'OPEN' ? 'var(--sage-green)' : 'var(--sage-red)';

  // Risk score
  document.getElementById('riskScoreValue').textContent = data.riskScore;
  const bar = document.getElementById('riskProgressBar');
  bar.style.width = `${data.riskScore}%`;
  bar.style.background = riskColor(data.riskLevel);

  // Last updated
  document.getElementById('lastUpdatedValue').textContent = fmtTime(data.timestamp);

  // Safety gauge
  const safety = data.safetyScore;
  const offset = GAUGE_CIRCUMFERENCE * (1 - safety / 100);
  const gaugeFg = document.getElementById('gaugeFg');
  gaugeFg.style.strokeDasharray = GAUGE_CIRCUMFERENCE;
  gaugeFg.style.strokeDashoffset = offset;
  gaugeFg.style.stroke = riskColor(data.riskLevel);
  document.getElementById('safetyScoreNum').textContent = `${safety}%`;

  // Reasons & actions
  const reasonsList = document.getElementById('reasonsList');
  reasonsList.innerHTML = (data.reasons || []).map(r =>
    `<div class="mb-1"><i class="fa-solid fa-circle-info text-primary me-2"></i>${r}</div>`
  ).join('');

  const actionsList = document.getElementById('actionsList');
  actionsList.innerHTML = (data.recommendedActions || []).map(a =>
    `<span class="badge rounded-pill text-bg-light border" style="font-weight:600; padding:8px 14px;">${a}</span>`
  ).join('');

  // Emergency banner
  const banner = document.getElementById('emergencyBanner');
  if (data.riskLevel === 'EMERGENCY') {
    banner.classList.remove('d-none');
    document.getElementById('bannerReason').textContent = (data.reasons && data.reasons[0]) || 'Critical condition detected.';
  } else {
    banner.classList.add('d-none');
  }

  maybeTriggerEmergency(data);
}

refreshDashboard();
setInterval(refreshDashboard, 3000);
