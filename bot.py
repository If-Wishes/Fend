import requests
from bs4 import BeautifulSoup
import hashlib
import threading
import time
import html
import json
from collections import deque

class SMSPortal:
    def __init__(self, username, password):
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.base_url = "https://mysmsportal.com"
        self.seen_hashes = set()
        self.running = True
        self.message_queue = deque()
        self.bot_name = "A.MUNTAQA NUMBER BOT"
        
    def login(self):
        """Login to the portal"""
        login_url = f"{self.base_url}/index.php?login=1"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        login_data = {'user': self.username, 'password': self.password}
        
        self.session.headers.update(headers)
        response = self.session.post(login_url, data=login_data)
        
        if "User name and password needed" not in response.text:
            return True
        else:
            return False
    
    def mask_number(self, number):
        """Mask number: show first 5, last 3, replace middle with *"""
        if not number:
            return "Unknown"
        
        number = number.strip()
        
        if len(number) <= 8:
            return number
        
        first_part = number[:5]
        last_part = number[-3:]
        masked_part = "*" * (len(number) - 8)
        
        return f"{first_part}{masked_part}{last_part}"
    
    def submit_form_and_get_table2(self, form, form_action, form_method, form_data):
        """Submit a single form and extract TABLE 2 messages"""
        try:
            if form_action:
                if form_action.startswith('/'):
                    submit_url = f"{self.base_url}{form_action}"
                elif form_action.startswith('http'):
                    submit_url = form_action
                else:
                    submit_url = f"{self.base_url}/{form_action}"
            else:
                submit_url = f"{self.base_url}/index.php?opt=shw_sum"
            
            if form_method == 'POST':
                response = self.session.post(submit_url, data=form_data, timeout=30)
            else:
                response = self.session.get(submit_url, params=form_data, timeout=30)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')
            
            if len(tables) < 2:
                return []
            
            table = tables[1]
            rows = table.find_all('tr')
            messages = []
            
            for row in rows[1:]:
                cells = row.find_all('td')
                if len(cells) >= 5:
                    date_time = cells[0].get_text(strip=True)
                    range_name = cells[1].get_text(strip=True)
                    sender = cells[2].get_text(strip=True)
                    receiver = cells[3].get_text(strip=True)
                    message_body = cells[4].get_text(strip=True)
                    
                    country = range_name.split('-')[0].strip() if '-' in range_name else "Unknown"
                    
                    message_string = f"{date_time}_{receiver}_{message_body}"
                    message_hash = hashlib.md5(message_string.encode()).hexdigest()
                    
                    messages.append({
                        'hash': message_hash,
                        'date_time': date_time,
                        'range': range_name,
                        'country': country,
                        'sender': sender,
                        'receiver': receiver,
                        'message': message_body
                    })
            
            return messages
            
        except Exception:
            return []
    
    def get_all_forms_and_submit(self, html_content):
        """Extract all forms and submit each one to get TABLE 2 messages"""
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        forms = soup.find_all('form')
        
        if not forms:
            return []
        
        all_messages = []
        
        for form in forms:
            form_action = form.get('action', '')
            form_method = form.get('method', 'POST').upper()
            
            base_form_data = {}
            for inp in form.find_all('input', type='hidden'):
                name = inp.get('name')
                value = inp.get('value', '')
                if name:
                    base_form_data[name] = value
            
            selects = form.find_all('select')
            
            if selects:
                for select in selects:
                    select_name = select.get('name')
                    if select_name:
                        options = select.find_all('option')
                        for option in options:
                            opt_value = option.get('value', '')
                            if opt_value:
                                form_data = base_form_data.copy()
                                form_data[select_name] = opt_value
                                
                                submit_btn = form.find(['button', 'input'], type='submit')
                                if submit_btn:
                                    btn_name = submit_btn.get('name')
                                    btn_value = submit_btn.get('value', 'Submit')
                                    if btn_name:
                                        form_data[btn_name] = btn_value
                                
                                messages = self.submit_form_and_get_table2(
                                    form, form_action, form_method, form_data
                                )
                                all_messages.extend(messages)
            else:
                submit_btn = form.find(['button', 'input'], type='submit')
                if submit_btn:
                    btn_name = submit_btn.get('name')
                    btn_value = submit_btn.get('value', 'Submit')
                    if btn_name:
                        base_form_data[btn_name] = btn_value
                
                messages = self.submit_form_and_get_table2(
                    form, form_action, form_method, base_form_data
                )
                all_messages.extend(messages)
        
        return all_messages
    
    def get_all_messages_from_all_forms(self):
        """Get ALL messages from ALL forms' TABLE 2"""
        summary_url = f"{self.base_url}/index.php?opt=shw_sum"
        response = self.session.get(summary_url, timeout=30)
        
        if response.status_code != 200:
            return []
        
        all_messages = []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        if len(tables) >= 2:
            table = tables[1]
            rows = table.find_all('tr')
            for row in rows[1:]:
                cells = row.find_all('td')
                if len(cells) >= 5:
                    date_time = cells[0].get_text(strip=True)
                    range_name = cells[1].get_text(strip=True)
                    sender = cells[2].get_text(strip=True)
                    receiver = cells[3].get_text(strip=True)
                    message_body = cells[4].get_text(strip=True)
                    
                    country = range_name.split('-')[0].strip() if '-' in range_name else "Unknown"
                    message_string = f"{date_time}_{receiver}_{message_body}"
                    message_hash = hashlib.md5(message_string.encode()).hexdigest()
                    
                    all_messages.append({
                        'hash': message_hash,
                        'date_time': date_time,
                        'range': range_name,
                        'country': country,
                        'sender': sender,
                        'receiver': receiver,
                        'message': message_body
                    })
        
        form_messages = self.get_all_forms_and_submit(response.text)
        all_messages.extend(form_messages)
        
        seen = set()
        unique_messages = []
        for msg in all_messages:
            if msg['hash'] not in seen:
                seen.add(msg['hash'])
                unique_messages.append(msg)
        
        unique_messages.sort(key=lambda x: x['date_time'], reverse=True)
        return unique_messages
    
    def format_telegram_message(self, message, is_old=False):
        """Format message for Telegram with brand header + quoted lines"""
        prefix = "📜 OLD MESSAGE" if is_old else "📨 New SMS Received 🏳️"
        
        country   = html.escape(message['country'])
        masked_receiver = html.escape(self.mask_number(message['receiver']))
        sender    = html.escape(message['sender'])
        date_time = html.escape(message['date_time'])
        range_    = html.escape(message['range'])
        
        country_q  = f"<blockquote>🌍 Country: 🏳️ {country}</blockquote>"
        number_q   = f"<blockquote>📱 Number: {masked_receiver}</blockquote>"
        sender_q   = f"<blockquote>📌 Sender: ❓ {sender}</blockquote>"
        datetime_q = f"<blockquote>📅 Date/Time: {date_time}</blockquote>"
        range_q    = f"<blockquote>🌐 Range: {range_}</blockquote>"
        
        message_lines = message['message'].split('\n')
        quoted_lines = '\n'.join(
            f"<blockquote>{html.escape(line)}</blockquote>"
            for line in message_lines if line.strip() != ""
        )
        
        brand = f"🏷️ <b>{self.bot_name}</b> 🏷️"
        
        formatted = f"""{brand}
━━━━━━━━━━━━━━━━━━━━━━
{prefix}
━━━━━━━━━━━━━━━━━━━━━━
{country_q}
{number_q}
{sender_q}
{datetime_q}
{range_q}
━━━━━━━━━━━━━━━━━━━━━━
💬 Message:
{quoted_lines}
━━━━━━━━━━━━━━━━━━━━━━
Panel - Mediatel"""
        
        return formatted
    
    def build_developer_keyboard(self):
        """Build inline keyboard with Developer button"""
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "Developer",
                        "url": "https://t.me/prince_ACTIVE1"
                    }
                ]
            ]
        }
        return json.dumps(keyboard)
    
    def send_to_telegram(self, bot_token, chat_id, message, reply_markup=None):
        """Send message to Telegram with HTML parsing and optional inline keyboard"""
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        if reply_markup:
            payload['reply_markup'] = reply_markup
        
        try:
            response = requests.post(url, data=payload, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def send_old_messages(self, bot_token, chat_id, count=5):
        """Send last 'count' messages from ALL forms"""
        all_messages = self.get_all_messages_from_all_forms()
        
        if not all_messages:
            return 0
        
        last_5_messages = all_messages[:count] if len(all_messages) >= count else all_messages
        
        sent_count = 0
        keyboard = self.build_developer_keyboard()
        
        for msg in last_5_messages:
            formatted_msg = self.format_telegram_message(msg, is_old=True)
            
            if self.send_to_telegram(bot_token, chat_id, formatted_msg, reply_markup=keyboard):
                sent_count += 1
                self.seen_hashes.add(msg['hash'])
            
            time.sleep(0.5)
        
        for msg in all_messages:
            self.seen_hashes.add(msg['hash'])
        
        return sent_count
    
    def monitor_all_forms_forever(self, bot_token, chat_id):
        """Monitor ALL forms continuously"""
        message_buffer = []
        keyboard = self.build_developer_keyboard()
        
        all_messages = self.get_all_messages_from_all_forms()
        for msg in all_messages:
            self.seen_hashes.add(msg['hash'])
        
        last_hash = all_messages[0]['hash'] if all_messages else None
        
        while self.running:
            try:
                fresh_messages = self.get_all_messages_from_all_forms()
                
                if fresh_messages:
                    current_hash = fresh_messages[0]['hash']
                    
                    if current_hash != last_hash:
                        for msg in fresh_messages:
                            if msg['hash'] not in self.seen_hashes:
                                self.seen_hashes.add(msg['hash'])
                                message_buffer.append(msg)
                        
                        if message_buffer:
                            message_buffer.sort(key=lambda x: x['date_time'])
                            
                            for msg in message_buffer:
                                formatted_msg = self.format_telegram_message(msg, is_old=False)
                                self.send_to_telegram(bot_token, chat_id, formatted_msg, reply_markup=keyboard)
                            
                            message_buffer.clear()
                            last_hash = current_hash
                
                time.sleep(0.5)
                
            except Exception:
                time.sleep(0.005)

def main():
    # SMS Portal credentials
    USERNAME = "5786"
    PASSWORD = "1134amabdu"
    
    # Telegram configuration
    BOT_TOKEN = "9089872288:AAH6plkYsJjhL2xwQuOF55-AT-aS_4LWYf0"
    CHAT_ID = "-1004408204768"
    
    portal = SMSPortal(USERNAME, PASSWORD)
    
    if not portal.login():
        return
    
    portal.send_old_messages(BOT_TOKEN, CHAT_ID, count=5)
    portal.monitor_all_forms_forever(BOT_TOKEN, CHAT_ID)

if __name__ == "__main__":
    main()
