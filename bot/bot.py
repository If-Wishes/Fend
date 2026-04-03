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
processed_count = 0

# NO send_message function - bot will never reply

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
        return response.status_code in [200, 201]
    except Exception:
        return False

def process_updates():
    global last_update_id, processed_count
    try:
        url = f"{TELEGRAM_API_URL}/getUpdates"
        params = {"offset": last_update_id + 1, "timeout": 25}
        response = requests.get(url, params=params, timeout=30)
        
        if response.ok:
            result = response.json().get('result', [])
            
            for update in result:
                last_update_id = update['update_id']
                
                if 'message' in update:
                    msg = update['message']
                    text = msg.get('text', '')
                    
                    otp_match = re.search(r'\b\d{4,6}\b', text)
                    if not otp_match:
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
                    
                    if save_to_supabase(otp, phone_last3, country, service, time_raw):
                        processed_count += 1
                        # Only print every 10th message to keep logs small
                        if processed_count % 10 == 0:
                            print(f"📊 Processed {processed_count} OTPs so far")
                        
    except Exception:
        pass  # Complete silence on errors

def poll_loop():
    while True:
        try:
            process_updates()
        except Exception:
            pass
        time.sleep(3)  # Check every 3 seconds

@app.route('/')
def health():
    return 'OK', 200

@app.route('/stats')
def stats():
    return f'Processed {processed_count} OTPs', 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    poll_thread = threading.Thread(target=poll_loop, daemon=True)
    poll_thread.start()
    
    app.run(host='0.0.0.0', port=port, debug=False)
