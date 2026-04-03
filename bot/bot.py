#!/usr/bin/env python3
import re
import os
import threading
import requests
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

import logging
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "7941038643:AAFFM8jv2RkFyyxzgdzuyqy6UiCHNZhIlWo"
SUPABASE_URL = "https://zubkwzsnpdjtndlvqfqf.supabase.co"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Ymt3enNucGRqdG5kbHZxZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDgyMjMsImV4cCI6MjA5MDcyNDIyM30.6fcSUpeuBONYGsWCG9lmOaf0lOPq9CDt2Ud9jXsvbSo"

app = Flask(__name__)

@app.route('/')
def health():
    return 'OK', 200

def save_to_supabase(otp, phone_last3):
    try:
        data = {
            'otp': otp,
            'phone_last3': phone_last3,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'message_time': datetime.now().isoformat()
        }
        headers = {'apikey': API_KEY, 'Content-Type': 'application/json'}
        r = requests.post(f'{SUPABASE_URL}/rest/v1/otp_logs', headers=headers, json=data)
        print(f"✅ Saved to Supabase: {r.status_code}")
        return True
    except Exception as e:
        print(f"❌ Supabase error: {e}")
        return False

async def handle(update, context):
    msg = update.message
    if not msg or not msg.text:
        return
    
    text = msg.text
    print(f"📨 Received: {text[:100]}")
    
    # Extract OTP
    otp_match = re.search(r'\b\d{4,6}\b', text)
    if not otp_match:
        print("No OTP found")
        return
    
    otp = otp_match.group()
    print(f"🔑 Found OTP: {otp}")
    
    # Extract phone last 3 digits
    phone_match = re.search(r'(\d{3})(?=\D|$)', text)
    phone_last3 = phone_match.group(1) if phone_match else "???"
    print(f"📱 Phone last3: {phone_last3}")
    
    # Save to Supabase
    save_to_supabase(otp, phone_last3)

def run_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("🤖 Bot started...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
