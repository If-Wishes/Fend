#!/usr/bin/env python3
"""
MIMA Panel Telegram Bot - Saves OTPs directly to Supabase
"""

import re
import os
import threading
import requests
from datetime import datetime
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# Suppress logs
import logging
logging.getLogger().setLevel(logging.ERROR)

# ============ CONFIGURATION ============
BOT_TOKEN = "7941038643:AAFFM8jv2RkFyyxzgdzuyqy6UiCHNZhIlWo"
SUPABASE_URL = "https://zubkwzsnpdjtndlvqfqf.supabase.co"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Ymt3enNucGRqdG5kbHZxZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDgyMjMsImV4cCI6MjA5MDcyNDIyM30.6fcSUpeuBONYGsWCG9lmOaf0lOPq9CDt2Ud9jXsvbSo"

# ============ FLASK SERVER ============
app = Flask(__name__)

@app.route('/')
def health():
    return jsonify({'status': 'running'})

# ============ OTP EXTRACTION ============
def extract_otp(text):
    patterns = [r'\b\d{6}\b', r'\b\d{4}\b', r'OTP[:\s]*(\d{4,6})', r'code[:\s]*(\d{4,6})']
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1) if m.groups() else m.group(0)
    return None

def extract_phone_last3(text):
    patterns = [r'☎️ Number:\s*(\d+\*+\d+)', r'\+?\d{10,15}', r'from\s*\+?(\d+)']
    for p in patterns:
        m = re.search(p, text)
        if m:
            phone = m.group(1) if m.groups() else m.group(0)
            clean = re.sub(r'\D', '', phone)
            if len(clean) >= 3:
                return clean[-3:]
    return None

def extract_country(text):
    m = re.search(r'🌍 Country:\s*(\w+)', text)
    return m.group(1) if m else None

def extract_service(text):
    m = re.search(r'⚙️ Service:\s*(.+)', text)
    return m.group(1).strip() if m else None

def save_to_supabase(otp, phone_last3, country, service):
    try:
        data = {
            'otp': otp,
            'phone_last3': phone_last3,
            'country': country,
            'service': service,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'message_time': datetime.now().isoformat()
        }
        headers = {'apikey': API_KEY, 'Content-Type': 'application/json'}
        r = requests.post(f'{SUPABASE_URL}/rest/v1/otp_logs', headers=headers, json=data)
        return r.status_code in [200, 201]
    except:
        return False

# ============ TELEGRAM BOT ============
async def handle_message(update: Update, context):
    message = update.message
    if not message or not message.text:
        return
    
    text = message.text
    
    # Extract OTP
    otp = extract_otp(text)
    if not otp:
        return
    
    # Extract other fields
    phone_last3 = extract_phone_last3(text)
    country = extract_country(text)
    service = extract_service(text)
    
    if not phone_last3:
        phone_last3 = "???"
    
    # Save to Supabase
    save_to_supabase(otp, phone_last3, country, service)

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    # Start bot in background
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
