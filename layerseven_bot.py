import requests
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import asyncio
import subprocess
import os

MAIL_TM_API = "https://api.mail.tm"
CAPTCHA_API = os.getenv("CAPTCHA_API")

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

def solve_recaptcha(site_key, page_url):
    captcha_id = requests.post("http://2captcha.com/in.php", data={
        "key": CAPTCHA_API,
        "method": "userrecaptcha",
        "googlekey": site_key,
        "pageurl": page_url,
        "json": 1
    }).json()

    if captcha_id["status"] != 1:
        raise Exception(f"Failed to send captcha: {captcha_id}")

    captcha_id = captcha_id["request"]

    # Wait for result
    for _ in range(20):
        time.sleep(5)
        resp = requests.get("http://2captcha.com/res.php", params={
            "key": CAPTCHA_API,
            "action": "get",
            "id": captcha_id,
            "json": 1
        }).json()
        if resp["status"] == 1:
            return resp["request"]
    raise Exception("Captcha solving timeout or failed.")

def submit_form(email):
    options = uc.ChromeOptions()
    # options.add_argument("--headless=new")  # New headless mode (Chrome >=109)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = uc.Chrome(options=options, browser_executable_path="/opt/google/chrome/google-chrome")
    wait = WebDriverWait(driver, 20)
    try:
        url = "https://panel.layerseven.ai/sign-up"
        driver.get(url)
        
        wait.until(EC.presence_of_element_located((By.NAME, "email")))
        driver.find_element(By.NAME, "email").send_keys(email)
        driver.find_element(By.NAME, "password").send_keys("Password123!")
        
        actions = ActionChains(driver)
        actions.move_by_offset(100, 0).perform()  # Move the mouse
        time.sleep(1)
        actions.move_by_offset(-100, 0).perform()  # Move back

        # ▶️ Solve captcha via 2captcha
        site_key = "6Ldwf7wqAAAAANb7Y2mzgutgMalTDWxSf3v0gQQh"
        token = solve_recaptcha(site_key, url)

        time.sleep(3)

        wait.until(
            EC.presence_of_element_located((By.ID, "g-recaptcha-response"))
        )

        # Inject the token and dispatch events
        driver.execute_script("""
            const textarea = document.getElementById('g-recaptcha-response');
            textarea.style.display = 'block';
            textarea.value = arguments[0];

            textarea.dispatchEvent(new Event('change', { bubbles: true }));
            textarea.dispatchEvent(new Event('input', { bubbles: true }));

            const form = textarea.closest('form');
            if (form) {
                form.dispatchEvent(new Event('submit', { bubbles: true }));
            }
        """, token)
                
        button = driver.find_element(By.XPATH, "//button[contains(text(), 'Create account')]")
        button.click()
        
        orders_link = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(text(), 'Orders')]")
        ))
        orders_link.click()
        
        free_trial_link = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(text(), 'Request free trial')]")
        ))
        free_trial_link.click()
        
        view_accounts_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'View Accounts')]")
        ))
        view_accounts_button.click()

        username_element = driver.find_element(By.XPATH, "//p[b[text()='Username:']]")
        username = username_element.text.split(":")[1].strip()
        password_element = driver.find_element(By.XPATH, "//p[b[text()='Password:']]")
        password = password_element.text.split(":")[1].strip()
        
        subprocess.run(
                    ['python', 'update_playlist_layerseven.py', username, password],
                    capture_output=True,
                    text=True
                )
        return f"Your Username: {username}\nYour Password: {password}"
    finally:
        driver.quit()

### 🔁 Async wrapper function
async def run_form_process():
    loop = asyncio.get_event_loop()
    session, email = await loop.run_in_executor(None, create_temp_account)

    # Submit form in a thread
    result = await loop.run_in_executor(None, submit_form, email)

    session.close()
    
    url_host = f"http://hi-world.me"

    # Add it to the top of the result
    result = f"URL Host: {url_host}\n{result}"
    return result
