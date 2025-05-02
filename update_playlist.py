import sys
import requests
import base64
import os

PAT = os.getenv("PAT")
GITHUB_REPO_OWNER = 'dmcs19'
GITHUB_REPO_NAME = 'iptv_bot_automation'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/'

def update_playlist(m3u_link, allowed_channels):
    print(f"Downloading M3U file from: {m3u_link}")
    m3u_content = download_m3u(m3u_link)
    if m3u_content:
        filtered_content = filter_m3u_content(m3u_content, allowed_channels)
        if filtered_content:
            upload_to_github("playlist.m3u", filtered_content)
        else:
            print("No valid content found to upload.")
    else:
        print("Failed to download M3U content.")

def download_m3u(m3u_url):
    try:
        response = requests.get(m3u_url)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        print(f"Successfully downloaded M3U file from: {m3u_url}")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error while downloading M3U file from {m3u_url}: {e}")
        return None

def filter_m3u_content(m3u_content, allowed_channels):
    lines = m3u_content.strip().splitlines()
    filtered_lines = []

    if len(lines) >= 2:
        filtered_lines.extend(lines[:2])
    else:
        print("M3U content seems too short or malformed.")
        return None

    i = 2
    while i < len(lines) - 1:
        line = lines[i]
        if line.startswith("#EXTINF"):
            channel_name = line.split(",")[-1].strip()
            url = lines[i + 1]

            if any(partial.lower() in channel_name.lower() for partial in allowed_channels):
                filtered_lines.append(line)
                filtered_lines.append(url)
            i += 2
        else:
            i += 1

    return "\n".join(filtered_lines) if len(filtered_lines) > 2 else None

def upload_to_github(file_name, file_content):
    if not PAT:
        print("Error: GitHub token is missing.")
        return

    existing_file_sha = None
    try:
        # Get the metadata of the file (if it exists)
        response = requests.get(f'{GITHUB_API_URL}{file_name}', headers={
            "Authorization": f"token {PAT}"
        })
        
        if response.status_code == 200:
            # File exists, extract the SHA value
            file_data = response.json()
            existing_file_sha = file_data['sha']
            print(f"File '{file_name}' already exists. SHA: {existing_file_sha}")
        elif response.status_code == 404:
            print(f"File '{file_name}' does not exist. Will create a new file.")
        else:
            print(f"Failed to check file existence. HTTP Status Code: {response.status_code}")
            print(response.json())
            return
    except requests.exceptions.RequestException as e:
        print(f"Error during GitHub API request: {e}")
        return

    encoded_content = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": "Update playlist.m3u",
        "content": encoded_content
    }

    if existing_file_sha:
        payload["sha"] = existing_file_sha
        print(f"Updating file '{file_name}' with SHA: {existing_file_sha}")

    try:
        response = requests.put(f'{GITHUB_API_URL}{file_name}', headers={
            "Authorization": f"token {PAT}"
        }, json=payload)
        
        if response.status_code == 201 or response.status_code == 200:
            print(f"File uploaded successfully to {GITHUB_REPO_NAME}/{file_name}")
        else:
            print(f"Failed to upload file. HTTP Status Code: {response.status_code}")
            print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error during the GitHub upload process: {e}")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        m3u_link = sys.argv[1]
        selected_channels = [
            "PT: Sporting TV",
            "PT: SPORT TV",
            "PT: NBA",
            "PT: Eleven Sports",
            "PT: Benfica",
            "4K: Sky Sports F1 UHD",
            "Sky Sports Football",
            "Sky Sports Main Event",
            "Sky Sports Premier Leauge",
            "ESP | DAZN",
            "ESP | M.Deportes",
            "ESP| LaLiga" 
        ]
        update_playlist(m3u_link, selected_channels)
    else:
        print("Error: M3U link argument missing.")
