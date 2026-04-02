// Supabase Configuration
const SUPABASE_URL = 'https://zubkwzsnpdjtndlvqfqf.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Ymt3enNucGRqdG5kbHZxZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDgyMjMsImV4cCI6MjA5MDcyNDIyM30.6fcSUpeuBONYGsWCG9lmOaf0lOPq9CDt2Ud9jXsvbSo';

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

function getLast3Digits(number) {
    const clean = number.replace(/\D/g, '');
    return clean.slice(-3);
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[m] || m));
}

function getTodayStr() {
    return new Date().toISOString().slice(0, 10);
}

// User functions
async function getUsers() {
    const { data, error } = await supabase.from('users').select('*').order('created_at', { ascending: false });
    if (error) return [];
    return data;
}

async function createUser(username, email, password, role = 'user') {
    const { data, error } = await supabase.from('users').insert([{ username, email, password, role }]).select();
    if (error) { console.error(error); return null; }
    return data[0];
}

async function deleteUser(userId) {
    const { error } = await supabase.from('users').delete().eq('id', userId);
    if (error) return false;
    return true;
}

// Number functions
async function getUserNumbers(userId) {
    const { data, error } = await supabase.from('user_numbers').select('*').eq('user_id', userId);
    if (error) return [];
    return data;
}

async function getAllNumbers() {
    const { data, error } = await supabase.from('user_numbers').select('*, users(username)').order('allocated_at', { ascending: false });
    if (error) return [];
    return data;
}

async function addNumbers(userId, numbers, country) {
    const records = numbers.map(number => ({
        user_id: userId,
        number: number,
        last3: getLast3Digits(number),
        country: country
    }));
    const { data, error } = await supabase.from('user_numbers').insert(records).select();
    if (error) { console.error(error); return null; }
    return data;
}

async function deleteNumber(numberId) {
    const { error } = await supabase.from('user_numbers').delete().eq('id', numberId);
    if (error) return false;
    return true;
}

async function deleteNumbersByUserAndCountry(userId, country) {
    const { error } = await supabase.from('user_numbers').delete().eq('user_id', userId).eq('country', country);
    if (error) return false;
    return true;
}

// OTP functions
async function saveOtp(otp, phoneLast3, country, service, timeRaw, messageTime) {
    const { data, error } = await supabase.from('otp_logs').insert([{
        otp: otp,
        phone_last3: phoneLast3,
        country: country,
        service: service,
        time_raw: timeRaw,
        message_time: messageTime
    }]).select();
    if (error) { console.error('Error saving OTP:', error); return null; }
    return data[0];
}

async function getOtpsForUser(userId, startDate, endDate) {
    const userNumbers = await getUserNumbers(userId);
    const last3List = userNumbers.map(n => n.last3);
    if (last3List.length === 0) return [];
    
    let query = supabase.from('otp_logs').select('*').in('phone_last3', last3List).order('created_at', { ascending: false });
    if (startDate && endDate) {
        query = query.gte('created_at', startDate).lte('created_at', endDate + ' 23:59:59');
    }
    const { data, error } = await query;
    if (error) return [];
    return data;
}

async function getAllOtpsForDate(date) {
    const { data, error } = await supabase.from('otp_logs').select('*').gte('created_at', date).lte('created_at', date + ' 23:59:59').order('created_at', { ascending: false });
    if (error) return [];
    return data;
}
