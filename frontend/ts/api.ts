// ==========================================
// Evero Budget — API Client
// ==========================================

const API_BASE = '';

function getToken(): string | null {
    return localStorage.getItem('evero_token');
}

function setToken(token: string): void {
    localStorage.setItem('evero_token', token);
}

function clearToken(): void {
    localStorage.removeItem('evero_token');
    localStorage.removeItem('evero_user');
}

function setUser(user: any): void {
    localStorage.setItem('evero_user', JSON.stringify(user));
}

function getUser(): any {
    const u = localStorage.getItem('evero_user');
    return u ? JSON.parse(u) : null;
}

function isLoggedIn(): boolean {
    return !!getToken();
}

function requireAuth(): void {
    if (!isLoggedIn()) {
        window.location.href = '/login.html';
    }
}

function requireGuest(): void {
    if (isLoggedIn()) {
        window.location.href = '/dashboard.html';
    }
}

async function apiFetch(url: string, options: RequestInit = {}): Promise<any> {
    const token = getToken();
    const headers: any = {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers,
    });

    if (res.status === 401) {
        clearToken();
        window.location.href = '/login.html';
        throw new Error('Unauthorized');
    }

    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.detail || 'Something went wrong');
    }

    return data;
}

function logout(): void {
    clearToken();
    window.location.href = '/login.html';
}

function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
    }).format(amount);
}

function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
    });
}

function showToast(message: string, type: 'success' | 'error' | 'info' = 'info'): void {
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

function setTheme(theme: 'light' | 'dark'): void {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('evero_theme', theme);
}

function initTheme(): void {
    const saved = localStorage.getItem('evero_theme') as 'light' | 'dark' | null;
    setTheme(saved || 'light');
}

// Expose globally for HTML onclick handlers
(window as any).api = { apiFetch, getToken, setToken, clearToken, setUser, getUser, isLoggedIn, requireAuth, requireGuest, logout, formatCurrency, formatDate, showToast, setTheme, initTheme };
