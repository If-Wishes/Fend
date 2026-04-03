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

def send_message(chat_id, text):
    """Send message back to chat (for testing)"""
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        requests.post(url, json=data, timeout=10)
        print(f"   📤 Reply sent")
    except Exception as e:
        print(f"   ❌ Send error: {e}")

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
            print(f"📡 Checking updates... Found {len(result)} new messages")
            
            for update in result:
                last_update_id = update['update_id']
                
                if 'message' in update:
                    msg = update['message']
                    chat_id = msg['chat']['id']
                    chat_title = msg['chat'].get('title', 'Private Chat')
                    text = msg.get('text', '')
                    
                    print(f"\n{'='*50}")
                    print(f"📨 Message from: {chat_title}")
                    print(f"   Chat ID: {chat_id}")
                    print(f"   Text: {text[:100]}...")
                    print(f"{'='*50}")
                    
                    otp_match = re.search(r'\b\d{4,6}\b', text)
                    if not otp_match:
                        print("   ❌ No OTP code found")
                        send_message(chat_id, "❌ No OTP code found in message")
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
                    
                    print(f"   🔑 Extracted OTP: {otp}")
                    print(f"   📱 Phone last3: {phone_last3}")
                    print(f"   🌍 Country: {country}")
                    print(f"   ⚙️ Service: {service}")
                    
                    if save_to_supabase(otp, phone_last3, country, service, time_raw):
                        reply = f"✅ OTP {otp} saved!\n📞 Phone: ***{phone_last3}\n💰 +$0.005"
                        send_message(chat_id, reply)
                        print(f"   ✅ Saved and replied!")
                    else:
                        send_message(chat_id, "❌ Failed to save OTP")
                        print(f"   ❌ Save failed!")
                        
    except Exception as e:
        print(f"❌ Polling error: {e}")

def poll_loop():
    print("🔄 Polling loop started...")
    print("🤖 Bot is active and listening for messages")
    print("💬 Add this bot to a Telegram group to start receiving OTPs")
    print("="*50)
    
    while True:
        try:
            process_updates()
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(2)

@app.route('/')
def health():
    return '🤖 MIMA Bot Running - Active and Listening', 200

@app.route('/test')
def test():
    """Test if bot can send message to yourself"""
    return 'Bot is alive! Check Telegram if you sent a message', 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    print("="*50)
    print("🚀 MIMA Panel Bot - WITH LOGGING")
    print("="*50)
    print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
    print(f"📡 Bot Name: @MIMABot")
    print("="*50)
    
    poll_thread = threading.Thread(target=poll_loop, daemon=True)
    poll_thread.start()
    
    print("✅ Bot running! Waiting for messages...")
    print("📊 Check Render logs for message details")
    print("="*50)
    
    app.run(host='0.0.0.0', port=port, debug=False)
