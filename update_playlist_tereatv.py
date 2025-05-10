import sys
import requests
import base64
import os

PAT = os.getenv("PAT")
GITHUB_REPO_OWNER = 'dmcs19'
GITHUB_REPO_NAME = 'iptv_bot_automation'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/'

def download_file_from_github(file_name):
    try:
        response = requests.get(f'{GITHUB_API_URL}{file_name}', headers={
            "Authorization": f"token {PAT}"
        })
        if response.status_code == 200:
            file_data = response.json()
            content = base64.b64decode(file_data['content']).decode('utf-8')
            print(f"Successfully downloaded {file_name} from GitHub.")
            return content
        else:
            print(f"Failed to download {file_name}. Status Code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error while downloading {file_name} from GitHub: {e}")
        return None

def replace_credentials(template_content, username, password, server):
    return template_content.replace("username", username).replace("password", password).replace("server", server)

def upload_to_github(file_name, file_content):
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

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    main_server = sys.argv[3]
    backup_server = sys.argv[4]

    # Step 1: Handle M3U Playlist Template
    template_content = download_file_from_github("playlist_tereatv_template.m3u")
    if template_content:
        updated_content = replace_credentials(template_content, username, password, main_server)
        upload_to_github("playlist3.m3u", updated_content)
        updated_content = replace_credentials(template_content, username, password, backup_server)
        upload_to_github("playlist4.m3u", updated_content)
