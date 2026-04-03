#!/usr/bin/env python3
import re
import os
import threading
import requests
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

BOT_TOKEN = "7941038643:AAFFM8jv2RkFyyxzgdzuyqy6UiCHNZhIlWo"
SUPABASE_URL = "https://zubkwzsnpdjtndlvqfqf.supabase.co"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Ymt3enNucGRqdG5kbHZxZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDgyMjMsImV4cCI6MjA5MDcyNDIyM30.6fcSUpeuBONYGsWCG9lmOaf0lOPq9CDt2Ud9jXsvbSo"

app = Flask(__name__)

@app.route('/')
def health():
    return 'Bot Running', 200

def save_to_supabase(otp, phone_last3, country, service, time_raw):
    try:
        data = {
            'otp': otp,
            'phone_last3': phone_last3,
            'country': country,
            'service': service,
            'time_raw': time_raw,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'message_time': datetime.now().isoformat()
        }
        headers = {'apikey': API_KEY, 'Content-Type': 'application/json'}
        r = requests.post(f'{SUPABASE_URL}/rest/v1/otp_logs', headers=headers, json=data)
        print(f"   📤 Supabase response: {r.status_code}")
        return True
    except Exception as e:
        print(f"   ❌ Supabase error: {e}")
        return False

async def handle(update: Update, context):
    msg = update.message
    if not msg or not msg.text:
        return
    
    text = msg.text
    print(f"\n📨 Message received:")
    print(f"   └─ {text[:100]}...")
    
    # Extract Time
    time_match = re.search(r'⏰ Time:\s*(.+)', text)
    time_raw = time_match.group(1).strip() if time_match else None
    
    # Extract Country
    country_match = re.search(r'🌍 Country:\s*(\w+)', text)
    country = country_match.group(1) if country_match else None
    
    # Extract Service
    service_match = re.search(r'⚙️ Service:\s*(.+)', text)
    service = service_match.group(1).strip() if service_match else None
    
    # Extract Number (get last 3 digits)
    number_match = re.search(r'☎️ Number:\s*(.+)', text)
    phone_last3 = "???"
    if number_match:
        number = number_match.group(1).strip()
        clean_number = re.sub(r'[\*\s]', '', number)
        digits = re.sub(r'\D', '', clean_number)
        if len(digits) >= 3:
            phone_last3 = digits[-3:]
    
    # Extract OTP
    otp_match = re.search(r'\b\d{4,6}\b', text)
    if not otp_match:
        print("   ❌ No OTP code found")
        return
    
    otp = otp_match.group()
    print(f"   🔑 OTP: {otp}")
    print(f"   📱 Phone last3: {phone_last3}")
    print(f"   🌍 Country: {country}")
    print(f"   ⚙️ Service: {service}")
    print(f"   ⏰ Time: {time_raw}")
    
    save_to_supabase(otp, phone_last3, country, service, time_raw)
    print(f"   ✅ OTP saved successfully!")

def run_bot():
    print("🤖 Bot started!")
    print("   Waiting for messages...")
    print("=" * 50)
    
    try:
        # Create application with updated method
        bot_app = Application.builder().token(BOT_TOKEN).build()
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
        
        # Start polling with proper error handling
        print("   Starting polling...")
        bot_app.run_polling(drop_pending_updates=True, allowed_updates=['message'])
    except Exception as e:
        print(f"   ❌ Bot error: {e}")
        print("   ⚠️ Retrying in 5 seconds...")
        import time
        time.sleep(5)
        run_bot()

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Starting MIMA Panel Telegram Bot")
    print("=" * 50)
    
    # Start bot in background
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Flask server running on port {port}")
    print("=" * 50)
    
    # Use waitress or gunicorn for production, but for now use Flask
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
