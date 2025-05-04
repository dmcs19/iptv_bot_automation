import os
import requests
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import asyncio
import subprocess
import string

MAILSAC_KEY = os.getenv("MAILSAC_API")
MAILSAC_API_BASE = "https://mailsac.com/api"      

# Generate a random Gmail alias using your base address
def generate_gmail_alias():
    base_username = "dmcsaraiva"
    domain = "gmail.com"
    tag = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{base_username}+{tag}@{domain}"

# Generate a random Portuguese phone number
def generate_random_portuguese_phone():
    prefixes = ["91", "92", "93", "96"]
    prefix = random.choice(prefixes)
    rest = ''.join(str(random.randint(0, 9)) for _ in range(7))
    return f"+351{prefix}{rest}"

# Poll Mailsac inbox and extract the first message’s credentials
def check_mail_and_extract_mailsac(mailsac_email):
    headers = {"Mailsac-Key": MAILSAC_KEY}
    inbox_url = f"{MAILSAC_API_BASE}/addresses/{mailsac_email}/messages"
    
    for _ in range(10):  # retry ~5 minutes
        resp = requests.get(inbox_url, headers=headers)
        resp.raise_for_status()
        messages = resp.json()
        
        if messages:
            # Use the `_id` field per API spec :contentReference[oaicite:3]{index=3}
            msg_id = messages[0]["_id"]
            text_url = f"{MAILSAC_API_BASE}/text/{mailsac_email}/{msg_id}"
            
            msg_resp = requests.get(text_url, headers=headers)
            msg_resp.raise_for_status()
            body = msg_resp.text
            
            username, password, m3u_link = extract_fields(body)
            if username and password:
                # run your updater script
                result = subprocess.run(
                    ['python', 'update_playlist_tellystudio.py', m3u_link],
                    capture_output=True, text=True
                )
                print(result.stderr)
                return f"Your Username: {username}\nYour Password: {password}\nM3U Link: {m3u_link}"
        
        time.sleep(30)
    
    return "❌ Email not received after 5 minutes."

# Extract the three fields from the email body
def extract_fields(body):
    username = password = m3u_link = None
    for line in body.splitlines():
        if "Username:" in line:
            username = line.split("Username:")[-1].strip()
        elif "Password:" in line:
            password = line.split("Password:")[-1].strip()
        elif "M3U PLAYLIST URL:" in line:
            m3u_link = line.split("M3U PLAYLIST URL:")[-1].strip()
    return username, password, m3u_link

# Submit TellyStudio trial form
def submit_form(email, phone):
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    driver = uc.Chrome(
        options=options,
        use_subprocess=False,
        browser_executable_path="/opt/google/chrome/google-chrome"
    )
    wait = WebDriverWait(driver, 20)
    
    try:
        driver.get("https://tellystudio.com/shop/index.php/store/trial")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a#product5-order-button"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "customfield2")))
        
        Select(driver.find_element(By.ID, "customfield2")) \
            .select_by_visible_text("Fire TVStick/Fire TVStick 4K/Fire TVCube")
        
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#btnCompleteProductConfig"))).click()
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a#checkout"))).click()
        wait.until(EC.presence_of_element_located((By.NAME, "firstname")))
        
        # Fill in the form
        Select(driver.find_element(By.NAME, "country")).select_by_visible_text("Portugal")
        driver.find_element(By.NAME, "firstname").send_keys("John")
        driver.find_element(By.NAME, "lastname").send_keys("Doe")
        driver.find_element(By.NAME, "email").send_keys(email)
        driver.find_element(By.NAME, "phonenumber").send_keys(phone)
        driver.find_element(By.NAME, "address1").send_keys("123 Test St")
        driver.find_element(By.NAME, "city").send_keys("Lisbon")
        driver.find_element(By.NAME, "postcode").send_keys("1000-000")
        driver.find_element(By.NAME, "state").send_keys("Lisbon")
        driver.find_element(By.NAME, "password").send_keys("Password123!")
        driver.find_element(By.NAME, "password2").send_keys("Password123!")
        
        wait.until(EC.element_to_be_clickable((By.ID, "btnCompleteOrder"))).click()
        time.sleep(5)
    finally:
        driver.quit()

# Async orchestration
async def run_form_process():
    loop = asyncio.get_event_loop()
    gmail_alias = generate_gmail_alias()
    mailsac_email = "dmcsaraiva@mailsac.com"
    phone = generate_random_portuguese_phone()
    
    await loop.run_in_executor(None, submit_form, gmail_alias, phone)
    result = await loop.run_in_executor(None, check_mail_and_extract_mailsac, mailsac_email)
    
    url_host = "http://telle.cc"
    return f"URL Host: {url_host}\n{result}"
