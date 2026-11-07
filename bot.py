import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from bs4 import BeautifulSoup
import hashlib
import html
import json
import re
from collections import deque
import os
from datetime import datetime

# ==========================================
# 1. THE WEB SERVER
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# ==========================================
# UNIVERSAL SAFE TELEGRAM SENDER
# ==========================================
def send_telegram_safe(bot_token, chat_id, message, raw_sms_text=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    
    if raw_sms_text:
        keyboard = []
        otp_matches = re.findall(r'\b\d{4,8}\b', str(raw_sms_text))
        if otp_matches:
            keyboard.append([{"text": f"📋 Copy OTP ({otp_matches[-1]})", "copy_text": {"text": otp_matches[-1]}}])
        keyboard.append([{"text": "➕ Add Number", "url": GROUP_LINK}])
        payload['reply_markup'] = json.dumps({"inline_keyboard": keyboard})
    
    while True:
        try:
            res = requests.post(url, data=payload, timeout=10)
            if res.status_code == 200:
                return True
            
            if res.status_code == 429:
                retry_after = res.json().get('parameters', {}).get('retry_after', 5)
                print(f"⚠️ Telegram rate limit hit. Waiting {retry_after} seconds...")
                time.sleep(retry_after + 1)
                continue
                
            return False
            
        except Exception:
            time.sleep(3)
            continue

# ==========================================
# SHARED HASH STORAGE HELPERS
# ==========================================
def load_hashes(filename, hash_set):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            for line in f:
                hash_set.add(line.strip())

def save_hash(filename, h):
    with open(filename, "a") as f:
        f.write(f"{h}\n")

# ==========================================
# 2. MEDIATEL BOT LOGIC
# ==========================================
mediatel_seen_hashes = set()

class SMSPortal:
    def __init__(self, username, password):
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.base_url = "https://mysmsportal.com"
        self.running = True
        self.bot_name = "A.MUNTAQA NUMBER BOT"
        
    def login(self):
        login_url = f"{self.base_url}/index.php?login=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        login_data = {'user': self.username, 'password': self.password}
        self.session.headers.update(headers)
        response = self.session.post(login_url, data=login_data)
        return "User name and password needed" not in response.text
    
    def mask_number(self, number):
        if not number: return "Unknown"
        number = number.strip()
        if len(number) <= 8: return number
        return f"{number[:5]}{'*' * (len(number) - 8)}{number[-3:]}"
    
    def get_all_messages(self):
        try:
            summary_url = f"{self.base_url}/index.php?opt=shw_sum"
            response = self.session.get(summary_url, timeout=30)
            if response.status_code != 200: return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')
            if len(tables) < 2: return []

            messages = []
            for row in tables[1].find_all('tr')[1:]:
                cells = row.find_all('td')
                if len(cells) >= 5:
                    date_time = cells[0].get_text(strip=True)
                    range_name = cells[1].get_text(strip=True)
                    sender = cells[2].get_text(strip=True)
                    receiver = cells[3].get_text(strip=True)
                    message_body = cells[4].get_text(strip=True)
                    
                    country = range_name.split('-')[0].strip() if '-' in range_name else "Unknown"
                    message_hash = hashlib.md5(f"{date_time}_{receiver}_{message_body}".encode()).hexdigest()
                    
                    messages.append({
                        'hash': message_hash, 'date_time': date_time, 'range': range_name,
                        'country': country, 'sender': sender, 'receiver': receiver, 'message': message_body
                    })
            
            messages.sort(key=lambda x: x['date_time'], reverse=True)
            return messages
        except Exception:
            return []
    
    def format_telegram_message(self, message, is_old=False):
        prefix = "📜 OLD MESSAGE" if is_old else "📨 New SMS Received 🏳️"
        country = html.escape(message['country'])
        masked_receiver = html.escape(self.mask_number(message['receiver']))
        sender = html.escape(message['sender'])
        date_time = html.escape(message['date_time'])
        range_ = html.escape(message['range'])
        
        message_lines = message['message'].split('\n')
        quoted_lines = '\n'.join(f"<blockquote>{html.escape(line)}</blockquote>" for line in message_lines if line.strip() != "")
        
        return f"""🏷️ <b>{self.bot_name}</b> 🏷️
━━━━━━━━━━━━━━━━━━━━━━
{prefix}
━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🌍 Country: 🏳️ {country}</blockquote>
<blockquote>📱 Number: {masked_receiver}</blockquote>
<blockquote>📌 Sender: ❓ {sender}</blockquote>
<blockquote>📅 Date/Time: {date_time}</blockquote>
<blockquote>🌐 Range: {range_}</blockquote>
━━━━━━━━━━━━━━━━━━━━━━
💬 Message:
{quoted_lines}
━━━━━━━━━━━━━━━━━━━━━━
Panel - Mediatel"""
    
    def monitor_forever(self, bot_token, chat_id):
        global mediatel_seen_hashes
        load_hashes("mediatel_sent.txt", mediatel_seen_hashes)
        
        # Mark existing messages as seen on startup to prevent spamming old ones
        initial_msgs = self.get_all_messages()
        for msg in initial_msgs:
            if msg['hash'] not in mediatel_seen_hashes:
                mediatel_seen_hashes.add(msg['hash'])
                save_hash("mediatel_sent.txt", msg['hash'])

        while self.running:
            try:
                fresh_messages = self.get_all_messages()
                for msg in reversed(fresh_messages):
                    if msg['hash'] not in mediatel_seen_hashes:
                        formatted_msg = self.format_telegram_message(msg, is_old=False)
                        
                        # Send and WAIT for confirmation before marking as seen
                        success = send_telegram_safe(bot_token, chat_id, formatted_msg, raw_sms_text=msg['message'])
                        
                        if success:
                            mediatel_seen_hashes.add(msg['hash'])
                            save_hash("mediatel_sent.txt", msg['hash'])
                            time.sleep(3) # 3 second strict delay between messages
                
                time.sleep(1)
            except Exception:
                time.sleep(5)

# ==========================================
# 3. CHOICE SMS MONITOR
# ==========================================
CHOICE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Connection": "keep-alive",
}

