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

// Add at the end of js/data.js

// ============ OTP PROCESSOR ============
async function fetchUnprocessedSms() {
    try {
        const response = await fetch('/api/sms/unprocessed');
        if (response.ok) {
            return await response.json();
        }
    } catch (e) {
        console.log('Could not fetch SMS, using local only');
    }
    return [];
}

async function processSmsMessages() {
    const messages = await fetchUnprocessedSms();
    
    for (const msg of messages) {
        const otp = extractOtpFromText(msg.text);
        const phoneLast4 = extractPhoneFromText(msg.text);
        
        if (otp && phoneLast4) {
            // Save OTP
            const newOtp = {
                id: msg.id,
                otp: otp,
                phone_last4: phoneLast4,
                sender: msg.sender,
                raw_message: msg.text,
                timestamp: msg.timestamp,
                date: msg.date,
                time: msg.time
            };
            
            let allOtps = JSON.parse(localStorage.getItem('mima_all_otps') || '[]');
            allOtps.push(newOtp);
            localStorage.setItem('mima_all_otps', JSON.stringify(allOtps));
            
            // Mark as processed
            await fetch(`/api/sms/mark_processed/${msg.id}`, { method: 'POST' });
        }
    }
}

function extractOtpFromText(text) {
    const patterns = [/\b\d{6}\b/, /\b\d{4}\b/, /OTP[:\s]*(\d{4,6})/i, /code[:\s]*(\d{4,6})/i];
    for (const p of patterns) {
        const m = text.match(p);
        if (m) return m[1] || m[0];
    }
    return null;
}

function extractPhoneFromText(text) {
    const m = text.match(/☎️ Number:\s*(\d+\*+\d+)/);
    if (m) {
        const clean = m[1].replace(/\*/g, '');
        if (clean.length >= 4) return clean.slice(-4);
    }
    const m2 = text.match(/\+?\d{10,15}/);
    if (m2) {
        const clean = m2[0].replace(/\D/g, '');
        if (clean.length >= 4) return clean.slice(-4);
    }
    return null;
}

// Auto-run processor every 10 seconds
setInterval(processSmsMessages, 10000);

// Add this to the END of your js/data.js file
// This ensures all data functions are properly defined

window.getTodayStr = function() {
    return new Date().toISOString().slice(0, 10);
};

window.escapeHtml = function(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
};
