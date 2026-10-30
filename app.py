import os
import time
import threading
import re
import json
from datetime import datetime, timedelta

from flask import Flask
import requests
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION
# ==========================================
BOT_TOKEN = "9136746567:AAEwSv5_eycbVM-sRm2n3-L-Gn1TDf8f_Xg"  # Replace with your real token
BASE_URL = "https://mysmsportal.com"
ALLOCATE_QTY = 50         # 50 numbers
RATE_LIMIT_HOURS = 2      # 2 hours limit

ADMIN_USERNAME = "5786"
ADMIN_PASSWORD = "1134amabdu"

api_url = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ==========================================
# IN-MEMORY STORAGE (Resets on restart)
# ==========================================
login_states = {}         # {chat_id: "waiting_username"}
user_limits = {}          # {user_id: {range_name: timestamp}}
user_profiles = {}        # {user_id: "username"} - Memory only

# ==========================================
# FLASK WEB SERVER (For Render)
# ==========================================
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running", 200

# ==========================================
# TELEGRAM API HELPERS
# ==========================================
def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    payload = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
        
    if parse_mode: payload['parse_mode'] = parse_mode
    try:
        requests.post(f"{api_url}/sendMessage", data=payload, timeout=10)
    except:
        pass

def answer_callback(callback_id, text):
    try:
        requests.post(f"{api_url}/answerCallbackQuery", data={'callback_query_id': callback_id, 'text': text}, timeout=10)
    except:
        pass

def delete_message(chat_id, message_id):
    payload = {'chat_id': chat_id, 'message_id': message_id}
    try:
        requests.post(f"{api_url}/deleteMessage", data=payload, timeout=10)
    except:
        pass

# ==========================================
# PORTAL LOGIC
# ==========================================
def get_admin_session():
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded'})
    session.post(f"{BASE_URL}/index.php?login=1", data={'user': ADMIN_USERNAME, 'password': ADMIN_PASSWORD}, timeout=15)
    return session

def verify_client_username(username):
    session = get_admin_session()
    try:
        res = session.get(f"{BASE_URL}/index.php?opt=shw_mge", timeout=15)
        if "User name and password needed" in res.text:
            return False, "❌ Admin session failed."

        soup = BeautifulSoup(res.text, 'html.parser')
        page_text = soup.get_text(separator=' ', strip=True)
        
        match = re.search(r'PASSWORD UPDATE (.*?) Add new client', page_text)
        if match:
            data_block = match.group(1)
            pattern = r'(5786\d{3})\s+([A-Za-z0-9\s\.\-\_]+?)\s+([A-Za-z0-9@\.\!\#\$\%\^\&\*\(\)\-\_]+)'
            matches = re.findall(pattern, data_block)
            
            for m in matches:
                db_name = m[1].strip()
                if db_name.lower() == username.lower():
                    return True, db_name
                    
            return False, "❌ Username not found."
    except Exception as e:
        return False, f"❌ Network Error: {e}"
    return False, "❌ Unknown error."

def get_live_ranges(client_name):
    session = get_admin_session()
    allocate_url = f"{BASE_URL}/index.php?opt=shw_all_v2"
    res = session.get(allocate_url, timeout=15)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    target_select = None
    target_form = None
    for select in soup.find_all('select'):
        options = select.find_all('option')
        if options and "select client" in options[0].get_text().lower():
            target_select = select
            target_form = select.find_parent('form')
            break
            
    if not target_select: return []

    selected_val = None
    for opt in target_select.find_all('option'):
        if opt.get_text(strip=True).lower() == client_name.lower():
            selected_val = opt.get('value', '')
            break
            
    if not selected_val: return []

    form_data = {inp.get('name'): inp.get('value', '') for inp in target_form.find_all('input') if inp.get('name')}
    form_data[target_select.get('name')] = selected_val
    submit_btn = target_form.find(['button', 'input'], type='submit')
    if submit_btn: form_data[submit_btn.get('name')] = submit_btn.get('value', 'Select')
    
    res_ranges = session.post(allocate_url, data=form_data, timeout=15)
    soup_ranges = BeautifulSoup(res_ranges.text, 'html.parser')
    
    target_table = next((t for t in soup_ranges.find_all('table') if "HOW MANY" in t.get_text().upper()), None)
    if not target_table: return []

    ranges = []
    for tr in target_table.find_all('tr'):
        cells = tr.find_all(['td', 'th'])
        if len(cells) >= 6 and "HOW MANY" not in tr.get_text().upper():
            ranges.append({'name': cells[0].get_text(strip=True)})
    return ranges

