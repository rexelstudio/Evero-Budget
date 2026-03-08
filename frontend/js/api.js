/* ================================================
   Evero Budget — API Client + Utilities
   ================================================ */

const API_BASE = '';

// ---- Token Management ----
function getToken() { return localStorage.getItem('evero_token'); }
function setToken(t) { localStorage.setItem('evero_token', t); }
function clearToken() { localStorage.removeItem('evero_token'); localStorage.removeItem('evero_user'); }
function getUser() { try { return JSON.parse(localStorage.getItem('evero_user')); } catch { return null; } }
function setUser(u) { localStorage.setItem('evero_user', JSON.stringify(u)); }

function requireAuth() {
    if (!getToken()) window.location.href = '/login.html';
}

function logout() {
    clearToken();
    window.location.href = '/login.html';
}

// ---- API Fetch ----
async function apiFetch(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    const token = getToken();
    if (token) headers['Authorization'] = 'Bearer ' + token;

    const res = await fetch(API_BASE + path, { ...opts, headers });
    if (res.status === 401) { clearToken(); window.location.href = '/login.html'; return; }

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
}

// ---- Formatters ----
function formatCurrency(n) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n || 0);
}

function formatDate(d) {
    if (!d) return '';
    return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateShort(d) {
    if (!d) return '';
    return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatPercent(n) {
    return Math.round(n || 0) + '%';
}

function relativeTime(d) {
    if (!d) return '';
    const diff = Date.now() - new Date(d).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return mins + 'm ago';
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return hrs + 'h ago';
    const days = Math.floor(hrs / 24);
    if (days < 7) return days + 'd ago';
    return formatDateShort(d);
}

// ---- Category Colors ----
const CATEGORY_COLORS = {
    'Food & Dining 🍽️': { badge: 'badge-orange', icon: '🍽️', color: 'var(--orange)' },
    'Groceries 🛒': { badge: 'badge-emerald', icon: '🛒', color: 'var(--emerald)' },
    'Transportation 🚗': { badge: 'badge-blue', icon: '🚗', color: 'var(--blue)' },
    'Gas ⛽️': { badge: 'badge-amber', icon: '⛽️', color: 'var(--amber)' },
    'Shopping 🛍️': { badge: 'badge-violet', icon: '🛍️', color: 'var(--violet)' },
    'Entertainment 🎬': { badge: 'badge-cyan', icon: '🎬', color: 'var(--cyan)' },
    'Bills & Utilities 📄': { badge: 'badge-amber', icon: '📄', color: 'var(--amber)' },
    'Health 💊': { badge: 'badge-emerald', icon: '💊', color: 'var(--emerald)' },
    'Housing 🏠': { badge: 'badge-blue', icon: '🏠', color: 'var(--blue)' },
    'Personal Care ✨': { badge: 'badge-rose', icon: '✨', color: 'var(--rose)' },
    'Education 🎓': { badge: 'badge-violet', icon: '🎓', color: 'var(--violet)' },
    'Travel ✈️': { badge: 'badge-cyan', icon: '✈️', color: 'var(--cyan)' },
    'Pets 🐾': { badge: 'badge-orange', icon: '🐾', color: 'var(--orange)' },
    'Gifts & Donations 🎁': { badge: 'badge-rose', icon: '🎁', color: 'var(--rose)' },
    'Investments 📈': { badge: 'badge-emerald', icon: '📈', color: 'var(--emerald)' },
    'Insurance 🛡️': { badge: 'badge-blue', icon: '🛡️', color: 'var(--blue)' },
    'Income 💰': { badge: 'badge-emerald', icon: '💰', color: 'var(--emerald)' },
    'Other 📦': { badge: 'badge-secondary', icon: '📦', color: 'var(--muted-foreground)' },
};

function getCategoryMeta(cat) {
    return CATEGORY_COLORS[cat] || CATEGORY_COLORS['Other'];
}

// ---- Toast (Sonner-style) ----
let toastContainer = null;

function showToast(message, type = 'info') {
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };
    const t = document.createElement('div');
    t.className = 'toast ' + type;
    t.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span><span>${message}</span>`;
    toastContainer.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateY(8px)'; setTimeout(() => t.remove(), 300); }, 3500);
}

// ---- Theme ----
function initTheme() {
    const saved = localStorage.getItem('evero_theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
}

function toggleTheme() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('evero_theme', isDark ? 'light' : 'dark');
}

function isDarkMode() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
}

initTheme();

// ---- Sidebar loader ----
function loadSidebar(user) {
    if (!user) return;
    const els = {
        name: document.getElementById('sidebarName'),
        email: document.getElementById('sidebarEmail'),
        avatar: document.getElementById('sidebarAvatar'),
        upgradeBanner: document.getElementById('upgradeBanner')
    };
    if (els.name) els.name.textContent = user.name || 'User';
    if (els.email) els.email.textContent = user.email;
    if (els.avatar) {
        if (user.image && user.image !== "") {
            els.avatar.innerHTML = `<img src="${user.image}" style="width:100%;height:100%;border-radius:inherit;object-fit:cover;">`;
        } else {
            els.avatar.textContent = (user.name || 'U')[0].toUpperCase();
        }
    }

    // Show upgrade banner for free users
    if (els.upgradeBanner) {
        if (!user.is_premium) {
            els.upgradeBanner.classList.remove('hidden');
        } else {
            els.upgradeBanner.classList.add('hidden');
        }
    }
}

// ---- Lucide Icon helper ----
function icon(name, size = 18) {
    return `<i data-lucide="${name}" style="width:${size}px;height:${size}px;"></i>`;
}

function renderIcons() {
    if (window.lucide) window.lucide.createIcons();
}
