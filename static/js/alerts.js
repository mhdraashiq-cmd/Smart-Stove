// alerts.js — Module 5: Alert History table + filters

async function loadAlerts() {
  const params = new URLSearchParams();
  const date = document.getElementById('filterDate').value;
  const type = document.getElementById('filterType').value;
  const severity = document.getElementById('filterSeverity').value;
  if (date) params.set('date', date);
  if (type) params.set('type', type);
  if (severity) params.set('severity', severity);

  const res = await fetch(`/api/history?${params.toString()}`);
  const rows = await res.json();
  renderAlertsTable(rows);
}

function severityBadge(sev) {
  const cls = sev === 'EMERGENCY' ? 'status-emergency' : 'status-warning';
  return `<span class="status-badge ${cls}">${sev}</span>`;
}

function renderAlertsTable(rows) {
  const body = document.getElementById('alertsTableBody');
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">No alerts match these filters.</td></tr>';
    return;
  }
  body.innerHTML = rows.map(r => `
    <tr>
      <td>${new Date(r.timestamp).toLocaleString()}</td>
      <td>${r.alert_type}</td>
      <td>${r.temperature != null ? Math.round(r.temperature) + '°C' : '—'}</td>
      <td>${r.gas != null ? Math.round(r.gas) + ' ppm' : '—'}</td>
      <td>${r.motion ? 'Detected' : 'None'}</td>
      <td>${r.flame ? 'ON' : 'OFF'}</td>
      <td>${severityBadge(r.severity)} <span class="text-muted small">${r.risk_score}</span></td>
      <td>${r.action_taken}</td>
      <td><span class="badge rounded-pill text-bg-light border">${r.status}</span></td>
    </tr>
  `).join('');
}

document.getElementById('applyFilters').addEventListener('click', loadAlerts);
document.getElementById('clearFilters').addEventListener('click', () => {
  document.getElementById('filterDate').value = '';
  document.getElementById('filterType').value = '';
  document.getElementById('filterSeverity').value = '';
  loadAlerts();
});

loadAlerts();
setInterval(loadAlerts, 10000);
