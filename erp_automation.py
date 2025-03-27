import os
import time
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

# Load credentials and settings from environment variables
ROLL_NUMBER = os.environ.get("ROLL_NUMBER")
PASSWORD = os.environ.get("PASSWORD")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
ERP_URL = os.environ.get("ERP_URL")

if not all([ROLL_NUMBER, PASSWORD, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ERP_URL]):
    raise Exception("Missing one or more required environment variables.")

# Set Tesseract path; default for Linux is /usr/bin/tesseract
tess_path = os.environ.get("TESSERACT_PATH")
if not tess_path or tess_path.strip() == "":
    tess_path = "/usr/bin/tesseract"
print("Using Tesseract command:", tess_path)
pytesseract.pytesseract.tesseract_cmd = tess_path

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    r = requests.post(url, json=payload)
    print("Telegram message response:", r.status_code, r.text)

# Setup Chrome Driver options with fixed window size and headless mode enabled
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")

driver = uc.Chrome(options=chrome_options, version_main=133)
driver.get(ERP_URL)
time.sleep(5)

# ----- LOGIN PROCESS -----
login_message = ""
try:
    # Locate username field
    try:
        username_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "txt_username"))
        )
    except Exception:
        username_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "txtusername"))
        )
    
    # Locate password field
    try:
        password_field = driver.find_element(By.ID, "txt_password")
    except Exception:
        password_field = driver.find_element(By.ID, "txtpassword")
    
    username_field.send_keys(ROLL_NUMBER)
    password_field.send_keys(PASSWORD)
    
    # CAPTCHA handling: Save screenshot to /tmp folder
    captcha_path = "/tmp/captcha.png"
    print("Using temporary captcha file:", captcha_path)
    
    captcha_element = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "captchaCanvas"))
    )
    
    if not captcha_element.screenshot(captcha_path):
        raise Exception("Captcha screenshot failed.")
    
    if os.path.exists(captcha_path):
        print("Captcha file created at:", captcha_path)
        # Update permissions if required
        os.chmod(captcha_path, 0o777)
        print("Permissions updated to 777.")
    else:
        raise Exception("Captcha file not found after saving!")
    
    def process_captcha(image_path):
        img = Image.open(image_path).convert("L")
        img = img.filter(ImageFilter.MedianFilter())
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)
        return pytesseract.image_to_string(img, config="--psm 6").strip()
    
    captcha_text = process_captcha(captcha_path)
    print("Captcha text:", captcha_text)
    
    captcha_input = driver.find_element(By.ID, "txtcaptcha")
    captcha_input.send_keys(captcha_text)
    
    login_button = driver.find_element(By.ID, "btnLogin")
    login_button.click()
    time.sleep(7)
    
    current_url = driver.current_url
    if "login" in current_url.lower():
        login_message = "❌ ERP Login Failed!"
    else:
        login_message = "✅ ERP Login Successful!"
    print(login_message)
except Exception as e:
    login_message = "❌ Error during login: " + str(e)
    print(login_message)

# Save page source for debugging
page_source_path = "/tmp/page_source.html"
with open(page_source_path, "w") as f:
    f.write(driver.page_source)
print("Page source saved to:", page_source_path)

# ----- Close Notice/News Modal if Present -----
try:
    close_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='modal-header']//button[@class='close']"))
    )
    driver.execute_script("arguments[0].click();", close_button)
    print("✅ Notice/News modal closed.")
except Exception as e:
    print("ℹ No Notice/News modal found or error closing modal:", e)

# ----- Click 'LMS' Option -----
try:
    lms = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#ctl00_mainMenu > ul > li:nth-child(3) > a"))
    )
    driver.execute_script("arguments[0].click();", lms)
    print("✅ 'LMS' option clicked.")
except Exception as e:
    print("ℹ Error clicking 'LMS' option:", e)

# ----- Click 'Transactions' Option from Submenu -----
try:
    transactions = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[id='ctl00_mainMenu:submenu:9'] li:nth-child(1) > a"))
    )
    driver.execute_script("arguments[0].click();", transactions)
    print("✅ 'Transactions' option clicked.")
except Exception as e:
    print("ℹ Transactions option not found or not clickable:", e)

# ----- Wait for "Select Course" Heading -----
try:
    select_course_heading = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Select Course')]"))
    )
    print("✅ 'Select Course' heading found:", select_course_heading.text)
except Exception as e:
    print("ℹ 'Select Course' heading not found:", e)

# ----- Click Bell Icon Once -----
try:
    bell = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_imgNotify"))
    )
    driver.execute_script("arguments[0].click();", bell)
    print("✅ Bell icon clicked once.")
except Exception as e:
    print("ℹ Bell icon not found or not clickable:", e)

# ----- Scroll Down to End of Page -----
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(3)

# ----- Check for Assignment List Table -----
assignment_message = ""
try:
    assignment_container = WebDriverWait(driver, 30).until(
         EC.presence_of_element_located((By.CSS_SELECTOR, "#divAssignments"))
    )
    try:
         table_element = assignment_container.find_element(By.ID, "DataTables_Table_0")
         table_text = table_element.text
         if table_text.strip():
             assignment_message = "Assignment List:\n" + table_text
         else:
             assignment_message = "ℹ Assignment table is empty."
    except Exception:
         assignment_message = "ℹ No assignments to upload."
except Exception as e:
    assignment_message = "ℹ 'Assignments List' container not found: " + str(e)

final_message = login_message + "\n" + assignment_message
send_telegram_message(final_message)

driver.quit()
