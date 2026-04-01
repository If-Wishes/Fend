let globalUsers = [];
let globalRequests = [];
let globalUserCredentials = [];

function getUsers() { return globalUsers; }
function getUserCredentials() { return globalUserCredentials; }
function getTodayStr() { return new Date().toISOString().slice(0,10); }

function initData() {
    const storedUsers = localStorage.getItem('mima_users');
    if (storedUsers) {
        globalUsers = JSON.parse(storedUsers);
        globalRequests = JSON.parse(localStorage.getItem('mima_requests') || '[]');
        globalUserCredentials = JSON.parse(localStorage.getItem('mima_credentials') || '[]');
    } else {
        globalUsers = [
            { id: 'u1', username: 'emily_chen', email: 'emily@example.com', password: 'password123', createdAt: getTodayStr() },
            { id: 'u2', username: 'marcus_v', email: 'marcus@example.com', password: 'password123', createdAt: getTodayStr() },
            { id: 'u3', username: 'sophia_laurent', email: 'sophia@example.com', password: 'password123', createdAt: getTodayStr() },
            { id: 'u4', username: 'james_m', email: 'james@example.com', password: 'password123', createdAt: getTodayStr() }
        ];
        globalRequests = [];
        globalUserCredentials = globalUsers;
        saveToLocal();
    }
}

function saveToLocal() {
    localStorage.setItem('mima_users', JSON.stringify(globalUsers));
    localStorage.setItem('mima_requests', JSON.stringify(globalRequests));
    localStorage.setItem('mima_credentials', JSON.stringify(globalUserCredentials));
}

function createUser(username, password, email = null) {
    const newId = crypto.randomUUID();
    const today = getTodayStr();
    const userEmail = email || `${username}@mimapanel.com`;
    const newUser = { id: newId, username, email: userEmail, password, createdAt: today };
    globalUsers.push(newUser);
    globalUserCredentials.push(newUser);
    saveToLocal();
    return newUser;
}

function updateUser(id, username, email) {
    const user = globalUsers.find(u => u.id === id);
    if (user) { user.username = username; user.email = email; saveToLocal(); }
}

function deleteUserById(id) {
    globalUsers = globalUsers.filter(u => u.id !== id);
    globalRequests = globalRequests.filter(r => r.userId !== id);
    saveToLocal();
}

function escapeHtml(str) { if(!str) return ''; return str.replace(/[&<>]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[m] || m)); }

// ============ OTP FUNCTIONS ============
async function loadOtps() {
    try {
        const response = await fetch('/data/otp_logs.json');
        if (response.ok) {
            const otps = await response.json();
            localStorage.setItem('mima_all_otps', JSON.stringify(otps));
            return otps;
        }
    } catch(e) { console.log('Using local storage'); }
    const stored = localStorage.getItem('mima_all_otps');
    return stored ? JSON.parse(stored) : [];
}

function getOtpsForUser(userId) {
    const allOtps = JSON.parse(localStorage.getItem('mima_all_otps') || '[]');
    const userNumbers = JSON.parse(localStorage.getItem('mima_analytics_numbers') || '[]');
    const userEntries = userNumbers.filter(n => n.userId === userId);
    const last4s = [];
    userEntries.forEach(entry => {
        if (entry.numbers) {
            entry.numbers.forEach(num => {
                const clean = num.replace(/\D/g, '');
                if (clean.length >= 4) last4s.push(clean.slice(-4));
            });
        }
    });
    return allOtps.filter(otp => last4s.includes(otp.phone_last4));
}

// Get earnings for a user on a specific date
function getUserEarningsForDate(userId, date) {
    const userOtps = getOtpsForUser(userId);
    const dayOtps = userOtps.filter(otp => otp.date === date);
    return dayOtps.length * 0.005;
}

// Get all user earnings for a date range
function getAllUsersEarningsForDate(date) {
    const allOtps = JSON.parse(localStorage.getItem('mima_all_otps') || '[]');
    const dayOtps = allOtps.filter(otp => otp.date === date);
    return dayOtps.length * 0.005;
}