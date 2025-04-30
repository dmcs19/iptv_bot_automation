import asyncio
import requests
from form_bot import run_form_process
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
# BOT_TOKEN = "8020314661:AAFUpm4RJPFeMXfZMWYTdpl6LB4BtJGG-KQ"
# CHAT_ID = "6444790041"

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=data)
    print("Telegram response:", response.json())

if __name__ == "__main__":
    try:
        result = asyncio.run(run_form_process())
        message = f"✅ Auto run completed:\n\n{result}"
    except Exception as e:
        message = f"❌ Auto run failed:\n{e}"
    
    send_to_telegram(message)
