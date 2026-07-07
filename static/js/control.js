// control.js — Module 7: Manual Control

const COMMAND_LABELS = {
  gas_on: 'Turn Gas ON',
  gas_off: 'Turn Gas OFF',
  restart_esp32: 'Restart ESP32',
  alarm_off: 'Alarm OFF',
  emergency_shutdown: 'Emergency Shutdown',
  test_alarm: 'Test Alarm',
};

const logEntries = [];
let pendingCommand = null;

async function sendCommand(command) {
  try {
    const res = await fetch('/api/manual-control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Command failed');

    logEntries.unshift(`${new Date(data.timestamp).toLocaleTimeString()} — ${COMMAND_LABELS[command]} sent successfully`);
    renderLog();
    sageToast(`${COMMAND_LABELS[command]} sent to ESP32`, 'success');
  } catch (e) {
    sageToast(`Failed to send command: ${e.message}`, 'danger');
  }
}

function renderLog() {
  const el = document.getElementById('commandLog');
  el.innerHTML = logEntries.slice(0, 8).map(l => `<div>${l}</div>`).join('');
}

document.querySelectorAll('.control-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const command = btn.dataset.command;
    const needsConfirm = btn.dataset.confirm === 'true';

    if (needsConfirm) {
      pendingCommand = command;
      document.getElementById('confirmModalText').textContent = btn.dataset.confirmText || 'Are you sure?';
      const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('confirmModal'));
      modal.show();
    } else {
      sendCommand(command);
    }
  });
});

document.getElementById('confirmModalYes').addEventListener('click', () => {
  const modalEl = document.getElementById('confirmModal');
  bootstrap.Modal.getInstance(modalEl).hide();
  if (pendingCommand) sendCommand(pendingCommand);
  pendingCommand = null;
});
