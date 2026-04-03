#!/usr/bin/env python3
import re, os, requests, time, threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "7941038643:AAFFM8jv2RkFyyxzgdzuyqy6UiCHNZhIlWo"
SUPABASE_URL = "https://zubkwzsnpdjtndlvqfqf.supabase.co"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Ymt3enNucGRqdG5kbHZxZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDgyMjMsImV4cCI6MjA5MDcyNDIyM30.6fcSUpeuBONYGsWCG9lmOaf0lOPq9CDt2Ud9jXsvbSo"

last_id = 0

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, *args): pass

def poll():
    global last_id
    while True:
        try:
            r = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_id+1}&timeout=25', timeout=30)
            for u in r.json().get('result', []):
                last_id = u['update_id']
                t = u.get('message',{}).get('text','')
                otp = re.search(r'\b\d{4,6}\b', t)
                if otp:
                    num = re.search(r'☎️ Number:\s*(.+)', t)
                    phone = (re.sub(r'\D', '', num.group(1))[-3:]) if num else '???'
                    c = re.search(r'🌍 Country:\s*(\w+)', t)
                    s = re.search(r'⚙️ Service:\s*(.+)', t)
                    tm = re.search(r'⏰ Time:\s*(.+)', t)
                    try:
                        requests.post(f'{SUPABASE_URL}/rest/v1/otp_logs',
                            headers={'apikey': API_KEY, 'Content-Type': 'application/json'},
                            json={'otp':otp.group(), 'phone_last3':phone,
                                  'country':c.group(1) if c else None,
                                  'service':s.group(1).strip() if s else None,
                                  'time_raw':tm.group(1).strip() if tm else None,
                                  'date':datetime.now().strftime('%Y-%m-%d'),
                                  'message_time':datetime.now().isoformat()}, timeout=5)
                    except: pass
        except: pass
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=poll, daemon=True).start()
    HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 5000))), Handler).serve_forever()
