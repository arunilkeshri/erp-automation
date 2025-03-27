import os
import time
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
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

# Setup Chrome Driver options with fixed window size
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36")

# For CI environment, headless mode must be enabled and binary location specified.
if os.environ.get("CI"):
    chrome_options.add_argument("--headless")
    chrome_options.binary_location = "/usr/bin/chromium-browser"
else:
    # Local testing with visible browser
    pass

driver = uc.Chrome(options=chrome_options, version_main=133)
driver.get(ERP_URL)
time.sleep(5)

# ----- LOGIN PROCESS -----
login_message = ""
try:
    try:
        username_field = WebDriverWait(driver, 45).until(
            EC.presence_of_element_located((By.ID, "txt_username"))
        )
    except Exception:
        username_field = WebDriverWait(driver, 45).until(
            EC.presence_of_element_located((By.ID, "txtusername"))
        )
    
    try:
        password_field = driver.find_element(By.ID, "txt_password")
    except Exception:
        password_field = driver.find_element(By.ID, "txtpassword")
    
    username_field.send_keys(ROLL_NUMBER)
    password_field.send_keys(PASSWORD)
    
    captcha_path = "/tmp/captcha.png"
    print("Using temporary captcha file:", captcha_path)
    
    captcha_element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "captchaCanvas"))
    )
    
    if not captcha_element.screenshot(captcha_path):
        raise Exception("Captcha screenshot failed.")
    
    if os.path.exists(captcha_path):
        print("Captcha file created at:", captcha_path)
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

page_source_path = "/tmp/page_source.html"
with open(page_source_path, "w") as f:
    f.write(driver.page_source)
print("Page source saved to:", page_source_path)

try:
    close_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@class='modal-header']//button[@class='close']"))
    )
    driver.execute_script("arguments[0].click();", close_button)
    print("✅ Notice/News modal closed.")
except Exception:
    print("ℹ No Notice/News modal found or error closing modal.")

try:
    lms = WebDriverWait(driver, 45).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#ctl00_mainMenu > ul > li:nth-child(3) > a"))
    )
    driver.execute_script("arguments[0].click();", lms)
    print("✅ 'LMS' option clicked.")
except Exception:
    print("ℹ Error clicking 'LMS' option.")

transactions_exists = driver.execute_script(
    "return document.querySelector('[id=\"ctl00_mainMenu:submenu:9\"] li:nth-child(1) > a') !== null"
)
print("Debug - Transactions element exists:", transactions_exists)

try:
    transactions = WebDriverWait(driver, 45).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[id='ctl00_mainMenu:submenu:9'] li:nth-child(1) > a"))
    )
    # Use ActionChains to move to the element and click
    actions = ActionChains(driver)
    actions.move_to_element(transactions).click().perform()
    print("✅ 'Transactions' option clicked using ActionChains.")
except Exception:
    print("ℹ Transactions option not found or not clickable.")

try:
    select_course_heading = WebDriverWait(driver, 45).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Select Course')]"))
    )
    print("✅ 'Select Course' heading found:", select_course_heading.text)
except Exception:
    print("ℹ 'Select Course' heading not found.")

bell_exists = driver.execute_script(
    "return document.querySelector('#ctl00_ContentPlaceHolder1_imgNotify') !== null"
)
print("Debug - Bell icon exists:", bell_exists)

try:
    bell = WebDriverWait(driver, 45).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_imgNotify"))
    )
    ActionChains(driver).move_to_element(bell).click().perform()
    print("✅ Bell icon clicked using ActionChains.")
except Exception:
    print("ℹ Bell icon not found or not clickable.")

driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(5)

assignment_message = ""
try:
    assignment_container = WebDriverWait(driver, 45).until(
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
except Exception:
    assignment_message = "ℹ 'Assignments List' container not found."

final_message = login_message + "\n" + assignment_message
send_telegram_message(final_message)

driver.quit()
