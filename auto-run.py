import asyncio
import requests
# from goldclub_bot import run_form_process as run goldclub
# from tellystudio_bot import run_form_process as run_tellystudio
from layerseven_bot import run_form_process as run_layerseven
from iptvdoor_bot import run_form_process as run_iptvdoor
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=data)
    print("Telegram response:", response.json())

async def run_all_bots():
    bots = {
        "IPTVDoor": run_iptvdoor,
        "LayerSeven": run_layerseven
    }

    for name, func in bots.items():
        try:
            result = await func()
            message = f"✅ *{name}* auto run completed:\n\n{result}"
        except Exception as e:
            message = f"❌ *{name}* auto run failed:\n{e}"
        send_to_telegram(message)

if __name__ == "__main__":
    asyncio.run(run_all_bots())
