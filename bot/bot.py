#!/usr/bin/env python3
import re
import json
import os
import threading
from datetime import datetime
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

BOT_TOKEN = "7941038643:AAFFM8jv2RkFyyxzgdzuyqy6UiCHNZhIlWo"
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'otp_logs.json')
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

OTP_PATTERNS = [r'\b\d{6}\b', r'\b\d{4}\b', r'OTP[:\s]*(\d{4,6})', r'code[:\s]*(\d{4,6})']
PHONE_PATTERNS = [r'\+?\d{10,15}', r'from\s*\+?(\d+)', r'sent\s*by\s*\+?(\d+)', r'number[:\s]*\+?(\d+)']

def extract_otp(text):
    if not text: return None
    for p in OTP_PATTERNS:
        m = re.search(p, text, re.IGNORECASE)
        if m: return m.group(1) if m.groups() else m.group(0)
    return None

def extract_phone_last4(text):
    if not text: return None
    for p in PHONE_PATTERNS:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            phone = m.group(1) if m.groups() else m.group(0)
            clean = re.sub(r'\D', '', phone)
            if len(clean) >= 4: return clean[-4:]
    return None

def save_otp(otp, phone, sender):
    try:
        logs = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                logs = json.load(f)
        now = datetime.now()
        logs.append({
            'otp': otp, 'phone_last4': phone, 'sender': sender,
            'timestamp': int(now.timestamp()), 'date': now.strftime('%Y-%m-%d'), 'time': now.strftime('%H:%M:%S')
        })
        if len(logs) > 5000: logs = logs[-5000:]
        with open(DATA_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
        return True
    except: return False

async def handle_message(update: Update, context):
    msg = update.message
    if not msg or not msg.text: return
    text, sender = msg.text, msg.from_user.username or msg.from_user.first_name or "unknown"
    otp = extract_otp(text)
    if not otp: return
    phone = extract_phone_last4(text)
    if not phone and msg.reply_to_message:
        phone = extract_phone_last4(msg.reply_to_message.text or '')
    if not phone: phone = "????"
    save_otp(otp, phone, sender)

app = Flask(__name__)

@app.route('/')
def health():
    count = 0
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            count = len(json.load(f))
    return jsonify({'status': 'Bot running', 'otps': count})

def run_bot():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)