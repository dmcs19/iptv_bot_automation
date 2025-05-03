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
import string

# MAIL_TM_API = "https://api.mail.tm"  # ❌ Old temp mail API (commented)

def generate_random_portuguese_phone():
    prefixes = ["91", "92", "93", "96"]
    prefix = random.choice(prefixes)
    rest = ''.join(str(random.randint(0, 9)) for _ in range(7))
    return f"+351{prefix}{rest}"

# ✅ NEW: 1secmail-based temp mail creation
def create_1secmail_account():
    domain_list = ["esiix.com", "yoggm.com", "wwjmp.com"]
    domain = random.choice(domain_list)
    login = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    email = f"{login}@{domain}"
    return login, domain, email

# ❌ Old method using mail.tm (commented)
# def create_temp_account():
#     session = requests.Session()
#     domains_resp = session.get(f"{MAIL_TM_API}/domains")
#     domains = domains_resp.json()["hydra:member"]
#     if not domains:
#         raise Exception("No available domains from mail.tm")
#     domain = domains[0]["domain"]
#     username = f"user{int(time.time())}@{domain}"
#     password = "TempPassword123!"
#     response = session.post(f"{MAIL_TM_API}/accounts", json={
#         "address": username,
#         "password": password
#     })
#     if response.status_code != 201:
#         raise Exception(f"Failed to create temp mail: {response.text}")
#     token_resp = session.post(f"{MAIL_TM_API}/token", json={
#         "address": username,
#         "password": password
#     })
#     token = token_resp.json()["token"]
#     session.headers.update({"Authorization": f"Bearer {token}"})
#     return session, username

# ✅ NEW: Uses 1secmail API to poll inbox and extract credentials
def check_mail_and_extract_1secmail(login, domain):
    for _ in range(20):  # Retry for 10 minutes
        resp = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}")
        if resp.status_code == 200 and resp.json():
            message_id = resp.json()[0]['id']
            msg_resp = requests.get(f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={message_id}")
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
                    return f"Your Username: {username}\nYour Password: {password}\nM3u Link: {m3u_link}"
        time.sleep(30)
    return "❌ Email not received after 10 minutes."

# ❌ Old mail.tm polling (commented)
# def check_mail_and_extract(session):
#     for _ in range(120):  # Retry for 1 hour
#         msgs = session.get(f"{MAIL_TM_API}/messages").json()
#         if msgs and "hydra:member" in msgs and msgs["hydra:member"]:
#             msg_id = msgs["hydra:member"][0]["id"]
#             msg = session.get(f"{MAIL_TM_API}/messages/{msg_id}").json()
#             body = msg.get("text", "") or msg.get("html", "")
#             username, password, m3u_link = extract_fields(body)
#             if username and password:
#                 result = subprocess.run(
#                     ['python', 'update_playlist_tellystudio.py', m3u_link],
#                     capture_output=True,
#                     text=True
#                 )
#                 print(result.stderr)
#                 return f"Your Username: {username}\nYour Password: {password}\nM3u Link: {m3u_link}"
#         time.sleep(30)
#     return "❌ Email not received after 1 hour."

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

# ✅ Updated async process
async def run_form_process():
    loop = asyncio.get_event_loop()
    login, domain, email = await loop.run_in_executor(None, create_1secmail_account)
    phone = generate_random_portuguese_phone()

    await loop.run_in_executor(None, submit_form, email, phone)

    result = await loop.run_in_executor(None, check_mail_and_extract_1secmail, login, domain)

    url_host = f"http://telle.cc"
    result = f"URL Host: {url_host}\n{result}"
    return result
