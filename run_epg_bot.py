import asyncio
import requests
import base64
import os
import gzip
from io import BytesIO

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PAT = os.getenv("PAT")
GITHUB_REPO_OWNER = "dmcs19"
GITHUB_REPO_NAME = "iptv_bot_automation"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/"
EPG_GZ_URL = "https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz"
TARGET_FILE_NAME = "epg_ripper_PT1.xml"

# --- TELEGRAM ---
def send_to_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    response = requests.post(url, data=data)
    print("Telegram response:", response.json())

# --- DOWNLOAD & EXTRACT ---
def download_and_extract_gz(url: str) -> str:
    try:
        print(f"Downloading: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                xml_content = gz.read().decode("utf-8")
                print("Successfully extracted XML content.")
                return xml_content
        else:
            raise Exception(f"Failed to download file. Status Code: {response.status_code}")
    except Exception as e:
        raise Exception(f"Error downloading or extracting .gz file: {e}")

# --- UPLOAD TO GITHUB ---
def upload_to_github(file_name: str, file_content: str):
    if not PAT:
        print("Error: GitHub token is missing.")
        return

    existing_file_sha = None
    try:
        response = requests.get(f'{GITHUB_API_URL}{file_name}', headers={
            "Authorization": f"token {PAT}"
        })
        if response.status_code == 200:
            file_data = response.json()
            existing_file_sha = file_data['sha']
            print(f"File '{file_name}' already exists. SHA: {existing_file_sha}")
        elif response.status_code == 404:
            print(f"File '{file_name}' does not exist. Creating a new one.")
        else:
            print(f"GitHub API error while checking file: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"Error during GitHub API request: {e}")
        return

    encoded_content = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": f"Upload {file_name}",
        "content": encoded_content
    }

    if existing_file_sha:
        payload["sha"] = existing_file_sha

    try:
        response = requests.put(f'{GITHUB_API_URL}{file_name}', headers={
            "Authorization": f"token {PAT}"
        }, json=payload)
        
        if response.status_code in [200, 201]:
            print(f"Successfully uploaded {file_name} to GitHub.")
        else:
            print(f"Failed to upload {file_name}. Status: {response.status_code}")
            print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error during GitHub upload: {e}")

# --- MAIN UPDATE PROCESS ---
def update_epg():
    xml_content = download_and_extract_gz(EPG_GZ_URL)
    upload_to_github(TARGET_FILE_NAME, xml_content)
    return "EPG updated successfully."

# --- RUNNER ---
async def run_epg_bot():
    try:
        result = await asyncio.to_thread(update_epg)
        send_to_telegram(f"✅ *EPG* run completed:\n\n{result}")
    except Exception as e:
        send_to_telegram(f"❌ *EPG* run failed:\n{e}")

if __name__ == "__main__":
    asyncio.run(run_epg_bot())
