import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import time
import requests

# ========== Read Credentials from Environment Variables ==========
ROLL_NUMBER = os.environ.get("ROLL_NUMBER")
PASSWORD = os.environ.get("PASSWORD")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not all([ROLL_NUMBER, PASSWORD, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    raise Exception("Missing required environment variables. Ensure ROLL_NUMBER, PASSWORD, TELEGRAM_BOT_TOKEN, and TELEGRAM_CHAT_ID are set.")

# ========== ERP URL ==========
ERP_URL = "https://jecrc.mastersofterp.in/iitmsv4eGq0RuNHb0G5WbhLmTKLmTO7YBcJ4RHuXxCNPvuIw=?enc=EGbCGWnlHNJ/WdgJnKH8DA=="

# ========== Set Tesseract Path ==========
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"  # For GitHub Actions on Ubuntu

# ========== Setup Chrome Driver with Extra Options ==========
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--headless")  # Run headless in CI environments
chrome_options.add_argument("--remote-debugging-port=9222")

# Force undetected_chromedriver to use ChromeDriver for Chrome version 133
driver = uc.Chrome(options=chrome_options, version_main=133)
driver.get(ERP_URL)
time.sleep(3)  # Allow page to load

# ========== LOGIN PROCESS ==========
try:
    # Locate the username field (try both possible IDs)
    try:
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txt_username"))
        )
    except Exception:
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txtusername"))
        )

    # Locate the password field (try both possible IDs)
    try:
        password_field = driver.find_element(By.ID, "txt_password")
    except Exception:
        password_field = driver.find_element(By.ID, "txtpassword")

    print("✅ Username & Password fields found.")

    # Enter credentials
    username_field.send_keys(ROLL_NUMBER)
    password_field.send_keys(PASSWORD)

    # ------------------- CAPTCHA HANDLING -------------------
    captcha_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "captchaCanvas"))
    )
    captcha_element.screenshot("captcha.png")

    def process_captcha(image_path):
        img = Image.open(image_path).convert("L")  # Convert to grayscale
        img = img.filter(ImageFilter.MedianFilter())  # Reduce noise
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)  # Increase contrast
        img.save("processed_captcha.png")  # Optional: save processed image for debugging
        return pytesseract.image_to_string(img, config="--psm 6").strip()

    captcha_text = process_captcha("captcha.png")
    print("🔍 Captcha Text:", captcha_text)

    captcha_input = driver.find_element(By.ID, "txtcaptcha")
    captcha_input.send_keys(captcha_text)

    login_button = driver.find_element(By.ID, "btnLogin")
    login_button.click()
    print("🔄 Attempting Login...")
    time.sleep(5)

    # ========== CHECK LOGIN STATUS ==========
    current_url = driver.current_url
    if "login" in current_url.lower():
        login_status = "❌ ERP Login Failed!"
    else:
        login_status = "✅ ERP Login Successful!"
    print(login_status)

except Exception as e:
    login_status = "❌ Error during login: " + str(e)
    print(login_status)

# ========== SEND TELEGRAM NOTIFICATION (Login Status) ==========
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, json=payload)
    print("Telegram API response:", response.status_code, response.text)

send_telegram_message(login_status)

# ========== POST-LOGIN ACTIONS ==========
if "Successful" in login_status:
    # 1. Close Notice/News Popup if present
    try:
        notice_modal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "noticemodal"))
        )
        close_button = notice_modal.find_element(By.XPATH, ".//button[@class='close']")
        close_button.click()
        print("✅ Notice popup closed.")
    except Exception as e:
        print("ℹ No notice popup found or already closed.")

    # 2. Click the LMS button
    try:
        lms_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@onclick, \"__doPostBack('ctl00$mainMenu','6')\") and contains(text(),'LMS')]"))
        )
        lms_button.click()
        print("🔄 LMS button clicked.")
        time.sleep(2)
    except Exception as e:
        print("❌ LMS button not found:", e)

    # 3. Click the Transactions option from the LMS dropdown
    try:
        transaction_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Transactions')]"))
        )
        transaction_option.click()
        print("🔄 Transactions option clicked.")
        time.sleep(3)
    except Exception as e:
        print("❌ Transactions option not found:", e)

    # 4. Click the bell icon (notification icon) on the right
    try:
        bell_icon = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_imgNotify"))
        )
        bell_icon.click()
        print("🔔 Bell icon clicked.")
        time.sleep(3)
    except Exception as e:
        print("❌ Bell icon not found:", e)

    # 5. Scroll down further to reveal the assignment table
    driver.execute_script("window.scrollBy(0, 600);")
    time.sleep(5)

    # 6. Check for the assignments table using the correct ID "DataTables_Table_0"
    try:
        # Wait for the table to be present
        assignment_table = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "DataTables_Table_0"))
        )
        rows = assignment_table.find_elements(By.CSS_SELECTOR, "tbody tr")
        print("Found", len(rows), "rows in the assignment table.")
        if not rows or len(rows) == 0:
            assignment_message = "ℹ You don't have any Assignment to upload."
        elif len(rows) == 1 and "you don't have any assignment" in rows[0].text.lower():
            assignment_message = "ℹ You don't have any Assignment to upload."
        else:
            row_texts = [" ".join(row.text.split()) for row in rows if row.text.strip()]
            assignment_message = "📢 You have assignments to upload:\n" + "\n".join(row_texts)
        print("Assignment Check:", assignment_message)
        send_telegram_message(assignment_message)
    except Exception as e:
        error_message = "❌ Error checking assignments: " + str(e)
        print(error_message)
        # Optional: Debug by printing a snippet of the page source
        page_snippet = driver.page_source[:1000]
        print("Page source snippet:", page_snippet)
        send_telegram_message(error_message)

# ========== FINISH ==========
try:
    input("Press Enter to exit and close the browser...")
except EOFError:
    pass
driver.quit()
