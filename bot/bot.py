#!/usr/bin/env python3
import re
import os
import requests
import time
import threading
from datetime import datetime
from flask import Flask

BOT_TOKEN = "YOUR_BOT_TOKEN"
SUPABASE_URL = "YOUR_SUPABASE_URL"
API_KEY = "YOUR_SUPABASE_API_KEY"

app = Flask(__name__)
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
last_update_id = 0


def save_to_supabase(otp, phone_last3, country, service, time_raw):
    try:
        data = {
            "otp": str(otp),
            "phone_last3": str(phone_last3),
            "country": str(country) if country else None,
            "service": str(service) if service else None,
            "time_raw": str(time_raw) if time_raw else None,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "message_time": datetime.now().isoformat()
        }

        headers = {
            "apikey": API_KEY,
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/otp_logs",
            headers=headers,
            json=data,
            timeout=10
        )

        return response.status_code in [200, 201]

    except Exception:
        return False


def process_updates():
    global last_update_id

    try:
        url = f"{TELEGRAM_API_URL}/getUpdates"
        params = {
            "offset": last_update_id + 1,
            "timeout": 30
        }

        response = requests.get(url, params=params, timeout=35)

        if not response.ok:
            return

        result = response.json().get("result", [])

        for update in result:
            last_update_id = update["update_id"]

            if "message" not in update:
                continue

            msg = update["message"]
            text = msg.get("text", "")

            otp_match = re.search(r"\b\d{4,6}\b", text)
            if not otp_match:
                continue

            otp = otp_match.group()

            number_match = re.search(r"☎️ Number:\s*(.+)", text)
            phone_last3 = "???"
            if number_match:
                number = number_match.group(1).strip()
                digits = re.sub(r"\D", "", number)
                if len(digits) >= 3:
                    phone_last3 = digits[-3:]

            country_match = re.search(r"🌍 Country:\s*(.+)", text)
            country = country_match.group(1).strip() if country_match else None

            service_match = re.search(r"⚙️ Service:\s*(.+)", text)
            service = service_match.group(1).strip() if service_match else None

            time_match = re.search(r"⏰ Time:\s*(.+)", text)
            time_raw = time_match.group(1).strip() if time_match else None

            save_to_supabase(otp, phone_last3, country, service, time_raw)

    except Exception:
        pass


def poll_loop():
    while True:
        try:
            process_updates()
        except Exception:
            pass
        time.sleep(1)


@app.route("/")
def health():
    return "MIMA Bot Running", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    poll_thread = threading.Thread(target=poll_loop, daemon=True)
    poll_thread.start()

    app.run(host="0.0.0.0", port=port, debug=False)
