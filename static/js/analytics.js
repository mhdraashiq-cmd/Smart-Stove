// analytics.js — Module 4: Analytics dashboard charts

let tempChart, gasChart, motionChart, riskChart, weeklyAlertsChart;

const chartColors = {
  blue: '#2563eb',
  green: '#16a34a',
  orange: '#f59e0b',
  red: '#dc2626',
};

function baseLineOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 8 } },
      y: { grid: { color: 'rgba(148,163,184,.15)' } },
    },
  };
}

async function loadAnalytics() {
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();
    renderCards(data);
    renderCharts(data);
  } catch (e) {
    console.error('Failed to load analytics', e);
  }
}

function renderCards(data) {
  document.getElementById('safetyScoreCard').textContent = `${data.safetyScore}%`;
  const t = data.alertTypeCounts || {};
  document.getElementById('emergencyCard').textContent =
    `${t.gas_leak || 0} Gas · ${t.overflow || 0} Overflow · ${t.auto_shutoff || 0} Shutoffs`;
  document.getElementById('avgTempCard').textContent = `${data.averageTemperature}°C`;
  document.getElementById('avgCookCard').textContent = `${data.estimatedDailyCookingMinutes} min`;

  document.getElementById('gasDaily').textContent = `${data.gasSavings.daily} kg`;
  document.getElementById('gasWeekly').textContent = `${data.gasSavings.weekly} kg`;
  document.getElementById('gasMonthly').textContent = `${data.gasSavings.monthly} kg`;
  document.getElementById('gasNote').textContent = data.gasSavings.note;
}

function renderCharts(data) {
  const labels = (data.series || []).map(s => fmtTime(s.timestamp));
  const temps = (data.series || []).map(s => s.temperature);
  const gasVals = (data.series || []).map(s => s.gas);
  const motionVals = (data.series || []).map(s => (s.motion ? 1 : 0));
  const riskVals = (data.series || []).map(s => s.risk_score);

  const weeklyLabels = (data.weeklyAlerts || []).map(w => w.day);
  const weeklyCounts = (data.weeklyAlerts || []).map(w => w.count);

  if (tempChart) {
    tempChart.data.labels = labels; tempChart.data.datasets[0].data = temps; tempChart.update();
  } else {
    tempChart = new Chart(document.getElementById('tempChart'), {
      type: 'line',
      data: { labels, datasets: [{ data: temps, borderColor: chartColors.orange, backgroundColor: 'rgba(245,158,11,.1)', fill: true, tension: .35, pointRadius: 0 }] },
      options: baseLineOptions(),
    });
  }

  if (gasChart) {
    gasChart.data.labels = labels; gasChart.data.datasets[0].data = gasVals; gasChart.update();
  } else {
    gasChart = new Chart(document.getElementById('gasChart'), {
      type: 'line',
      data: { labels, datasets: [{ data: gasVals, borderColor: chartColors.red, backgroundColor: 'rgba(220,38,38,.1)', fill: true, tension: .35, pointRadius: 0 }] },
      options: baseLineOptions(),
    });
  }

  if (motionChart) {
    motionChart.data.labels = labels; motionChart.data.datasets[0].data = motionVals; motionChart.update();
  } else {
    motionChart = new Chart(document.getElementById('motionChart'), {
      type: 'bar',
      data: { labels, datasets: [{ data: motionVals, backgroundColor: chartColors.blue, barPercentage: .6 }] },
      options: { ...baseLineOptions(), scales: { x: { grid: { display: false } }, y: { min: 0, max: 1, ticks: { stepSize: 1, callback: v => v ? 'Detected' : 'None' } } } },
    });
  }

  if (riskChart) {
    riskChart.data.labels = labels; riskChart.data.datasets[0].data = riskVals; riskChart.update();
  } else {
    riskChart = new Chart(document.getElementById('riskChart'), {
      type: 'line',
      data: { labels, datasets: [{ data: riskVals, borderColor: chartColors.green, backgroundColor: 'rgba(22,163,74,.1)', fill: true, tension: .35, pointRadius: 0 }] },
      options: baseLineOptions(),
    });
  }

  if (weeklyAlertsChart) {
    weeklyAlertsChart.data.labels = weeklyLabels; weeklyAlertsChart.data.datasets[0].data = weeklyCounts; weeklyAlertsChart.update();
  } else {
    weeklyAlertsChart = new Chart(document.getElementById('weeklyAlertsChart'), {
      type: 'bar',
      data: { labels: weeklyLabels, datasets: [{ data: weeklyCounts, backgroundColor: chartColors.orange, borderRadius: 6 }] },
      options: baseLineOptions(),
    });
  }
}

loadAnalytics();
setInterval(loadAnalytics, 8000);
