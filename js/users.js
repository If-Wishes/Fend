// ============ USER DATABASE ============
// ADD NEW USERS HERE - Just paste new users below!

const USERS_DATABASE = [
    { id: 'u1', username: 'bigx', password: '112233', email: 'emily@example.com', createdAt: getTodayStr() },
    { id: 'u2', username: 'marcus_v', password: 'password123', email: 'marcus@example.com', createdAt: getTodayStr() },
    { id: 'u3', username: 'sophia_laurent', password: 'password123', email: 'sophia@example.com', createdAt: getTodayStr() },
    { id: 'u4', username: 'james_m', password: 'password123', email: 'james@example.com', createdAt: getTodayStr() },
    
    // 👇👇👇 PASTE NEW USERS BELOW THIS LINE 👇👇👇
    // Example: { id: 'u5', username: 'Mike', password: 'Mike123', email: 'mike@example.com', createdAt: getTodayStr() },
    
];

// Helper function (don't remove)
function getTodayStr() {
    return new Date().toISOString().slice(0, 10);
}
