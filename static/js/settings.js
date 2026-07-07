// settings.js — Module 8: Settings

async function loadSettings() {
  const res = await fetch('/api/settings');
  const s = await res.json();

  document.getElementById('gasThreshold').value = s.gas_threshold;
  document.getElementById('temperatureThreshold').value = s.temperature_threshold;
  document.getElementById('riskThreshold').value = s.risk_threshold;
  document.getElementById('autoShutoffTimeout').value = s.auto_shutoff_timeout;

  document.getElementById('notifyTelegram').checked = s.notify_telegram === 'true';
  document.getElementById('notifyEmail').checked = s.notify_email === 'true';
  document.getElementById('notifyBrowser').checked = s.notify_browser === 'true';

  document.getElementById(s.units === 'F' ? 'unitF' : 'unitC').checked = true;
}

async function saveSettings() {
  const payload = {
    gas_threshold: document.getElementById('gasThreshold').value,
    temperature_threshold: document.getElementById('temperatureThreshold').value,
    risk_threshold: document.getElementById('riskThreshold').value,
    auto_shutoff_timeout: document.getElementById('autoShutoffTimeout').value,
    notify_telegram: document.getElementById('notifyTelegram').checked,
    notify_email: document.getElementById('notifyEmail').checked,
    notify_browser: document.getElementById('notifyBrowser').checked,
    units: document.querySelector('input[name="units"]:checked').value,
  };

  const res = await fetch('/api/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (res.ok) {
    sageToast('Settings saved successfully', 'success');
  } else {
    sageToast('Failed to save settings', 'danger');
  }
}

document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
loadSettings();
