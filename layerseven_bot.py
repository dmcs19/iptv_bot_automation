import requests
import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import asyncio
import subprocess
import os
uc.Chrome.__del__ = lambda self: None

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
    for _ in range(30):
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
    # options.add_argument("--headless=new")
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
            // Set token
            document.getElementById('g-recaptcha-response').style.display = 'block';
            document.getElementById('g-recaptcha-response').value = arguments[0];

            // Trigger Google's internal callback
            const recaptchaCallback = document.querySelector('.g-recaptcha').getAttribute('data-callback');
            if (recaptchaCallback && typeof window[recaptchaCallback] === 'function') {
                window[recaptchaCallback](arguments[0]);
            }

            // Dispatch events to notify any Vue/React listeners
            const textarea = document.getElementById('g-recaptcha-response');
            ['change', 'input'].forEach(evtType => {
                textarea.dispatchEvent(new Event(evtType, { bubbles: true }));
            });
        """, token)

        time.sleep(3)
                
        button = driver.find_element(By.XPATH, "//button[contains(text(), 'Create account')]")
        button.click()
        
        time.sleep(1)
                
        order_links = driver.find_elements(By.CSS_SELECTOR, "a[href='/orders']")
        if len(order_links) > 1:
            order_links[1].click()  # Clicking the second element in the list
        else:
            print("Second element with href='/orders' not found.")
        
        free_trial = driver.find_elements(By.CSS_SELECTOR, "a[href='/checkout?free-trial=1']")
        if len(free_trial) > 1:
            free_trial[1].click()  # Clicking the second element in the list
        else:
            print("Second element with href='/checkout?free-trial=1' not found.")

        xtreme_cells = driver.find_elements(By.XPATH, "//td[contains(., 'Username:')]")

        if xtreme_cells:
            # Extract the inner HTML of the first matching <td>
            td_html = xtreme_cells[0].get_attribute("innerHTML")
            soup = BeautifulSoup(td_html, "html.parser")

            # Extract values by label
            def extract_value(label):
                tag = soup.find("b", string=lambda t: label in t)
                if tag and tag.next_sibling:
                    return tag.next_sibling.strip()
                return ""

            username = extract_value("Username:")
            password = extract_value("Password:")
            server = extract_value("Server URL:")

        else:
            raise Exception("Could not extract credentials, stopping process.")

        subprocess.run(
                    ['python', 'update_playlist_layerseven.py', username, password, server, "http://hi-world.me"],
                    capture_output=True,
                    text=True
                )
        return f"Your Username: {username}\nYour Password: {password}\nServer: {server}"
    finally:
        driver.quit()

### 🔁 Async wrapper function
async def run_form_process():
    loop = asyncio.get_event_loop()
    session, email = await loop.run_in_executor(None, create_temp_account)

    # Submit form in a thread
    result = await loop.run_in_executor(None, submit_form, email)

    session.close()

    return result
