import re
import requests
from telegram.ext import ApplicationBuilder, MessageHandler, filters

BOT_TOKEN = "7941038643:AAFFM8jv2RkFyyxzgdzuyqy6UiCHNZhIlWo"
SUPABASE_URL = "https://zubkwzsnpdjtndlvqfqf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Ymt3enNucGRqdG5kbHZxZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDgyMjMsImV4cCI6MjA5MDcyNDIyM30.6fcSUpeuBONYGsWCG9lmOaf0lOPq9CDt2Ud9jXsvbSo"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

OTP_REGEX = r"\b\d{4,6}\b"

def extract_data(text):
    otp_match = re.search(OTP_REGEX, text)
    number_match = re.search(r"Number:\s*(.+)", text)

    otp = otp_match.group() if otp_match else None

    phone_last3 = None
    if number_match:
        digits = re.sub(r"\D", "", number_match.group(1))
        if len(digits) >= 3:
            phone_last3 = digits[-3:]

    return otp, phone_last3

async def handle(update, context):
    if not update.message or not update.message.text:
        return

    text = update.message.text

    otp, last3 = extract_data(text)

    if not otp or not last3:
        return

    payload = {
        "otp": otp,
        "phone_last3": last3,
        "raw_message": text
    }

    try:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/otp_logs",
            headers=HEADERS,
            json=payload,
            timeout=5
        )
    except:
        pass  # silent failure

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()
