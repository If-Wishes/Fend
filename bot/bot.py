#!/usr/bin/env python3
import re
import os
import threading
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import requests

BOT_TOKEN = "7941038643:AAFFM8jv2RkFyyxzgdzuyqy6UiCHNZhIlWo"
SUPABASE_URL = "https://zubkwzsnpdjtndlvqfqf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Ymt3enNucGRqdG5kbHZxZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDgyMjMsImV4cCI6MjA5MDcyNDIyM30.6fcSUpeuBONYGsWCG9lmOaf0lOPq9CDt2Ud9jXsvbSo"

TIME_PATTERN = r'⏰ Time:\s*(.+)'
COUNTRY_PATTERN = r'🌍 Country:\s*(\w+)'
SERVICE_PATTERN = r'⚙️ Service:\s*(.+)'
NUMBER_PATTERN = r'☎️ Number:\s*(.+)'
OTP_PATTERNS = [r'\b\d{6}\b', r'\b\d{4}\b', r'OTP[:\s]*(\d{4,6})', r'code[:\s]*(\d{4,6})']

def extract_otp(text):
    for p in OTP_PATTERNS:
        m = re.search(p, text, re.IGNORECASE)
        if m: return m.group(1) if m.groups() else m.group(0)
    return None

def extract_field(text, pattern):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None

def extract_last3(number_text):
    clean = re.sub(r'[^0-9]', '', number_text)
    return clean[-3:] if len(clean) >= 3 else clean

def save_to_supabase(otp, phone_last3, country, service, time_raw):
    try:
        headers = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Content-Type': 'application/json'}
        data = {'otp': otp, 'phone_last3': phone_last3, 'country': country, 'service': service, 'time_raw': time_raw, 'message_time': datetime.now().isoformat()}
        requests.post(f'{SUPABASE_URL}/rest/v1/otp_logs', headers=headers, json=data)
    except: pass

async def handle(update: Update, context):
    msg = update.message
    if not msg or not msg.text: return
    text = msg.text
    otp = extract_otp(text)
    if not otp: return
    time_raw = extract_field(text, TIME_PATTERN)
    country = extract_field(text, COUNTRY_PATTERN)
    service = extract_field(text, SERVICE_PATTERN)
    number_text = extract_field(text, NUMBER_PATTERN)
    phone_last3 = extract_last3(number_text) if number_text else "???"
    save_to_supabase(otp, phone_last3, country, service, time_raw)

app = Flask(__name__)
@app.route('/')
def health(): return 'OK', 200

def run_bot():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
