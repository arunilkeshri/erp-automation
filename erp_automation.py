import time
import os
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

# ========== Load Credentials from Environment Variables ==========
ROLL_NUMBER = os.getenv("ROLL_NUMBER")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ========== ERP URL ==========
ERP_URL = "https://jecrc.mastersofterp.in/iitmsv4eGq0RuNHb0G5WbhLmTKLmTO7YBcJ4RHuXxCNPvuIw=?enc=EGbCGWnlHNJ/WdgJnKH8DA=="

# ========== Set Tesseract Path ==========
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"  # Adjust for GitHub Actions/Linux

# ========== Telegram Function ==========
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    r = requests.post(url, json=payload)
    print("Telegram message response:", r.status_code, r.text)

# ========== Setup Chrome Driver Options ==========
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--headless")  # Enable headless mode for GitHub
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")

# Start Chrome
driver = uc.Chrome(options=chrome_options, version_main=133)
driver.get(ERP_URL)
time.sleep(3)

# ========== LOGIN PROCESS ==========
try:
    username_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "txt_username")))
    password_field = driver.find_element(By.ID, "txt_password")

    username_field.send_keys(ROLL_NUMBER)
    password_field.send_keys(PASSWORD)

    # CAPTCHA Handling
    captcha_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "captchaCanvas")))
    captcha_path = "/tmp/captcha.png"
    captcha_element.screenshot(captcha_path)

    def process_captcha(image_path):
        img = Image.open(image_path).convert("L")
        img = img.filter(ImageFilter.MedianFilter())
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)
        return pytesseract.image_to_string(img, config="--psm 6").strip()

    captcha_text = process_captcha(captcha_path)
    print("🔍 CAPTCHA Text:", captcha_text)

    driver.find_element(By.ID, "txtcaptcha").send_keys(captcha_text)
    driver.find_element(By.ID, "btnLogin").click()
    time.sleep(5)

    if "login" in driver.current_url.lower():
        raise Exception("❌ ERP Login Failed!")
    
    print("✅ ERP Login Successful!")
    send_telegram_message("✅ ERP Login Successful!")

except Exception as e:
    print("❌ Error during login:", e)
    send_telegram_message("❌ Login Failed!")
    driver.quit()
    exit()

# ========== Check Assignments ==========
try:
    assignment_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#divAssignments"))
    )
    print("✅ 'Assignments List' container found.")

    try:
        table_element = assignment_container.find_element(By.ID, "DataTables_Table_0")
        table_text = table_element.text
        if table_text.strip():
            send_telegram_message("📜 Assignment List:\n" + table_text)
        else:
            send_telegram_message("ℹ No assignments found.")
    except:
        send_telegram_message("ℹ No assignments to upload.")
except:
    send_telegram_message("ℹ 'Assignments List' container not found.")

print("✅ Script Completed.")
driver.quit()
