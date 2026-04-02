// ============ SUPABASE CONFIGURATION ============
const SUPABASE_URL = 'https://zubkwzsnpdjtndlvqfqf.supabase.co';
const API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Ymt3enNucGRqdG5kbHZxZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDgyMjMsImV4cCI6MjA5MDcyNDIyM30.6fcSUpeuBONYGsWCG9lmOaf0lOPq9CDt2Ud9jXsvbSo';

// ============ HELPER FUNCTIONS ============
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[m] || m));
}

function getTodayStr() {
    return new Date().toISOString().slice(0, 10);
}

function getLast3Digits(number) {
    return number.replace(/\D/g, '').slice(-3);
}

function getCountryFlag(country) {
    const flags = {
        'Jordan': '🇯🇴', 'Tajikistan': '🇹🇯', 'Nigeria': '🇳🇬',
        'Myanmar': '🇲🇲', 'Hungary': '🇭🇺', 'Slovenia': '🇸🇮',
        'Venezuela': '🇻🇪', 'Uzbekistan': '🇺🇿'
    };
    return flags[country] || '🌍';
}

// ============ AUTHENTICATION (Session only in localStorage) ============
async function adminLogin(username, password) {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/users?select=id,username,role&username=eq.${username}&password=eq.${password}&role=eq.admin`, {
        headers: { 'apikey': API_KEY }
    });
    const data = await res.json();
    if (data && data.length > 0) {
        localStorage.setItem('mima_session', JSON.stringify({
            userId: data[0].id,
            username: data[0].username,
            role: 'admin'
        }));
        return { success: true };
    }
    return { success: false };
}

async function userLogin(username, password) {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/users?select=id,username,role&username=eq.${username}&password=eq.${password}&role=eq.user`, {
        headers: { 'apikey': API_KEY }
    });
    const data = await res.json();
    if (data && data.length > 0) {
        localStorage.setItem('mima_session', JSON.stringify({
            userId: data[0].id,
            username: data[0].username,
            role: 'user'
        }));
        return { success: true };
    }
    return { success: false };
}

function logout() {
    localStorage.removeItem('mima_session');
    window.location.href = '../index.html';
}

function getSession() {
    return JSON.parse(localStorage.getItem('mima_session') || 'null');
}

function checkAdminAuth() {
    const session = getSession();
    if (!session || session.role !== 'admin') {
        window.location.href = '../index.html';
        return false;
    }
    if (document.getElementById('adminName')) {
        document.getElementById('adminName').innerText = session.username;
    }
    return true;
}

function checkUserAuth() {
    const session = getSession();
    if (!session || session.role !== 'user') {
        window.location.href = '../index.html';
        return null;
    }
    return session;
}

// ============ USER MANAGEMENT ============
async function getUsers() {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/users?select=*&order=created_at.desc`, {
        headers: { 'apikey': API_KEY }
    });
    return await res.json();
}

async function createUser(username, email, password, role) {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/users`, {
        method: 'POST',
        headers: { 'apikey': API_KEY, 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, role })
    });
    return res.ok;
}

async function deleteUser(userId) {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/users?id=eq.${userId}`, {
        method: 'DELETE',
        headers: { 'apikey': API_KEY }
    });
    return res.ok;
}

async function renderUsersList() {
    const users = await getUsers();
    const tbody = document.getElementById('usersList');
    if (!tbody) return;
    
    tbody.innerHTML = users.map(u => `
        <tr class="border-b">
            <td class="px-6 py-3">${escapeHtml(u.username)}Js
            <td class="px-6 py-3">${escapeHtml(u.email)}Js
            <td class="px-6 py-3"><span class="px-2 py-1 rounded-full text-xs ${u.role === 'admin' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}">${u.role}</span>Js
            <td class="px-6 py-3 text-xs">${u.created_at?.slice(0,10) || '—'}Js
            <td class="text-center"><button onclick="deleteUserById('${u.id}')" class="text-red-500"><i class="fas fa-trash"></i></button>Js
        </tr>
    `).join('');
}

window.deleteUserById = async (id) => {
    if (confirm('Delete this user?')) {
        await deleteUser(id);
        renderUsersList();
    }
};

// ============ NUMBER ALLOCATION ============
async function getAllNumbers() {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/user_numbers?select=*,users(username)&order=allocated_at.desc`, {
        headers: { 'apikey': API_KEY }
    });
    return await res.json();
}

async function addNumbers(userId, numbers, country) {
    for (const num of numbers) {
        await fetch(`${SUPABASE_URL}/rest/v1/user_numbers`, {
            method: 'POST',
            headers: { 'apikey': API_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                number: num,
                last3: getLast3Digits(num),
                country: country
            })
        });
    }
    return true;
}

