#!/usr/bin/env python3
import re
import os
import requests
from datetime import datetime
from flask import Flask, request, jsonify

# Configuration
BOT_TOKEN = "7941038643:AAFFM8jv2RkFyyxzgdzuyqy6UiCHNZhIlWo"
SUPABASE_URL = "https://zubkwzsnpdjtndlvqfqf.supabase.co"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Ymt3enNucGRqdG5kbHZxZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDgyMjMsImV4cCI6MjA5MDcyNDIyM30.6fcSUpeuBONYGsWCG9lmOaf0lOPq9CDt2Ud9jXsvbSo"

app = Flask(__name__)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram_message(chat_id, text):
    """Send message via Telegram API"""
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=data, timeout=10)
        return response.ok
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def save_to_supabase(otp, phone_last3, country, service, time_raw):
    """Save OTP data to Supabase"""
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
        headers = {
            'apikey': API_KEY,
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f'{SUPABASE_URL}/rest/v1/otp_logs',
            headers=headers,
            json=data,
            timeout=10
        )
        print(f"   📤 Supabase: {response.status_code}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"   ❌ Supabase error: {e}")
        return False

@app.route('/', methods=['GET'])
def health():
    return '🤖 MIMA Bot is running!', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram updates"""
    try:
        update = request.get_json()
        
        if 'message' in update:
            msg = update['message']
            chat_id = msg['chat']['id']
            text = msg.get('text', '')
            
            print(f"\n📨 Message from {chat_id}: {text[:100]}...")
            
            # Extract OTP (4-6 digit code)
            otp_match = re.search(r'\b\d{4,6}\b', text)
            if not otp_match:
                send_telegram_message(chat_id, "❌ No OTP code found in message")
                return jsonify({"status": "ok"}), 200
            
            otp = otp_match.group()
            
            # Extract phone last 3 digits
            number_match = re.search(r'☎️ Number:\s*(.+)', text)
            phone_last3 = "???"
            if number_match:
                number = number_match.group(1).strip()
                # Remove asterisks, spaces, keep only digits
                digits = re.sub(r'\D', '', number)
                if len(digits) >= 3:
                    phone_last3 = digits[-3:]
            
            # Extract country
            country_match = re.search(r'🌍 Country:\s*(\w+)', text)
            country = country_match.group(1) if country_match else None
            
            # Extract service
            service_match = re.search(r'⚙️ Service:\s*(.+)', text)
            service = service_match.group(1).strip() if service_match else None
            
            # Extract time
            time_match = re.search(r'⏰ Time:\s*(.+)', text)
            time_raw = time_match.group(1).strip() if time_match else None
            
            print(f"   🔑 OTP: {otp}")
            print(f"   📱 Phone last3: {phone_last3}")
            print(f"   🌍 Country: {country}")
            print(f"   ⚙️ Service: {service}")
            print(f"   ⏰ Time: {time_raw}")
            
            # Save to Supabase
            if save_to_supabase(otp, phone_last3, country, service, time_raw):
                reply = f"✅ OTP {otp} saved successfully!\n📞 Phone: ***{phone_last3}\n💰 +$0.005"
                send_telegram_message(chat_id, reply)
                print(f"   ✅ Saved successfully!")
            else:
                send_telegram_message(chat_id, "❌ Failed to save OTP. Please try again.")
                print(f"   ❌ Save failed!")
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print("="*50)
    print("🚀 MIMA Panel Telegram Bot")
    print("="*50)
    print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
    print(f"🗄️ Supabase: {SUPABASE_URL}")
    print(f"🌐 Server running on port {port}")
    print("="*50)
    print("✅ Bot is ready! Waiting for messages...")
    print("="*50)
    
    app.run(host='0.0.0.0', port=port, debug=False)
