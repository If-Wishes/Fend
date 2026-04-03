#!/usr/bin/env python3
import re
import os
import requests
import time
import threading
from datetime import datetime
from flask import Flask

BOT_TOKEN = "7941038643:AAFFM8jv2RkFyyxzgdzuyqy6UiCHNZhIlWo"
SUPABASE_URL = "https://zubkwzsnpdjtndlvqfqf.supabase.co"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Ymt3enNucGRqdG5kbHZxZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDgyMjMsImV4cCI6MjA5MDcyNDIyM30.6fcSUpeuBONYGsWCG9lmOaf0lOPq9CDt2Ud9jXsvbSo"

app = Flask(__name__)
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
last_update_id = 0

# No send_message function needed - bot will be silent

def save_to_supabase(otp, phone_last3, country, service, time_raw):
    try:
        data = {
            'otp': str(otp),
            'phone_last3': str(phone_last3),
            'country': str(country) if country else None,
            'service': str(service) if service else None,
            'time_raw': str(time_raw) if time_raw else None,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'message_time': datetime.now().isoformat()
        }
        headers = {'apikey': API_KEY, 'Content-Type': 'application/json'}
        response = requests.post(f'{SUPABASE_URL}/rest/v1/otp_logs', headers=headers, json=data, timeout=10)
        print(f"   📤 Supabase: {response.status_code}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"   ❌ Supabase error: {e}")
        return False

def process_updates():
    global last_update_id
    try:
        url = f"{TELEGRAM_API_URL}/getUpdates"
        params = {"offset": last_update_id + 1, "timeout": 30}
        response = requests.get(url, params=params, timeout=35)
        
        if response.ok:
            result = response.json().get('result', [])
            for update in result:
                last_update_id = update['update_id']
                
                if 'message' in update:
                    msg = update['message']
                    text = msg.get('text', '')
                    
                    print(f"\n📨 Message: {text[:80]}...")
                    
                    otp_match = re.search(r'\b\d{4,6}\b', text)
                    if not otp_match:
                        print("   ❌ No OTP code found - ignoring")
                        continue
                    
                    otp = otp_match.group()
                    
                    number_match = re.search(r'☎️ Number:\s*(.+)', text)
                    phone_last3 = "???"
                    if number_match:
                        number = number_match.group(1).strip()
                        digits = re.sub(r'\D', '', number)
                        if len(digits) >= 3:
                            phone_last3 = digits[-3:]
                    
                    country_match = re.search(r'🌍 Country:\s*(\w+)', text)
                    country = country_match.group(1) if country_match else None
                    
                    service_match = re.search(r'⚙️ Service:\s*(.+)', text)
                    service = service_match.group(1).strip() if service_match else None
                    
                    time_match = re.search(r'⏰ Time:\s*(.+)', text)
                    time_raw = time_match.group(1).strip() if time_match else None
                    
                    print(f"   🔑 OTP: {otp} | 📱 Last3: {phone_last3} | 🌍 {country} | ⚙️ {service}")
                    
                    if save_to_supabase(otp, phone_last3, country, service, time_raw):
                        print(f"   ✅ Saved successfully! (silent mode - no reply sent)")
                    else:
                        print(f"   ❌ Failed to save")
                        
    except Exception as e:
        print(f"❌ Polling error: {e}")

def poll_loop():
    print("🔄 Polling loop started...")
    print("🤫 Bot is in SILENT mode - will NOT send any replies")
    while True:
        try:
            process_updates()
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(1)

@app.route('/')
def health():
    return '🤖 MIMA Bot Running (Silent Mode - No Replies)', 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    print("="*50)
    print("🚀 MIMA Panel Bot (Silent Polling Mode)")
    print("="*50)
    print("🤫 Bot will NOT send any messages to Telegram")
    print("💾 Only saves OTPs to Supabase database")
    print("="*50)
    
    poll_thread = threading.Thread(target=poll_loop, daemon=True)
    poll_thread.start()
    
    print("✅ Bot running silently! Waiting for messages...")
    print("="*50)
    
    app.run(host='0.0.0.0', port=port, debug=False)