async function deleteNumber(numberId) {
    await fetch(`${SUPABASE_URL}/rest/v1/user_numbers?id=eq.${numberId}`, {
        method: 'DELETE',
        headers: { 'apikey': API_KEY }
    });
}

async function deleteNumbersByUserAndCountry(userId, country) {
    await fetch(`${SUPABASE_URL}/rest/v1/user_numbers?user_id=eq.${userId}&country=eq.${country}`, {
        method: 'DELETE',
        headers: { 'apikey': API_KEY }
    });
}

async function renderAllocations() {
    const filter = document.getElementById('filterSelect')?.value;
    let url = `${SUPABASE_URL}/rest/v1/user_numbers?select=*,users(username)&order=allocated_at.desc`;
    if (filter) {
        url = `${SUPABASE_URL}/rest/v1/user_numbers?select=*,users(username)&user_id=eq.${filter}&order=allocated_at.desc`;
    }
    const res = await fetch(url, { headers: { 'apikey': API_KEY } });
    const nums = await res.json();
    const container = document.getElementById('allocations');
    if (!container) return;
    
    if (nums.length === 0) {
        container.innerHTML = '<div class="text-center py-8 text-gray-400">No numbers allocated</div>';
        return;
    }
    
    const grouped = {};
    for (const n of nums) {
        const key = n.user_id + '_' + n.country;
        if (!grouped[key]) {
            grouped[key] = {
                userId: n.user_id,
                userName: n.users?.username || 'Unknown',
                country: n.country,
                numbers: []
            };
        }
        grouped[key].numbers.push(n);
    }
    
    let html = '';
    for (const key in grouped) {
        const g = grouped[key];
        html += `
            <div class="border rounded-xl mb-3">
                <div class="bg-gray-50 px-4 py-2 flex justify-between">
                    <span><strong>${escapeHtml(g.userName)}</strong> - ${escapeHtml(g.country)}</span>
                    <button onclick="deleteCountryNumbers('${g.userId}','${g.country}')" class="text-red-500 text-sm">Delete All</button>
                </div>
                <div class="flex flex-wrap gap-2 p-3">
                    ${g.numbers.map(num => `
                        <span class="bg-gray-100 px-3 py-1 rounded-full text-sm flex items-center gap-1">
                            <span class="font-mono">${escapeHtml(num.number)}</span>
                            <button onclick="deleteSingleNumber('${num.id}')" class="text-red-400 hover:text-red-600">&times;</button>
                        </span>
                    `).join('')}
                </div>
            </div>
        `;
    }
    container.innerHTML = html;
}

window.deleteCountryNumbers = async (userId, country) => {
    if (confirm('Delete all numbers for this country?')) {
        await deleteNumbersByUserAndCountry(userId, country);
        renderAllocations();
    }
};

window.deleteSingleNumber = async (id) => {
    if (confirm('Delete this number?')) {
        await deleteNumber(id);
        renderAllocations();
    }
};

// ============ OTP & ACTIVITIES ============
async function getOtpsForDate(date) {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/otp_logs?select=*&date=eq.${date}`, {
        headers: { 'apikey': API_KEY }
    });
    return await res.json();
}

async function getUserNumbers(userId) {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/user_numbers?select=*&user_id=eq.${userId}`, {
        headers: { 'apikey': API_KEY }
    });
    return await res.json();
}

async function getUserOtps(userId, startDate, endDate) {
    const userNumbersList = await getUserNumbers(userId);
    const last3List = userNumbersList.map(n => n.last3);
    if (last3List.length === 0) return [];
    
    let url = `${SUPABASE_URL}/rest/v1/otp_logs?select=*&phone_last3=in.(${last3List.join(',')})&order=message_time.desc`;
    if (startDate && endDate) {
        url = `${SUPABASE_URL}/rest/v1/otp_logs?select=*&phone_last3=in.(${last3List.join(',')})&date=gte.${startDate}&date=lte.${endDate}&order=message_time.desc`;
    }
    const res = await fetch(url, { headers: { 'apikey': API_KEY } });
    return await res.json();
}

