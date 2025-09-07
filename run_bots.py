import argparse
import asyncio
import requests
from layerseven_bot import run_form_process as run_layerseven
from iptvdoor_bot import run_form_process as run_iptvdoor
from tereatv_bot import run_form_process as run_tereatv
from luxiptv_bot import run_form_process as run_luxiptv
from epg_bot import update_epg as run_epg
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

async def run_all_bots(selected_bot=None):
    bots = {
        "IPTVDoor": run_iptvdoor,
        "TereaTv": run_tereatv,
        "LayerSeven": run_layerseven,
        "LuxIPTV": run_luxiptv
    }

    if selected_bot and selected_bot != "All":
        bots = {k: v for k, v in bots.items() if k == selected_bot}

        if not bots:
            send_to_telegram(f"❌ No bot found with the name: {selected_bot}")
            return


    for name, func in bots.items():
        try:
            result = await func()
            message = f"✅ *{name}* run completed:\n\n{result}"
        except Exception as e:
            message = f"❌ *{name}* run failed:\n{e}"
        send_to_telegram(message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot", help="Bot to run (or 'All')", default="LuxIPTV")
    args = parser.parse_args()

    asyncio.run(run_all_bots(args.bot))

