// ==========================================
// Evero Budget — API Client (Compiled JS)
// ==========================================

const API_BASE = '';

function getToken() { return localStorage.getItem('evero_token'); }
function setToken(token) { localStorage.setItem('evero_token', token); }
function clearToken() { localStorage.removeItem('evero_token'); localStorage.removeItem('evero_user'); }
function setUser(user) { localStorage.setItem('evero_user', JSON.stringify(user)); }
function getUser() { const u = localStorage.getItem('evero_user'); return u ? JSON.parse(u) : null; }
function isLoggedIn() { return !!getToken(); }
function requireAuth() { if (!isLoggedIn()) window.location.href = '/login.html'; }
function requireGuest() { if (isLoggedIn()) window.location.href = '/dashboard.html'; }

async function apiFetch(url, options = {}) {
    const token = getToken();
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}${url}`, { ...options, headers });
    if (res.status === 401) { clearToken(); window.location.href = '/login.html'; throw new Error('Unauthorized'); }
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Something went wrong');
    return data;
}

function logout() { clearToken(); window.location.href = '/login.html'; }

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(amount);
}

function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function initTheme() {
    const saved = localStorage.getItem('evero_theme');
    document.documentElement.setAttribute('data-theme', saved || 'light');
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('evero_theme', next);
}

initTheme();