async function renderActivities() {
    const filterDate = document.getElementById('filterDate')?.value || getTodayStr();
    
    const usersRes = await fetch(`${SUPABASE_URL}/rest/v1/users?select=id,username,email`, { headers: { 'apikey': API_KEY } });
    const users = await usersRes.json();
    
    const numbersRes = await fetch(`${SUPABASE_URL}/rest/v1/user_numbers?select=*`, { headers: { 'apikey': API_KEY } });
    const numbers = await numbersRes.json();
    
    const otpsRes = await fetch(`${SUPABASE_URL}/rest/v1/otp_logs?select=*&date=eq.${filterDate}`, { headers: { 'apikey': API_KEY } });
    const otps = await otpsRes.json();
    
    let totalOtps = 0, totalEarnings = 0, activeCount = 0;
    const rows = [];
    
    for (const user of users) {
        const userNumbers = numbers.filter(n => n.user_id === user.id);
        const userLast3 = userNumbers.map(n => n.last3);
        const userOtps = otps.filter(o => userLast3.includes(o.phone_last3));
        const otpCount = userOtps.length;
        const earnings = otpCount * 0.005;
        const lastOtp = userOtps.sort((a,b) => new Date(b.message_time) - new Date(a.message_time))[0];
        
        totalOtps += otpCount;
        totalEarnings += earnings;
        if (otpCount > 0) activeCount++;
        
        rows.push(`
            <tr class="border-b">
                <td class="px-6 py-3 font-medium">${escapeHtml(user.username)}Js
                <td class="px-6 py-3">${escapeHtml(user.email)}Js
                <td class="px-6 py-3 text-center">${userNumbers.length}Js
                <td class="px-6 py-3 text-center font-bold text-emerald-600">${otpCount}Js
                <td class="px-6 py-3 text-center">$${earnings.toFixed(2)}Js
                <td class="px-6 py-3 text-center text-xs">${lastOtp ? new Date(lastOtp.message_time).toLocaleTimeString() : '—'}Js
            </tr>
        `);
    }
    
    if (document.getElementById('totalOtps')) {
        document.getElementById('totalOtps').textContent = totalOtps;
        document.getElementById('totalEarnings').textContent = `$${totalEarnings.toFixed(2)}`;
        document.getElementById('activeUsers').textContent = activeCount;
        document.getElementById('avgPerUser').textContent = `$${(activeCount > 0 ? (totalEarnings / activeCount).toFixed(2) : '0.00')}`;
        document.getElementById('activitiesTable').innerHTML = rows.join('');
    }
}