def perform_allocation(client_name, range_name):
    session = get_admin_session()
    allocate_url = f"{BASE_URL}/index.php?opt=shw_all_v2"
    res = session.get(allocate_url, timeout=15)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    target_select = None
    target_form = None
    for select in soup.find_all('select'):
        if "select client" in select.find_all('option')[0].get_text().lower():
            target_select = select
            target_form = select.find_parent('form')
            break

    selected_val = next((opt.get('value') for opt in target_select.find_all('option') if opt.get_text(strip=True).lower() == client_name.lower()), None)
    if not selected_val: return False, "Client not found"

    form_data = {inp.get('name'): inp.get('value', '') for inp in target_form.find_all('input') if inp.get('name')}
    form_data[target_select.get('name')] = selected_val
    submit_btn = target_form.find(['button', 'input'], type='submit')
    if submit_btn: form_data[submit_btn.get('name')] = submit_btn.get('value', 'Select')
    
    res_ranges = session.post(allocate_url, data=form_data, timeout=15)
    soup_ranges = BeautifulSoup(res_ranges.text, 'html.parser')
    
    target_table = next((t for t in soup_ranges.find_all('table') if "HOW MANY" in t.get_text().upper()), None)
    if not target_table: return False, "Ranges table not found"

    selected_range = None
    for tr in target_table.find_all('tr'):
        cells = tr.find_all(['td', 'th'])
        if len(cells) >= 6 and "HOW MANY" not in tr.get_text().upper():
            if cells[0].get_text(strip=True) == range_name:
                selected_range = {'allocated': cells[3].get_text(strip=True), 'form': tr.find('form')}
                break

    if not selected_range: return False, "Range not found"

    payload = {inp.get('name'): inp.get('value', '') for inp in selected_range['form'].find_all('input', type='hidden') if inp.get('name')}
    payload['quantity'] = str(ALLOCATE_QTY)
    action = selected_range['form'].get('action', '')
    post_url = f"{BASE_URL}/{action}" if action else allocate_url

    final_res = session.post(post_url, data=payload, timeout=15)
    final_soup = BeautifulSoup(final_res.text, 'html.parser')
    
    updated_table = next((t for t in final_soup.find_all('table') if "HOW MANY" in t.get_text().upper()), None)
    if updated_table:
        for tr in updated_table.find_all('tr'):
            cells = tr.find_all(['td', 'th'])
            if len(cells) >= 6 and "HOW MANY" not in tr.get_text().upper():
                if cells[0].get_text(strip=True) == range_name:
                    if int(cells[3].get_text(strip=True)) > int(selected_range['allocated']):
                        return True, f"✅ Success! Allocated {ALLOCATE_QTY} numbers."
    return False, "❌ Failed! The count did not increase."

# ==========================================
# BOT HANDLERS
# ==========================================
def handle_message(msg):
    chat_id = msg['chat']['id']
    chat_type = msg['chat']['type']
    text = msg.get('text', '')
    user_id = str(msg['from']['id'])
    
    bot_info = requests.get(f'{api_url}/getMe').json()
    bot_username = bot_info['result']['username']

    # 1. GROUP CHAT: Trigger private prompt
    if chat_type in ['group', 'supergroup']:
        if text.startswith('/add_numbers'):
            # THE FIX: Remove the command part and strip spaces
            username_input = text.replace('/add_numbers', '').strip()
            
            # If they didn't provide a username after the command, ask for it
            if not username_input:
                send_message(chat_id, "⚠️ Please provide a username.\nUsage: `/add_numbers YourUsername`", parse_mode="Markdown")
                return
                
            private_link = f"https://t.me/{bot_username}?start=add_{username_input}"
            markup = {
                "inline_keyboard": [
                    [{"text": "🔒 Verify Username Privately", "url": private_link}]
                ]
            }
            send_message(
                chat_id, 
                f"⚠️ {msg['from']['first_name']}, click the button below to verify your username privately.", 
                reply_markup=markup
            )
            return

    # 2. PRIVATE CHAT: Enter username or via Deep Link
    if chat_type == 'private':
        if text.startswith('/start'):
            # Check if the user came from the group with a username (e.g. /start add_AMUNTAQA ash)
            if text.startswith('/start add_'):
                # Extract the username from the deep link
                username_input = text.replace('/start add_', '').strip()
                send_message(chat_id, "⏳ Verifying username...")
                
                is_valid, result = verify_client_username(username_input)
                if is_valid:
                    client_name = result 
                    user_profiles[user_id] = client_name 
                    
                    send_message(chat_id, f"✅ Username verified!")
                    
                    ranges = get_live_ranges(client_name)
                    if not ranges:
                        send_message(chat_id, "❌ No ranges available or error fetching data.")
                        return
                        
                    keyboard = []
                    current_row = []
                    for i, r in enumerate(ranges):
                        btn_text = f"{i+1}️⃣ {r['name']}"
                        callback_data = f"alloc|{r['name']}"
                        current_row.append({"text": btn_text, "callback_data": callback_data})
                        if len(current_row) == 2:
                            keyboard.append(current_row)
                            current_row = []
                    if current_row:
                        keyboard.append(current_row)
                    
                    markup = {"inline_keyboard": keyboard}
                    text_table = f"🏷️ **Available Ranges**\n━━━━━━━━━━━━━━━━━━━━━━\nClick a range below to allocate {ALLOCATE_QTY} numbers:"
                    send_message(chat_id, text_table, reply_markup=markup, parse_mode="Markdown")
                else:
                    send_message(chat_id, f"{result}\n\nPlease type /start to try again.", parse_mode="Markdown")
                return
                
            else:
                # Normal start
                login_states[chat_id] = "waiting_username"
                send_message(chat_id, "👋 Welcome! Please enter your **Username** to fetch your available ranges:", parse_mode="Markdown")
                return

        if chat_id in login_states and login_states[chat_id] == "waiting_username":
            username_input = text.strip()
            send_message(chat_id, "⏳ Verifying username...")
            
            is_valid, result = verify_client_username(username_input)
            if is_valid:
                client_name = result 
                user_profiles[user_id] = client_name 
                
                send_message(chat_id, f"✅ Username verified!")
                
                ranges = get_live_ranges(client_name)
                if not ranges:
                    send_message(chat_id, "❌ No ranges available or error fetching data.")
                    return
                    
                keyboard = []
                current_row = []
                for i, r in enumerate(ranges):
                    btn_text = f"{i+1}️⃣ {r['name']}"
                    callback_data = f"alloc|{r['name']}"
                    current_row.append({"text": btn_text, "callback_data": callback_data})
                    if len(current_row) == 2:
                        keyboard.append(current_row)
                        current_row = []
                if current_row:
                    keyboard.append(current_row)
                
                markup = {"inline_keyboard": keyboard}
                text_table = f"🏷️ **Available Ranges**\n━━━━━━━━━━━━━━━━━━━━━━\nClick a range below to allocate {ALLOCATE_QTY} numbers:"
                send_message(chat_id, text_table, reply_markup=markup, parse_mode="Markdown")
            else:
                send_message(chat_id, f"{result}\n\nPlease send /start to try again.", parse_mode="Markdown")
            
            del login_states[chat_id]
        return