choice_sesskey = None
choice_last_sesskey_fetch = 0
choice_server_date = None
choice_seen_hashes = set()

def choice_solve_captcha(html_text):
    text = re.sub(r"<[^>]+>", " ", html_text)
    text = text.replace("&plus;", "+").replace("&#43;", "+")
    m = re.search(r"What\s+is\s+(\d+)\s*\+\s*(\d+)", text, re.I)
    return str(int(m.group(1)) + int(m.group(2))) if m else None

def choice_login(username, password, base_url, login_url, post_url):
    session = requests.Session()
    session.headers.update(CHOICE_HEADERS)
    try:
        r = session.get(login_url, timeout=15)
        answer = choice_solve_captcha(r.text)
        if not answer: return None
        payload = {"username": username, "password": password, "capt": answer}
        lr = session.post(post_url, data=payload, allow_redirects=True, timeout=15)
        if "dashboard" not in lr.url.lower() and "/agent/" not in lr.url.lower(): return None
        return session
    except:
        return None

def choice_get_session_info(session, report_url):
    global choice_sesskey, choice_last_sesskey_fetch, choice_server_date
    if time.time() - choice_last_sesskey_fetch < 600 and choice_sesskey:
        return choice_sesskey
    try:
        r = session.get(report_url, timeout=15)
        match = re.search(r"sesskey=([a-f0-9]+)", r.text)
        if match:
            choice_sesskey = match.group(1)
            choice_last_sesskey_fetch = time.time()
        date_match = re.search(r'value="(\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}:\d{2}"', r.text)
        if date_match:
            choice_server_date = date_match.group(1)
    except:
        pass
    return choice_sesskey

def choice_fetch_messages(session, base_url, report_url, limit=100):
    global choice_sesskey, choice_server_date
    try:
        current_sesskey = choice_get_session_info(session, report_url)
        if not current_sesskey:
            return None 

        if not choice_server_date:
            choice_server_date = datetime.now().strftime("%Y-%m-%d")

        start_date = f"{choice_server_date} 00:00:00"
        end_date = f"{choice_server_date} 23:59:59"

        url = f"{base_url}/ints/agent/res/data_smscdr.php"
        params = {
            "fdate1": start_date, "fdate2": end_date, 
            "frange": "", "fclient": "", "fnum": "", "fcli": "",
            "fgdate": "", "fgmonth": "", "fgrange": "", "fgclient": "", "fgnumber": "", "fgcli": "",
            "fg": "0", "sesskey": current_sesskey, "sEcho": "1", "iDisplayStart": "0",
            "iDisplayLength": str(limit), "iSortCol_0": "0", "sSortDir_0": "desc",
            "_": str(int(time.time() * 1000))
        }
        headers = {
            **CHOICE_HEADERS,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": report_url,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Cache-Control": "no-cache", "Pragma": "no-cache"
        }
        data_resp = session.get(url, params=params, headers=headers, timeout=10)
        if data_resp.status_code != 200: return []

        data = data_resp.json()
        rows = data.get("aaData", [])
        messages = []
        for row in rows:
            if not row or not row[0] or not re.match(r"\d{4}-\d{2}-\d{2}", str(row[0])):
                continue
            try:
                msg_time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                messages.append({
                    "number": row[2], "cli": row[3], "range": row[1], "sms": row[5], "timestamp": msg_time 
                })
            except:
                pass
        messages.sort(key=lambda x: x["timestamp"], reverse=True)
        return messages
    except:
        return []

