import os
import time
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
# For GitHub Actions (Linux), adjust this path if needed.
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# ========== Telegram Function ==========
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    r = requests.post(url, json=payload)
    print("Telegram message response:", r.status_code, r.text)

# ========== Setup Chrome Driver Options ==========
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--headless")  # Enable headless mode for GitHub Actions
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")

# Start Chrome without specifying version_main
driver = uc.Chrome(options=chrome_options)  
driver.get(ERP_URL)
time.sleep(3)

# ========== LOGIN PROCESS ==========
try:
    # Locate username field (try both IDs)
    try:
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txt_username"))
        )
    except Exception:
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txtusername"))
        )
    
    # Locate password field (try both IDs)
    try:
        password_field = driver.find_element(By.ID, "txt_password")
    except Exception:
        password_field = driver.find_element(By.ID, "txtpassword")
    
    print("✅ Username & Password fields found.")
    username_field.send_keys(ROLL_NUMBER)
    password_field.send_keys(PASSWORD)
    
    # CAPTCHA handling: Capture and process CAPTCHA image
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
    else:
        print("✅ ERP Login Successful!")
        send_telegram_message("✅ ERP Login Successful!")
except Exception as e:
    print("❌ Error during login:", e)
    send_telegram_message("❌ Login Failed!")
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

# ========== Click 'LMS' Option ==========
try:
    time.sleep(1)  # Wait for the top menu to be interactable
    driver.execute_script("document.querySelector('#ctl00_mainMenu > ul > li:nth-child(3) > a').click();")
    print("✅ 'LMS' option clicked.")
except Exception as e:
    print("ℹ Error clicking 'LMS' option:", e)

# ========== Click 'Transactions' Option from Submenu ==========
try:
    time.sleep(1)  # Wait for submenu to appear
    driver.execute_script(
        "document.querySelector(\"[id='ctl00_mainMenu:submenu:9'] li:nth-child(1) > a\").click();"
    )
    print("✅ 'Transactions' option clicked.")
except Exception as e:
    print("ℹ Error clicking 'Transactions' option:", e)

# ========== Wait for 'Select Course' Heading ==========
try:
    select_course_heading = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Select Course')]"))
    )
    print("✅ 'Select Course' heading found:", select_course_heading.text)
except Exception as e:
    print("ℹ 'Select Course' heading not found:", e)

# ========== Click Bell Icon Once ==========
try:
    time.sleep(1)  # Allow time for adjustments after heading appears
    driver.execute_script("document.querySelector('#ctl00_ContentPlaceHolder1_imgNotify').click();")
    print("✅ Bell icon clicked once.")
except Exception as e:
    print("ℹ Error clicking bell icon:", e)

# ========== Scroll Down to End of Page ==========
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

# ========== Check for Assignment List Table and Send via Telegram as Text ==========
try:
    assignment_container = WebDriverWait(driver, 10).until(
         EC.presence_of_element_located((By.CSS_SELECTOR, "#divAssignments"))
    )
    print("✅ 'Assignments List' container found.")
    
    try:
         table_element = assignment_container.find_element(By.ID, "DataTables_Table_0")
         print("✅ Assignment table found.")
         table_text = table_element.text
         if table_text.strip():
             send_telegram_message("Assignment List:\n" + table_text)
         else:
             send_telegram_message("ℹ Assignment table is empty.")
    except Exception as e:
         print("ℹ Assignment table not found; no assignments to upload.", e)
         send_telegram_message("ℹ No assignments to upload.")
except Exception as e:
    print("ℹ 'Assignments List' container not found:", e)

# ====== Keep Browser Window Open ======
print("Automation complete. Browser window will remain open. Close it manually when done.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Script interrupted. Please close the browser manually.")
    driver.quit()
