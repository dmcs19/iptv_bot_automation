import sys
import requests
import base64
import os

PAT = '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'
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
    # Check if the M3U link argument is provided
    if len(sys.argv) == 2:
        m3u_link = sys.argv[1]
        update_playlist(m3u_link)
    else:
        print("Error: M3U link argument missing.")
