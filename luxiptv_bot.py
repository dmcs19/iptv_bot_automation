import requests
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import asyncio
import subprocess
import re

MAIL_TM_API = "https://api.mail.tm"

def create_temp_account():
    session = requests.Session()
    
    # 🔁 Get a valid domain
    domains_resp = session.get(f"{MAIL_TM_API}/domains")
    domains = domains_resp.json()["hydra:member"]
    if not domains:
        raise Exception("No available domains from mail.tm")
    domain = domains[0]["domain"]  # just pick the first valid domain

    username = f"user{int(time.time())}@{domain}"
    password = "TempPassword123!"

    response = session.post(f"{MAIL_TM_API}/accounts", json={
        "address": username,
        "password": password
    })

    if response.status_code != 201:
        raise Exception(f"Failed to create temp mail: {response.text}")

    # 🔐 Authenticate to get token
    token_resp = session.post(f"{MAIL_TM_API}/token", json={
        "address": username,
        "password": password
    })
    token = token_resp.json()["token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session, username

def check_mail_and_extract(session):
    for _ in range(10):  # Retry for 5 mins
        msgs = session.get(f"{MAIL_TM_API}/messages").json()
        if msgs and "hydra:member" in msgs and msgs["hydra:member"]:
            msg_id = msgs["hydra:member"][0]["id"]
            msg = session.get(f"{MAIL_TM_API}/messages/{msg_id}").json()
            body = msg.get("text", "") or msg.get("html", "")
            username, password = extract_fields(body)
            if username and password:
                result = subprocess.run(
                    ['python', 'update_playlist_luxiptv.py', username, password],
                    capture_output=True,  # Capture the output of the script
                    text=True  # Capture the output as a string (not bytes)
                )                
                print(result.stderr)  # Print any errors if occurred
                return f"Your Username: {username}\nYour Password: {password}"
        time.sleep(30)
    return "❌ Email not received after 5 minutes."

def extract_fields(body):
    username_match = re.search(r'(?:Your\s+)?Username:\s*([^\s]+)', body)
    password_match = re.search(r'(?:Your\s+)?Password:\s*([^\s]+)', body)

    username = username_match.group(1) if username_match else None
    password = password_match.group(1) if password_match else None

    return username, password

def submit_form(email):
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--window-size=1920,1080")
    driver = uc.Chrome(options=options, use_subprocess=False, browser_executable_path="/opt/google/chrome/google-chrome")
    try:
        driver.get("https://lux-iptv.shop/")
        
        # ---------------- Step 1: Click small chat bubble ----------------
        small_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[title="chat widget"]'))
        )
        driver.switch_to.frame(small_iframe)

        bubble_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Chat widget"]'))
        )
        bubble_button.click()
        driver.switch_to.default_content()

        # ---------------- Step 2: Wait for expanded chat iframe ----------------
        large_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'iframe[title="chat widget"].open')
            )
        )
        driver.switch_to.frame(large_iframe)

        # ---------------- Step 3: Click "Submit" card ----------------
        submit_card = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//p[contains(text(),"Submit")]'))
        )
        submit_card.click()

        # ---------------- Step 4: Fill Email ----------------
        email_input = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="email"]'))
        )

        # Clear and fill email
        email_input.clear()
        email_input.send_keys(email)


        # ---------------- Step 5: Click "Start Chat" ----------------
        start_chat_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Start Chat")]'))
        )
        start_chat_button.click()

        # Optional: wait to see result
        time.sleep(5)
    finally:
        driver.quit()

### 🔁 Async wrapper function
async def run_form_process():
    loop = asyncio.get_event_loop()
    session, email = await loop.run_in_executor(None, create_temp_account)

    # Submit form in a thread
    await loop.run_in_executor(None, submit_form, email)

    # Wait for email in a thread
    result = await loop.run_in_executor(None, check_mail_and_extract, session)

    session.close()
    
    return result
