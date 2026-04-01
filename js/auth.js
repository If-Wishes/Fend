const ADMIN_SESSION_KEY = 'mima_admin_session';
const USER_SESSION_KEY = 'mima_user_session';

function getCurrentAdmin() { const s = localStorage.getItem(ADMIN_SESSION_KEY); return s ? JSON.parse(s) : null; }
function isAdminLoggedIn() { return getCurrentAdmin() !== null; }
function adminLogout() { localStorage.removeItem(ADMIN_SESSION_KEY); window.location.href = '../index.html'; }
function requireAdminAuth() { if (!isAdminLoggedIn()) { window.location.href = '../index.html'; return false; } return true; }

function getCurrentUser() { const s = localStorage.getItem(USER_SESSION_KEY); return s ? JSON.parse(s) : null; }
function isUserLoggedIn() { return getCurrentUser() !== null; }
function userLogout() { localStorage.removeItem(USER_SESSION_KEY); window.location.href = '../index.html'; }
function requireUserAuth() { if (!isUserLoggedIn()) { window.location.href = '../index.html'; return false; } return true; }