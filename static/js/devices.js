// devices.js — Module 6: Device Status

const DEVICE_ICONS = {
  esp32: 'fa-microchip',
  mq6_gas_sensor: 'fa-smog',
  flame_sensor: 'fa-fire',
  temperature_sensor: 'fa-temperature-half',
  pir_sensor: 'fa-person-walking',
  overflow_sensor: 'fa-droplet',
  solenoid_valve: 'fa-valve',
  buzzer: 'fa-bell',
  led_indicator: 'fa-lightbulb',
  wifi_status: 'fa-wifi',
};

const DEVICE_LABELS = {
  esp32: 'ESP32 Controller',
  mq6_gas_sensor: 'MQ-6 Gas Sensor',
  flame_sensor: 'Flame Sensor',
  temperature_sensor: 'Temperature Sensor',
  pir_sensor: 'PIR Motion Sensor',
  overflow_sensor: 'Overflow Sensor',
  solenoid_valve: 'Solenoid Valve',
  buzzer: 'Buzzer',
  led_indicator: 'LED Indicator',
  wifi_status: 'Wi-Fi Status',
};

function goodStatus(v) {
  return ['Connected', 'Working', 'Ready'].includes(v);
}

async function loadDeviceStatus() {
  try {
    const res = await fetch('/api/device-status');
    const data = await res.json();
    renderDeviceGrid(data);
    document.getElementById('deviceIdText').textContent = data.deviceId;
    document.getElementById('lastCommText').textContent = data.lastCommunication ? new Date(data.lastCommunication).toLocaleString() : '—';
    document.getElementById('currentRiskText').textContent = data.currentRiskLevel;
  } catch (e) {
    console.error(e);
  }
}

function renderDeviceGrid(data) {
  const grid = document.getElementById('deviceGrid');
  grid.innerHTML = Object.entries(data.sensors).map(([key, value]) => {
    const ok = goodStatus(value);
    return `
      <div class="col-6 col-lg-3">
        <div class="sage-card">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <div class="sage-card-icon ${ok ? 'icon-green' : 'icon-red'}"><i class="fa-solid ${DEVICE_ICONS[key] || 'fa-microchip'}"></i></div>
            <span class="dot ${ok ? 'dot-green' : 'dot-red'}"></span>
          </div>
          <div class="sage-card-title">${DEVICE_LABELS[key] || key}</div>
          <div class="fw-semibold">${value}</div>
        </div>
      </div>
    `;
  }).join('');
}

loadDeviceStatus();
setInterval(loadDeviceStatus, 5000);
