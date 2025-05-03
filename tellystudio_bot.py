import requests
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import asyncio
import subprocess

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
    for _ in range(120):  # Retry for 1 hour
        msgs = session.get(f"{MAIL_TM_API}/messages").json()
        if msgs and "hydra:member" in msgs and msgs["hydra:member"]:
            msg_id = msgs["hydra:member"][0]["id"]
            msg = session.get(f"{MAIL_TM_API}/messages/{msg_id}").json()
            body = msg.get("text", "") or msg.get("html", "")
            username, password, m3u_link = extract_fields(body)
            if username and password:
                result = subprocess.run(
                    ['python', 'update_playlist_tellystudio.py', m3u_link],
                    capture_output=True,  # Capture the output of the script
                    text=True  # Capture the output as a string (not bytes)
                )                
                print(result.stderr)  # Print any errors if occurred
                return f"Your Username: {username}\nYour Password: {password}\nM3u Link: {m3u_link}"
        time.sleep(30)
    return "❌ Email not received after 1 hour."

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
    
    url_host = f"http://telle.cc"

    # Add it to the top of the result
    result = f"URL Host: {url_host}\n{result}"
    return result
