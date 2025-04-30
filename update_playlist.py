import sys
import requests
import base64
import os

GITHUB_TOKEN = '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'
GITHUB_REPO_OWNER = 'dmcs19'
GITHUB_REPO_NAME = 'iptv_bot_automation'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/'

def update_playlist(m3u_link):
    print(f"Downloading M3U file from: {m3u_link}")
    m3u_content = download_m3u(m3u_link)
    if m3u_content:
        upload_to_github("playlist.m3u", m3u_content)

def download_m3u(m3u_url):
    try:
        response = requests.get(m3u_url)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        print(f"Successfully downloaded M3U file from: {m3u_url}")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error while downloading M3U file from {m3u_url}: {e}")
        return None

def upload_to_github(file_name, file_content):
    if not GITHUB_TOKEN:
        print("Error: GitHub token is missing.")
        return

    encoded_content = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": "Update playlist.m3u",
        "content": encoded_content
    }

    try:
        response = requests.put(f'{GITHUB_API_URL}{file_name}', headers={
            "Authorization": f"token {GITHUB_TOKEN}"
        }, json=payload)
        
        if response.status_code == 201:
            print(f"File uploaded successfully to {GITHUB_REPO_NAME}/{file_name}")
        else:
            print(f"Failed to upload file. HTTP Status Code: {response.status_code}")
            print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error during the GitHub upload process: {e}")

if __name__ == "__main__":
    # Check if the M3U link argument is provided
    if len(sys.argv) == 2:
        m3u_link = sys.argv[1]
        update_playlist(m3u_link)
    else:
        print("Error: M3U link argument missing.")
