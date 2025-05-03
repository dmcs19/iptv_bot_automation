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
import os

MAILSAC_API = os.getenv("MAILSAC_API")

# Mailsac API and Gmail alias generation
MAILSAC_API = "https://api.mailsac.com/api/v1"

# Generate random Gmail alias
def generate_gmail_alias():
    base_email = "dmcsaraiva@gmail.com"
    alias = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))  # Random alias
    return f"{alias}+{alias}@gmail.com"

def generate_random_portuguese_phone():
    prefixes = ["91", "92", "93", "96"]
    prefix = random.choice(prefixes)
    rest = ''.join(str(random.randint(0, 9)) for _ in range(7))
    return f"+351{prefix}{rest}"

# Mailsac account to retrieve emails
def check_mail_and_extract_mailsac(mailsac_email, api_key):
    for _ in range(10):  # Retry for 5 minutes
        url = f"{MAILSAC_API}/addresses/{mailsac_email}/messages"
        headers = {
            "Mailsac-Key": api_key
        }

        resp = requests.get(url, headers=headers)
        if resp.status_code == 200 and resp.json():
            message_id = resp.json()[0]['id']
            msg_resp = requests.get(f"{MAILSAC_API}/addresses/{mailsac_email}/messages/{message_id}", headers=headers)
            if msg_resp.status_code == 200:
                body = msg_resp.json().get('textBody', '') or msg_resp.json().get('htmlBody', '')
                username, password, m3u_link = extract_fields(body)
                if username and password:
                    result = subprocess.run(
                        ['python', 'update_playlist_tellystudio.py', m3u_link],
                        capture_output=True,
                        text=True
                    )
                    print(result.stderr)
                    return f"Your Username: {username}\nYour Password: {password}\nM3U Link: {m3u_link}"
        time.sleep(30)
    return "❌ Email not received after 5 minutes."

def extract_fields(body):
    username_pattern = "Username:"
    password_pattern = "Password:"
    m3u_link_pattern = "M3U PLAYLIST URL:"
    username = password = m3u_link = None
    lines = body.splitlines()
    for line in lines:
        if username_pattern in line:
            username = line.split(username_pattern)[-1].strip()
        elif password_pattern in line:
            password = line.split(password_pattern)[-1].strip()
        elif m3u_link_pattern in line:
            m3u_link = line.split(m3u_link_pattern)[-1].strip()
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
        driver.get("https://tellystudio.com/shop/index.php/store/trial")

        order_now_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a#product5-order-button")))
        order_now_button.click()

        customfield_dropdown = wait.until(EC.presence_of_element_located((By.ID, "customfield2")))
        Select(customfield_dropdown).select_by_visible_text("Fire TVStick/Fire TVStick 4K/Fire TVCube")

        checkout_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#btnCompleteProductConfig")))
        checkout_button.click()

        checkout_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a#checkout")))
        checkout_button.click()

        wait.until(EC.presence_of_element_located((By.NAME, "firstname")))

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

        submit_btn = wait.until(EC.element_to_be_clickable((By.ID, "btnCompleteOrder")))
        submit_btn.click()

        time.sleep(5)
    finally:
        driver.quit()

# Updated async process
async def run_form_process():
    loop = asyncio.get_event_loop()

    # Generate a Gmail alias and Mailsac email
    gmail_alias = generate_gmail_alias()
    mailsac_email = "dmcsaraiva@mailsac.com"  # Your Mailsac email (this will receive forwarded emails)
    
    phone = generate_random_portuguese_phone()

    # Submit the form
    await loop.run_in_executor(None, submit_form, gmail_alias, phone)

    # Check the Mailsac inbox for the email
    result = await loop.run_in_executor(None, check_mail_and_extract_mailsac, mailsac_email, MAILSAC_API)

    url_host = f"http://telle.cc"
    result = f"URL Host: {url_host}\n{result}"
    return result
