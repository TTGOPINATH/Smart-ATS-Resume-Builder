/* ═══════════════════════════════════════════════
   Smart ATS — app.js
   Auth helpers, API calls, toast UI, nav init
   ═══════════════════════════════════════════════ */

// ── Token helpers ────────────────────────────────
const getToken  = () => localStorage.getItem('ats_token');
const getUser   = () => { try { return JSON.parse(localStorage.getItem('ats_user')); } catch { return null; } };
const setAuth   = (token, user) => { localStorage.setItem('ats_token', token); localStorage.setItem('ats_user', JSON.stringify(user)); };
const clearAuth = () => { localStorage.removeItem('ats_token'); localStorage.removeItem('ats_user'); };

function logout() {
  clearAuth();
  showToast('Logged out successfully', 'info');
  setTimeout(() => window.location.href = '/', 800);
}

// ── Navbar init ──────────────────────────────────
function initNav() {
  const user  = getUser();
  const token = getToken();
  if (user && token) {
    document.getElementById('navAuthBtns')?.classList.add('d-none');
    const menu = document.getElementById('navUserMenu');
    if (menu) {
      menu.classList.remove('d-none');
      const nameEl = document.getElementById('navUserName');
      if (nameEl) nameEl.textContent = user.username || 'Account';
      if (user.is_premium) {
        document.getElementById('navProBadge')?.classList.remove('d-none');
      }
    }
  }
}

// ── API helper ───────────────────────────────────
async function apiCall(method, url, body = null, isFormData = false) {
  const headers = {};
  const token   = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!isFormData) headers['Content-Type'] = 'application/json';

  const opts = { method, headers };
  if (body) opts.body = isFormData ? body : JSON.stringify(body);

  const res  = await fetch(url, opts);
  const data = await res.json();

  if (res.status === 401) {
    clearAuth();
    window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
    return null;
  }
  if (!res.ok) {
    const detail = data.detail;
    if (typeof detail === 'object' && detail?.message) throw new Error(detail.message);
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(data));
  }
  return data;
}

// ── Toast system ─────────────────────────────────
let _toastId = 0;
function showToast(message, type = 'info', duration = 4000) {
  const id        = `toast-${++_toastId}`;
  const icons     = { success: 'check-circle-fill', error: 'x-circle-fill', info: 'info-circle-fill', warning: 'exclamation-triangle-fill' };
  const iconCols  = { success: '#06d6a0', error: '#ef233c', info: '#3a86ff', warning: '#ffd60a' };
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const el = document.createElement('div');
  el.id        = id;
  el.className = `toast ats-toast toast-${type} show mb-2`;
  el.setAttribute('role', 'alert');
  el.innerHTML = `
    <div class="toast-header">
      <i class="bi bi-${icons[type] || 'info-circle-fill'} me-2" style="color:${iconCols[type]}"></i>
      <strong class="me-auto">${type.charAt(0).toUpperCase()+type.slice(1)}</strong>
      <button type="button" class="btn-close btn-close-white" onclick="document.getElementById('${id}')?.remove()"></button>
    </div>
    <div class="toast-body" style="color:#c8c8d8;font-size:0.9rem">${message}</div>`;
  container.appendChild(el);
  setTimeout(() => el.remove(), duration);
}

// ── Loading overlay ──────────────────────────────
function showLoading(msg = 'Processing…') {
  let ol = document.getElementById('globalOverlay');
  if (!ol) {
    ol = document.createElement('div');
    ol.id = 'globalOverlay';
    ol.className = 'loading-overlay';
    ol.innerHTML = `<div class="text-center"><div class="spinner-border spinner-accent mb-3" style="width:3rem;height:3rem"></div><p class="text-secondary">${msg}</p></div>`;
    document.body.appendChild(ol);
  }
}
function hideLoading() { document.getElementById('globalOverlay')?.remove(); }

// ── Score helpers ────────────────────────────────
function scoreColor(score) {
  if (score >= 80) return '#06d6a0';
  if (score >= 60) return '#3a86ff';
  if (score >= 40) return '#ffd60a';
  return '#ef233c';
}

function animateScoreRing(svgId, score, max = 100) {
  const circle = document.getElementById(svgId);
  if (!circle) return;
  const r          = parseFloat(circle.getAttribute('r'));
  const circumf    = 2 * Math.PI * r;
  const pct        = Math.max(0, Math.min(score, max)) / max;
  circle.style.strokeDasharray  = circumf;
  circle.style.strokeDashoffset = circumf * (1 - pct);
  circle.style.stroke = scoreColor(score);
}

function animateProgressBars() {
  document.querySelectorAll('[data-progress]').forEach(bar => {
    const v = parseFloat(bar.dataset.progress) || 0;
    setTimeout(() => {
      bar.style.width = v + '%';
      bar.style.background = scoreColor(v);
    }, 300);
  });
}

// ── Require auth guard ───────────────────────────
function requireAuth() {
  if (!getToken()) {
    window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
    return false;
  }
  return true;
}

// ── Skills tag input ─────────────────────────────
function initSkillsInput(containerId, inputId, hiddenId) {
  const container = document.getElementById(containerId);
  const input     = document.getElementById(inputId);
  const hidden    = document.getElementById(hiddenId);
  if (!container || !input) return;

  let skills = [];

  function render() {
    const old = container.querySelectorAll('.skill-tag');
    old.forEach(t => t.remove());
    skills.forEach((s, i) => {
      const tag = document.createElement('span');
      tag.className = 'skill-tag me-1 mb-1';
      tag.innerHTML = `${s} <span class="remove-skill" data-i="${i}"><i class="bi bi-x"></i></span>`;
      tag.querySelector('.remove-skill').onclick = () => { skills.splice(i, 1); render(); };
      container.insertBefore(tag, input);
    });
    if (hidden) hidden.value = JSON.stringify(skills);
  }

  function loadInitial() {
    try {
      const val = hidden?.value || '[]';
      const parsed = JSON.parse(val);
      skills = Array.isArray(parsed) ? parsed : [];
      render();
    } catch {}
  }

  input.addEventListener('keydown', e => {
    if ((e.key === 'Enter' || e.key === ',') && input.value.trim()) {
      e.preventDefault();
      const v = input.value.trim().replace(/,$/, '');
      if (v && !skills.includes(v)) { skills.push(v); render(); }
      input.value = '';
    }
    if (e.key === 'Backspace' && !input.value && skills.length) {
      skills.pop(); render();
    }
  });

  loadInitial();
  return { getSkills: () => skills, setSkills: (arr) => { skills = arr; render(); } };
}

// ── Confirm modal (reusable) ─────────────────────
function confirmAction(message, onConfirm) {
  if (confirm(message)) onConfirm();
}

// ── Init ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initNav();

  // Handle ?next= param after login
  const params = new URLSearchParams(window.location.search);
  const nextUrl = params.get('next');

  // Auto-redirect to dashboard if token + on landing/login/register
  const protectedRedirects = ['/', '/login', '/register'];
  if (getToken() && protectedRedirects.includes(window.location.pathname)) {
    // Only auto-redirect to dashboard from login/register pages
    if (window.location.pathname === '/login' || window.location.pathname === '/register') {
      window.location.href = nextUrl || '/dashboard';
    }
  }
});
