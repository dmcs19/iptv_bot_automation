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

def generate_random_portuguese_phone():
    prefixes = ["91", "92", "93", "96"]
    prefix = random.choice(prefixes)
    rest = ''.join(str(random.randint(0, 9)) for _ in range(7))
    return f"+351{prefix}{rest}"

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
            username, password, m3u_link = extract_fields(body)
            if username and password:
                result = subprocess.run(
                    ['python', 'update_playlist_iptvdoor.py', m3u_link],
                    capture_output=True,  # Capture the output of the script
                    text=True  # Capture the output as a string (not bytes)
                )                
                print(result.stderr)  # Print any errors if occurred
                return f"Your Username: {username}\nYour Password: {password}\nM3u Link: {m3u_link}"
        time.sleep(30)
    return "❌ Email not received after 5 minutes."

def extract_fields(body):
    username_match = re.search(r'Username:\s*(\w+)', body)
    password_match = re.search(r'Password:\s*(\w+)', body)

    m3u_match = re.search(r'Primary:\s*(http[^\s]+m3uplus[^\s]*)', body)

    username = username_match.group(1) if username_match else None
    password = password_match.group(1) if password_match else None
    m3u_link = m3u_match.group(1) if m3u_match else None
    
    return username, password, m3u_link

def submit_form(email, phone):
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
    wait = WebDriverWait(driver, 20)
    try:
        driver.get("https://www.iptvdoor.com/step/store-checkout-free-trial/")

        # First name
        wait.until(EC.visibility_of_element_located((By.NAME, "billing_first_name")))
        driver.find_element(By.NAME, "billing_first_name").send_keys("John")

        # Last name
        wait.until(EC.visibility_of_element_located((By.NAME, "billing_last_name")))
        driver.find_element(By.NAME, "billing_last_name").send_keys("Doe")

        # Country select
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".select2-selection--single"))).click()
        search_box = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "select2-search__field")))
        search_box.send_keys("Portugal")
        search_box.send_keys(Keys.ENTER)

        # Email
        wait.until(EC.visibility_of_element_located((By.NAME, "billing_email")))
        driver.find_element(By.NAME, "billing_email").send_keys(email)

        # Phone
        wait.until(EC.visibility_of_element_located((By.NAME, "billing_phone")))
        driver.find_element(By.NAME, "billing_phone").send_keys(phone)

        # Place order button
        place_order_btn = wait.until(EC.presence_of_element_located((By.ID, "place_order")))
        driver.execute_script("arguments[0].scrollIntoView(true);", place_order_btn)
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.ID, "place_order"))).click()

        time.sleep(5)
    finally:
        driver.quit()

### 🔁 Async wrapper function
async def run_form_process():
    loop = asyncio.get_event_loop()
    session, email = await loop.run_in_executor(None, create_temp_account)
    phone = generate_random_portuguese_phone()

    # Submit form in a thread
    await loop.run_in_executor(None, submit_form, email, phone)

    # Wait for email in a thread
    result = await loop.run_in_executor(None, check_mail_and_extract, session)

    session.close()
    
    url_host = f"http://smarters.live:80"

    # Add it to the top of the result
    result = f"URL Host: {url_host}\n{result}"
    return result