def handle_callback(cb):
    cb_id = cb['id']
    chat_id = cb['message']['chat']['id']
    message_id = cb['message']['message_id']
    user_id = str(cb['from']['id'])
    data = cb['data']
    
    if data.startswith("alloc|"):
        range_name = data.split("|")[1]
        
        if user_id not in user_profiles:
            answer_callback(cb_id, "❌ Session expired. Please type /start.")
            return
            
        client_name = user_profiles[user_id]
        
        delete_message(chat_id, message_id)
        
        if user_id not in user_limits:
            user_limits[user_id] = {}
            
        last_alloc_str = user_limits[user_id].get(range_name)
        if last_alloc_str:
            last_alloc_time = datetime.fromisoformat(last_alloc_str)
            if datetime.now() < last_alloc_time + timedelta(hours=RATE_LIMIT_HOURS):
                time_left = (last_alloc_time + timedelta(hours=RATE_LIMIT_HOURS)) - datetime.now()
                mins_left = int(time_left.total_seconds() // 60)
                answer_callback(cb_id, f"⚠️ Rate Limit! Please wait {mins_left} minutes.")
                send_message(chat_id, f"⚠️ **Rate Limit Reached!**\n\nYou can only allocate {ALLOCATE_QTY} numbers from **{range_name}** every {RATE_LIMIT_HOURS} hours. Please wait **{mins_left} minutes** or choose a different range.", parse_mode="Markdown")
                return

        answer_callback(cb_id, f"⏳ Allocating...")
        success, message = perform_allocation(client_name, range_name)
        
        if success:
            user_limits[user_id][range_name] = datetime.now().isoformat()
            send_message(chat_id, f"🏷️ {range_name}\n\n{message}\n\n⏳ *Next allocation for this range available in {RATE_LIMIT_HOURS} hours.*", parse_mode="Markdown")
        else:
            send_message(chat_id, f"🏷️ {range_name}\n\n{message}", parse_mode="Markdown")

# ==========================================
# BOT POLLING LOOP
# ==========================================
def bot_polling():
    last_update_id = None
    while True:
        try:
            params = {'timeout': 15, 'offset': last_update_id}
            res = requests.get(f"{api_url}/getUpdates", params=params, timeout=20).json()
            
            if res.get('ok'):
                for update in res['result']:
                    last_update_id = update['update_id'] + 1
                    if 'message' in update:
                        handle_message(update['message'])
                    elif 'callback_query' in update:
                        handle_callback(update['callback_query'])
        except requests.exceptions.ReadTimeout:
            pass
        except Exception:
            time.sleep(2)

# ==========================================
# MAIN ENTRY POINT
# ==========================================
if __name__ == "__main__":
    threading.Thread(target=bot_polling, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
