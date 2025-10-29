import os
import time
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import subprocess

# ========== Load Credentials from Environment Variables ==========
ROLL_NUMBER = os.getenv("ROLL_NUMBER")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ========== ERP URL ==========
ERP_URL = "https://jecrc.mastersofterp.in/iitmsv4eGq0RuNHb0G5WbhLmTKLmTO7YBcJ4RHuXxCNPvuIw=?enc=EGbCGWnlHNJ/WdgJnKH8DA=="

# ========== Set Tesseract Path ==========
pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

# ========== Telegram Function ==========
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    r = requests.post(url, json=payload)
    print("Telegram message response:", r.status_code, r.text)

# ========== Setup Chrome Driver Options ==========
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")

# ========== Determine Installed Chrome Major Version ==========
def get_chrome_major_version():
    try:
        output = subprocess.check_output(["google-chrome", "--version"])  # or "chromium-browser"
        version_str = output.decode().strip().split()[-1]
        return int(version_str.split('.')[0])
    except Exception as e:
        print("⚠️ Could not detect Chrome version, falling back to automatic:", e)
        return None

chrome_major = get_chrome_major_version()

# Start Chrome, specifying version_main if detected
if chrome_major:
    driver = uc.Chrome(options=chrome_options, version_main=chrome_major)
else:
    driver = uc.Chrome(options=chrome_options)

driver.get(ERP_URL)
time.sleep(3)

# ========== LOGIN PROCESS ==========
try:
    try:
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txt_username"))
        )
    except:
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txtusername"))
        )

    try:
        password_field = driver.find_element(By.ID, "txt_password")
    except:
        password_field = driver.find_element(By.ID, "txtpassword")

    print("✅ Username & Password fields found.")
    username_field.send_keys(ROLL_NUMBER)
    password_field.send_keys(PASSWORD)

    captcha_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "captchaCanvas"))
    )
    captcha_element.screenshot("captcha.png")

    def process_captcha(image_path):
        img = Image.open(image_path).convert("L")
        img = img.filter(ImageFilter.MedianFilter())
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)
        return pytesseract.image_to_string(img, config="--psm 6").strip()

    captcha_text = process_captcha("captcha.png")
    print("🔍 Captcha Text:", captcha_text)

    captcha_input = driver.find_element(By.ID, "txtcaptcha")
    captcha_input.send_keys(captcha_text)

    login_button = driver.find_element(By.ID, "btnLogin")
    login_button.click()
    print("🔄 Attempting Login...")
    time.sleep(5)

    current_url = driver.current_url
    if "login" in current_url.lower():
        print("❌ ERP Login Failed!")
        send_telegram_message("❌ ERP Login Failed!")
        driver.quit()
        exit()
    else:
        print("✅ ERP Login Successful!")
        send_telegram_message("✅ ERP Login Successful!")

except Exception as e:
    print("❌ Error during login:", e)
    send_telegram_message("❌ ERP Login Failed!")
    driver.quit()
    exit()

# ========== Close Notice/News Modal if Present ==========
try:
    close_button = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='modal-header']//button[@class='close']"))
    )
    print("ℹ Notice/News modal found. Closing it...")
    driver.execute_script("arguments[0].click();", close_button)
    print("✅ Notice/News modal closed.")
except Exception as e:
    print("ℹ No Notice/News modal found or error closing modal:", e)

# ========== Navigate to LMS Transactions ==========
try:
    time.sleep(1)
    driver.execute_script("document.querySelector('#ctl00_mainMenu > ul > li:nth-child(3) > a').click();")
    print("✅ 'LMS' option clicked.")
    time.sleep(1)
    driver.execute_script("document.querySelector(\"[id='ctl00_mainMenu:submenu:9'] li:nth-child(1) > a\").click();")
    print("✅ 'Transactions' option clicked.")
except Exception as e:
    print("ℹ Error navigating menus:", e)

# ========== Updated Bell Icon Click (New Layout 2025) ==========
try:
    print("🔔 Searching for updated bell icon area...")

    # Wait for new UpdatePanel section to load
    update_panel = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_UpdatePanel1"))
    )
    print("✅ Update panel found.")

    # Try multiple possible selectors for bell icon
    bell_icon = None
    possible_selectors = [
        "#ctl00_ContentPlaceHolder1_UpdatePanel1 img[id*='imgNotify']",
        "#ctl00_ContentPlaceHolder1_UpdatePanel1 i[class*='fa-bell']",
        "#ctl00_ContentPlaceHolder1_UpdatePanel1 button[id*='btnNotify']",
        "#ctl00_ContentPlaceHolder1_UpdatePanel1 a[id*='imgNotify']"
    ]

    for selector in possible_selectors:
        try:
            bell_icon = update_panel.find_element(By.CSS_SELECTOR, selector)
            if bell_icon:
                print(f"✅ Bell icon found with selector: {selector}")
                break
        except:
            continue

    if bell_icon:
        driver.execute_script("arguments[0].click();", bell_icon)
        print("🔔 Bell icon clicked successfully.")
    else:
        print("⚠️ Bell icon not found in new layout.")
except Exception as e:
    print("ℹ Error while clicking bell icon:", e)

# ========== Wait for and Process Assignments ==========
try:
    print("⌛ Waiting for 'Select Course' heading...")
    select_course_heading = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Select Course')]"))
    )
    print("✅ 'Select Course' heading found.")

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    assignment_container = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#divAssignments"))
    )
    print("✅ 'Assignments List' container found.")

    table_element = assignment_container.find_element(By.ID, "DataTables_Table_0")
    print("✅ Assignment table found.")

    table_text = table_element.text
    if table_text.strip():
        send_telegram_message("📚 Assignment List:\n" + table_text)
    else:
        send_telegram_message("✅ You don't have any assignments to upload.")

except Exception as e:
    print("ℹ No assignments found or error:", e)
    send_telegram_message("✅ You don't have any assignments to upload.")

# ====== Automatic Browser Close ======
print("🧹 Automation complete. Closing browser shortly.")
time.sleep(10)
driver.quit()
