// js/otp_processor.js
// This file runs in the browser to process OTPs from the bot

async function processNewMessages() {
    try {
        // Fetch unprocessed messages from the bot's API
        const response = await fetch('/api/sms/unprocessed');
        if (!response.ok) return;
        
        const messages = await response.json();
        
        for (const msg of messages) {
            // Extract OTP from message
            const otp = extractOtp(msg.text);
            const phoneLast4 = extractPhoneLast4(msg.text);
            
            if (otp && phoneLast4) {
                // Save OTP to local storage
                saveOtpToStorage(otp, phoneLast4, msg.sender, msg.timestamp);
                
                // Mark as processed
                await fetch(`/api/sms/mark_processed/${msg.id}`, { method: 'POST' });
            }
        }
    } catch (error) {
        console.log('Error processing messages:', error);
    }
}

function extractOtp(text) {
    // Look for 4-6 digit OTP codes
    const patterns = [
        r'\b\d{6}\b',
        r'\b\d{4}\b',
        r'OTP[:\s]*(\d{4,6})',
        r'code[:\s]*(\d{4,6})',
        r'verification[:\s]*(\d{4,6})',
        r'pin[:\s]*(\d{4,6})'
    ];
    
    for (const pattern of patterns) {
        const match = text.match(new RegExp(pattern, 'i'));
        if (match) {
            return match[1] || match[0];
        }
    }
    return null;
}

function extractPhoneLast4(text) {
    // Look for phone number patterns
    const patterns = [
        r'☎️ Number:\s*(\d+\*+\d+)',
        r'\+?\d{10,15}',
        r'from\s*\+?(\d+)',
        r'number[:\s]*\+?(\d+)'
    ];
    
    for (const pattern of patterns) {
        const match = text.match(new RegExp(pattern, 'i'));
        if (match) {
            let phone = match[1] || match[0];
            // Remove non-digits
            phone = phone.replace(/\D/g, '');
            if (phone.length >= 4) {
                return phone.slice(-4);
            }
        }
    }
    return null;
}

function saveOtpToStorage(otp, phoneLast4, sender, timestamp) {
    const now = new Date();
    const newOtp = {
        id: Date.now().toString(),
        otp: otp,
        phone_last4: phoneLast4,
        sender: sender,
        timestamp: timestamp || now.getTime(),
        date: now.toISOString().slice(0, 10),
        time: now.toLocaleTimeString()
    };
    
    let allOtps = JSON.parse(localStorage.getItem('mima_all_otps') || '[]');
    allOtps.push(newOtp);
    localStorage.setItem('mima_all_otps', JSON.stringify(allOtps));
    
    console.log(`✅ OTP ${otp} saved for ***${phoneLast4}`);
}

// Run every 10 seconds
setInterval(processNewMessages, 10000);

// Run immediately on page load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(processNewMessages, 2000);
});