def choice_mask_number(num):
    num = str(num).strip()
    if len(num) > 7:
        return num[:4] + "*" * (len(num) - 7) + num[-3:]
    return num

def choice_format_message(msg, is_old=False):
    t_str = msg["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    masked_num = choice_mask_number(msg["number"])
    message_lines = str(msg['sms']).split('\n')
    quoted_lines = '\n'.join(f"<blockquote>{html.escape(line)}</blockquote>" for line in message_lines if line.strip() != "")
    
    prefix = "📜 OLD MESSAGE" if is_old else "📨 New SMS Received 🏳️"
    
    return f"""🏷️ <b>CHOICE PANEL</b> 🏷️
━━━━━━━━━━━━━━━━━━━━━━
{prefix}
━━━━━━━━━━━━━━━━━━━━━━
<blockquote>📱 Number: {masked_num}</blockquote>
<blockquote>📌 Sender: ❓ {msg['cli']}</blockquote>
<blockquote>📅 Date/Time: {t_str}</blockquote>
<blockquote>🌐 Range: {msg['range']}</blockquote>
━━━━━━━━━━━━━━━━━━━━━━
💬 Message:
{quoted_lines}
━━━━━━━━━━━━━━━━━━━━━━
Panel - Choice"""

def choice_monitor(bot_token, chat_id, username, password, base_url, login_url, post_url, report_url):
    global choice_sesskey, choice_server_date, choice_seen_hashes
    time.sleep(3) 
    
    load_hashes("choice_sent.txt", choice_seen_hashes)
    
    session = None
    while not session:
        session = choice_login(username, password, base_url, login_url, post_url)
        if not session:
            time.sleep(10)

    # Mark existing messages as seen on startup
    messages = choice_fetch_messages(session, base_url, report_url, limit=100)
    if messages:
        for msg in messages:
            fingerprint = f"{msg['timestamp']}_{msg['number']}_{msg['sms']}"
            msg_hash = hashlib.md5(fingerprint.encode()).hexdigest()
            if msg_hash not in choice_seen_hashes:
                choice_seen_hashes.add(msg_hash)
                save_hash("choice_sent.txt", msg_hash)

    # Live loop
    while True:
        try:
            messages = choice_fetch_messages(session, base_url, report_url, limit=10)
            if messages is None:
                session = choice_login(username, password, base_url, login_url, post_url)
                if not session: time.sleep(10)
                continue

            if messages:
                for msg in reversed(messages):
                    fingerprint = f"{msg['timestamp']}_{msg['number']}_{msg['sms']}"
                    msg_hash = hashlib.md5(fingerprint.encode()).hexdigest()
                    
                    if msg_hash not in choice_seen_hashes:
                        formatted = choice_format_message(msg, is_old=False)
                        
                        # Send and WAIT for confirmation before marking as seen
                        success = send_telegram_safe(bot_token, chat_id, formatted, raw_sms_text=msg['sms'])
                        
                        if success:
                            choice_seen_hashes.add(msg_hash)
                            save_hash("choice_sent.txt", msg_hash)
                            time.sleep(3) # 3 second strict delay between messages
                            
            time.sleep(2) 
        except requests.exceptions.ConnectionError:
            time.sleep(5)
        except Exception:
            time.sleep(5)

# ==========================================
# 4. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    MEDIATEL_USERNAME = "5786"
    MEDIATEL_PASSWORD = "1134amabdu"
    
    CHOICE_USERNAME = "Joker5968"
    CHOICE_PASSWORD = "Joker5968"
    
    BOT_TOKEN = "9089872288:AAH6plkYsJjhL2xwQuOF55-AT-aS_4LWYf0"
    MEDIATEL_CHAT_ID = "-1004408204768"
    CHOICE_CHAT_ID = "-1004408204768" 
    
    GROUP_LINK = "https://t.me/+IZ0-S-sBDD9iOGJk"

    threading.Thread(target=run_web_server, daemon=True).start()

    mediatel_portal = SMSPortal(MEDIATEL_USERNAME, MEDIATEL_PASSWORD)
    if mediatel_portal.login():
        threading.Thread(
            target=mediatel_portal.monitor_forever,
            args=(BOT_TOKEN, MEDIATEL_CHAT_ID),
            daemon=True
        ).start()
    
    threading.Thread(
        target=choice_monitor,
        args=(
            BOT_TOKEN, CHOICE_CHAT_ID, 
            CHOICE_USERNAME, CHOICE_PASSWORD,
            "http://51.77.52.79", 
            "http://51.77.52.79/ints/", 
            "http://51.77.52.79/ints/signin", 
            "http://51.77.52.79/ints/agent/SMSCDRReports"
        ),
        daemon=True
    ).start()

    while True:
        time.sleep(60)
