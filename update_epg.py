import requests
import base64
import os
import gzip
from io import BytesIO

# Environment and GitHub details
PAT = os.getenv("PAT")
GITHUB_REPO_OWNER = 'dmcs19'
GITHUB_REPO_NAME = 'iptv_bot_automation'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/'

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

def download_and_extract_gz(url):
    try:
        print(f"Downloading: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                xml_content = gz.read().decode('utf-8')
                print("Successfully extracted XML content.")
                return xml_content
        else:
            print(f"Failed to download file. Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading or extracting .gz file: {e}")
        return None

if __name__ == "__main__":
    gz_url = "https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz"
    xml_content = download_and_extract_gz(gz_url)
    if xml_content:
        upload_to_github("epg_ripper_PT1.xml", xml_content)