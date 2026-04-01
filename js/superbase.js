// ============ SUPABASE CONFIGURATION ============
// Your Supabase URL and Anon Key
const SUPABASE_URL = 'https://uizrpckqnproauqllono.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVpenJwY2txbnByb2F1cWxsb25vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwNDc0NjQsImV4cCI6MjA5MDYyMzQ2NH0.qKVaCbH2NiksMuh85guJiRySQxykwSx-MkbWNuE-PdE';

// Initialize Supabase client
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ============ USER FUNCTIONS ============
async function getUsers() {
    const { data, error } = await supabase.from('users').select('*').order('created_at', { ascending: false });
    if (error) return [];
    return data;
}

async function createUser(username, email, password) {
    const { data, error } = await supabase.from('users').insert([{ username, email, password }]).select();
    if (error) { alert('Error: ' + error.message); return null; }
    return data[0];
}

async function deleteUser(userId) {
    const { error } = await supabase.from('users').delete().eq('id', userId);
    if (error) { alert('Error: ' + error.message); return false; }
    return true;
}

// ============ NUMBER ALLOCATION FUNCTIONS ============
async function getUserNumbers(userId) {
    const { data, error } = await supabase.from('user_numbers').select('*').eq('user_id', userId);
    if (error) return [];
    return data;
}

async function getAllNumbers() {
    const { data, error } = await supabase.from('user_numbers').select('*').order('allocated_at', { ascending: false });
    if (error) return [];
    return data;
}

async function addNumbers(userId, country, numbers) {
    const records = numbers.map(number => ({ user_id: userId, country: country, number: number }));
    const { data, error } = await supabase.from('user_numbers').insert(records).select();
    if (error) { alert('Error: ' + error.message); return null; }
    return data;
}

async function deleteNumber(numberId) {
    const { error } = await supabase.from('user_numbers').delete().eq('id', numberId);
    if (error) { alert('Error: ' + error.message); return false; }
    return true;
}

async function deleteNumbersByUserAndCountry(userId, country) {
    const { error } = await supabase.from('user_numbers').delete().eq('user_id', userId).eq('country', country);
    if (error) { alert('Error: ' + error.message); return false; }
    return true;
}

// ============ OTP FUNCTIONS ============
async function saveOtp(otp, phoneLast4, sender, userId) {
    const now = new Date();
    const { data, error } = await supabase.from('otp_logs').insert([{
        otp: otp,
        phone_last4: phoneLast4,
        sender: sender,
        user_id: userId,
        timestamp: now.getTime(),
        date: now.toISOString().slice(0, 10),
        time: now.toLocaleTimeString()
    }]).select();
    if (error) { console.error('Error:', error); return null; }
    return data[0];
}

async function getOtpsForUser(userId, startDate, endDate) {
    let query = supabase.from('otp_logs').select('*').eq('user_id', userId).order('timestamp', { ascending: false });
    if (startDate && endDate) {
        query = query.gte('date', startDate).lte('date', endDate);
    }
    const { data, error } = await query;
    if (error) return [];
    return data;
}

async function getAllOtpsForDate(date) {
    const { data, error } = await supabase.from('otp_logs').select('*').eq('date', date).order('timestamp', { ascending: false });
    if (error) return [];
    return data;
}

// ============ HELPER FUNCTIONS ============
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[m] || m));
}

function getTodayStr() {
    return new Date().toISOString().slice(0, 10);
}
