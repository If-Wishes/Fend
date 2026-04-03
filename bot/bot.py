#!/usr/bin/env python3
import re
import os
import threading
import requests
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# Suppress all logging
import logging
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('telegram').setLevel(logging.ERROR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

BOT_TOKEN = "7941038643:AAFFM8jv2RkFyyxzgdzuyqy6UiCHNZhIlWo"
SUPABASE_URL = "https://zubkwzsnpdjtndlvqfqf.supabase.co"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Ymt3enNucGRqdG5kbHZxZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDgyMjMsImV4cCI6MjA5MDcyNDIyM30.6fcSUpeuBONYGsWCG9lmOaf0lOPq9CDt2Ud9jXsvbSo"

app = Flask(__name__)

@app.route('/')
def health():
    return 'Bot Running', 200

def save_otp(otp, phone_last3):
    try:
        data = {
            'otp': otp,
            'phone_last3': phone_last3,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'message_time': datetime.now().isoformat()
        }
        headers = {'apikey': API_KEY, 'Content-Type': 'application/json'}
        requests.post(f'{SUPABASE_URL}/rest/v1/otp_logs', headers=headers, json=data)
    except:
        pass

async def handle(update, context):
    msg = update.message
    if not msg or not msg.text:
        return
    
    text = msg.text
    otp_match = re.search(r'\b\d{4,6}\b', text)
    if otp_match:
        otp = otp_match.group()
        phone_match = re.search(r'(\d{3})(?=\D|$)', text)
        phone_last3 = phone_match.group(1) if phone_match else "???"
        save_otp(otp, phone_last3)

def run_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
