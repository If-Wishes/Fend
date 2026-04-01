#!/usr/bin/env python3
"""
MIMA Panel Telegram Bot - Saves all messages to sms.json
No processing, just saves raw messages
"""

import json
import os
import threading
from datetime import datetime
from flask import Flask, jsonify

# ============ CONFIGURATION ============
BOT_TOKEN = "7941038643:AAFFM8jv2RkFyyxzgdzuyqy6UiCHNZhIlWo"
SMS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'sms.json')

# Ensure data directory exists
os.makedirs(os.path.dirname(SMS_FILE), exist_ok=True)

# Initialize empty file if not exists
if not os.path.exists(SMS_FILE):
    with open(SMS_FILE, 'w') as f:
        json.dump([], f)

# ============ TELEGRAM BOT ============
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

def save_message(text, sender, chat_id, chat_title, timestamp):
    """Save message to sms.json"""
    try:
        # Load existing messages
        with open(SMS_FILE, 'r') as f:
            messages = json.load(f)
        
        # Add new message
        messages.append({
            'id': len(messages) + 1,
            'text': text,
            'sender': sender,
            'chat_id': str(chat_id),
            'chat_title': chat_title,
            'timestamp': timestamp,
            'date': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d'),
            'time': datetime.fromtimestamp(timestamp).strftime('%H:%M:%S'),
            'processed': False
        })
        
        # Keep last 10,000 messages
        if len(messages) > 10000:
            messages = messages[-10000:]
        
        # Save back
        with open(SMS_FILE, 'w') as f:
            json.dump(messages, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving: {e}")
        return False

async def handle_message(update: Update, context):
    """Save any message to sms.json - NO REPLIES"""
    message = update.message
    if not message or not message.text:
        return
    
    text = message.text
    sender = message.from_user.username or message.from_user.first_name or "unknown"
    chat_id = message.chat_id
    chat_title = message.chat.title or "Private Chat"
    timestamp = message.date.timestamp()
    
    # Save to file - no reply
    save_message(text, sender, chat_id, chat_title, timestamp)

# ============ FLASK SERVER ============
app = Flask(__name__)

@app.route('/')
def health():
    """Health check"""
    with open(SMS_FILE, 'r') as f:
        messages = json.load(f)
        unprocessed = len([m for m in messages if not m.get('processed', False)])
    return jsonify({'status': 'running', 'total_messages': len(messages), 'unprocessed': unprocessed})

@app.route('/sms')
def get_sms():
    """Get all unprocessed SMS"""
    with open(SMS_FILE, 'r') as f:
        messages = json.load(f)
    return jsonify(messages)

@app.route('/sms/unprocessed')
def get_unprocessed_sms():
    """Get only unprocessed messages"""
    with open(SMS_FILE, 'r') as f:
        messages = json.load(f)
    unprocessed = [m for m in messages if not m.get('processed', False)]
    return jsonify(unprocessed)

@app.route('/sms/mark_processed/<int:msg_id>', methods=['POST'])
def mark_processed(msg_id):
    """Mark a message as processed"""
    with open(SMS_FILE, 'r') as f:
        messages = json.load(f)
    
    for msg in messages:
        if msg.get('id') == msg_id:
            msg['processed'] = True
            break
    
    with open(SMS_FILE, 'w') as f:
        json.dump(messages, f, indent=2)
    
    return jsonify({'success': True})

def run_bot():
    """Run Telegram bot"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(MessageHandler(filters.ALL, handle_message))
        print("🤖 Bot started - saving messages to sms.json")
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"Bot error: {e}")

if __name__ == "__main__":
    # Start Telegram bot in background
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
