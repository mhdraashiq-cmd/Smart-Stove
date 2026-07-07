// common.js — shared UI behaviors across all SAGE pages

document.addEventListener('DOMContentLoaded', () => {
  // Dark mode
  const darkToggle = document.getElementById('darkModeToggle');
  const savedTheme = window.__sageTheme || 'light';
  if (savedTheme === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
  if (darkToggle) {
    darkToggle.addEventListener('click', () => {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      if (isDark) {
        document.documentElement.removeAttribute('data-theme');
        darkToggle.innerHTML = '<i class="fa-solid fa-moon"></i>';
        window.__sageTheme = 'light';
      } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        darkToggle.innerHTML = '<i class="fa-solid fa-sun"></i>';
        window.__sageTheme = 'dark';
      }
    });
  }

  // Mobile sidebar toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sageSidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  }

  // Ask for browser notification permission once
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
});

// ---- Shared helpers -----------------------------------------------------

function sageToast(message, variant = 'primary') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const id = 'toast-' + Date.now();
  const el = document.createElement('div');
  el.className = `toast align-items-center text-bg-${variant} border-0`;
  el.id = id;
  el.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  container.appendChild(el);
  const toast = new bootstrap.Toast(el, { delay: 5000 });
  toast.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

function updateConnectionPill(state) {
  const pill = document.getElementById('connectionPill');
  if (!pill) return;
  pill.classList.remove('offline', 'warning');
  if (state === 'online') {
    pill.innerHTML = '<i class="fa-solid fa-circle"></i> Live';
  } else if (state === 'warning') {
    pill.classList.add('warning');
    pill.innerHTML = '<i class="fa-solid fa-circle"></i> Reconnecting';
  } else {
    pill.classList.add('offline');
    pill.innerHTML = '<i class="fa-solid fa-circle"></i> Offline';
  }
}

let lastEmergencyTimestamp = null;

function maybeTriggerEmergency(data) {
  if (data.riskLevel !== 'EMERGENCY') return;
  if (lastEmergencyTimestamp === data.timestamp) return; // avoid repeat popups for same event
  lastEmergencyTimestamp = data.timestamp;

  const reasonEl = document.getElementById('emergencyModalReason');
  const timeEl = document.getElementById('emergencyModalTime');
  if (reasonEl) reasonEl.textContent = (data.reasons && data.reasons[0]) || 'Critical risk detected in kitchen';
  if (timeEl) timeEl.textContent = new Date(data.timestamp).toLocaleString();

  const modalEl = document.getElementById('emergencyModal');
  if (modalEl) {
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }

  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification('🚨 SAGE Emergency Alert', {
      body: `${(data.reasons && data.reasons[0]) || 'Critical condition'} — Gas valve auto-closed.`,
    });
  }

  sageToast('🚨 Emergency detected — gas valve closed automatically', 'danger');
}

function riskColor(level) {
  if (level === 'EMERGENCY') return '#dc2626';
  if (level === 'WARNING') return '#f59e0b';
  return '#16a34a';
}

function fmtTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString();
  } catch (e) {
    return iso;
  }
}