// ============ USER DASHBOARD ============
async function loadUserNumbers(userId) {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/user_numbers?select=*&user_id=eq.${userId}`, {
        headers: { 'apikey': API_KEY }
    });
    const numbers = await res.json();
    const countries = [...new Set(numbers.map(n => n.country))];
    const sel = document.getElementById('countrySelect');
    if (sel) {
        sel.innerHTML = '<option value="">-- Select Country --</option>' +
            countries.map(c => `<option value="${c}">${getCountryFlag(c)} ${c}</option>`).join('');
    }
    return numbers;
}

function displayUserNumbers(country, numbers) {
    const data = numbers.filter(n => n.country === country);
    const div = document.getElementById('numbersDisplay');
    if (!div) return;
    
    if (data.length === 0) {
        div.innerHTML = '<div class="text-center py-8 text-gray-400">No numbers for this country</div>';
        return;
    }
    
    div.innerHTML = `
        <div class="border rounded-xl">
            <div class="bg-gray-50 px-4 py-2">${getCountryFlag(country)} ${country}</div>
            <div class="divide-y">
                ${data.map(n => `<div class="px-4 py-2 font-mono">${escapeHtml(n.number)}</div>`).join('')}
            </div>
        </div>
    `;
}

async function renderUserTodayOtps(userId) {
    const today = getTodayStr();
    const userNumbersList = await getUserNumbers(userId);
    const last3List = userNumbersList.map(n => n.last3);
    if (last3List.length === 0) {
        const tbody = document.getElementById('todayOtpTable');
        if (tbody) tbody.innerHTML = '';
        return;
    }
    
    const res = await fetch(`${SUPABASE_URL}/rest/v1/otp_logs?select=*&phone_last3=in.(${last3List.join(',')})&date=eq.${today}&order=message_time.desc`, {
        headers: { 'apikey': API_KEY }
    });
    const otps = await res.json();
    const tbody = document.getElementById('todayOtpTable');
    const emptyMsg = document.getElementById('todayEmptyMsg');
    
    if (!tbody) return;
    
    if (otps.length === 0) {
        tbody.innerHTML = '';
        if (emptyMsg) emptyMsg.classList.remove('hidden');
        return;
    }
    if (emptyMsg) emptyMsg.classList.add('hidden');
    
    tbody.innerHTML = otps.map(o => `
        <tr class="border-b">
            <td class="px-6 py-3 font-mono">***${escapeHtml(o.phone_last3)}Js
            <td class="px-6 py-3 font-bold text-emerald-600">${escapeHtml(o.otp)}Js
            <td class="px-6 py-3 text-gray-500">${new Date(o.message_time).toLocaleTimeString()}Js
        </tr>
    `).join('');
}

async function renderUserTotalStats(userId) {
    const today = getTodayStr();
    const userNumbersList = await getUserNumbers(userId);
    const last3List = userNumbersList.map(n => n.last3);
    if (last3List.length === 0) {
        document.getElementById('totalOtpCount').textContent = '0';
        document.getElementById('totalEarnings').textContent = '$0.00';
        return;
    }
    
    const res = await fetch(`${SUPABASE_URL}/rest/v1/otp_logs?select=count&phone_last3=in.(${last3List.join(',')})&date=eq.${today}`, {
        headers: { 'apikey': API_KEY }
    });
    const data = await res.json();
    const count = data[0]?.count || 0;
    document.getElementById('totalOtpCount').textContent = count;
    document.getElementById('totalEarnings').textContent = `$${(count * 0.005).toFixed(2)}`;
}

async function renderUserPastOtps(userId) {
    const start = document.getElementById('startDate')?.value;
    const end = document.getElementById('endDate')?.value;
    if (!start || !end) return;
    
    const userNumbersList = await getUserNumbers(userId);
    const last3List = userNumbersList.map(n => n.last3);
    if (last3List.length === 0) {
        const tbody = document.getElementById('pastOtpTable');
        if (tbody) tbody.innerHTML = '';
        return;
    }
    
    const res = await fetch(`${SUPABASE_URL}/rest/v1/otp_logs?select=*&phone_last3=in.(${last3List.join(',')})&date=gte.${start}&date=lte.${end}&order=message_time.desc`, {
        headers: { 'apikey': API_KEY }
    });
    const otps = await res.json();
    const tbody = document.getElementById('pastOtpTable');
    const emptyMsg = document.getElementById('pastEmptyMsg');
    const earningsSpan = document.getElementById('pastTotalEarnings');
    
    if (!tbody) return;
    
    if (otps.length === 0) {
        tbody.innerHTML = '';
        if (emptyMsg) emptyMsg.classList.remove('hidden');
        if (earningsSpan) earningsSpan.textContent = '$0.00';
        return;
    }
    if (emptyMsg) emptyMsg.classList.add('hidden');
    if (earningsSpan) earningsSpan.textContent = `$${(otps.length * 0.005).toFixed(2)}`;
    
    tbody.innerHTML = otps.map(o => `
        <tr class="border-b">
            <td class="px-6 py-3 text-xs">${o.date}Js
            <td class="px-6 py-3 font-bold text-emerald-600">${escapeHtml(o.otp)}Js
            <td class="px-6 py-3 text-gray-500">${new Date(o.message_time).toLocaleTimeString()}Js
        </tr>
    `).join('');
}

async function loadUserProfile(userId) {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/users?select=username,email,created_at&id=eq.${userId}`, {
        headers: { 'apikey': API_KEY }
    });
    const user = await res.json();
    if (user && user[0]) {
        document.getElementById('profileUsername').innerText = user[0].username;
        document.getElementById('profileEmail').innerText = user[0].email;
        document.getElementById('profileCreated').innerText = user[0].created_at?.slice(0,10) || getTodayStr();
    }
}

// ============ DASHBOARD STATS ============
async function loadDashboardStats() {
    const usersRes = await fetch(`${SUPABASE_URL}/rest/v1/users?select=id`, { headers: { 'apikey': API_KEY } });
    const users = await usersRes.json();
    if (document.getElementById('statUsers')) {
        document.getElementById('statUsers').textContent = users.length;
    }
    
    const numbersRes = await fetch(`${SUPABASE_URL}/rest/v1/user_numbers?select=id`, { headers: { 'apikey': API_KEY } });
    const numbers = await numbersRes.json();
    if (document.getElementById('statNumbers')) {
        document.getElementById('statNumbers').textContent = numbers.length;
    }
    
    const today = getTodayStr();
    const otpsRes = await fetch(`${SUPABASE_URL}/rest/v1/otp_logs?select=id&date=eq.${today}`, { headers: { 'apikey': API_KEY } });
    const otps = await otpsRes.json();
    if (document.getElementById('statOtps')) {
        document.getElementById('statOtps').textContent = otps.length;
        document.getElementById('statEarnings').textContent = `$${(otps.length * 0.005).toFixed(2)}`;
    }
}
