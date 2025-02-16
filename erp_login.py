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

# ========== ERP URL ==========
ERP_URL = "https://jecrc.mastersofterp.in/iitmsv4eGq0RuNHb0G5WbhLmTKLmTO7YBcJ4RHuXxCNPvuIw=?enc=EGbCGWnlHNJ/WdgJnKH8DA=="

# ========== Tesseract Path ==========
# For local Windows, use:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# For GitHub Actions (Ubuntu), Tesseract is usually at /usr/bin/tesseract.
# You can set this in your workflow environment if needed.
# For now, we'll assume local Windows environment:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ========== Setup Chrome Driver ==========
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
# Uncomment the next line if you want to see the browser window (non-headless):
# chrome_options.add_argument("--headless")
driver = uc.Chrome(options=chrome_options)
driver.get(ERP_URL)
time.sleep(3)  # Allow page to load

# ========== LOGIN PROCESS ==========
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
try:
    captcha_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "captchaCanvas"))
    )
    captcha_element.screenshot("captcha.png")

    def process_captcha(image_path):
        img = Image.open(image_path).convert("L")  # Convert to grayscale
        img = img.filter(ImageFilter.MedianFilter())  # Reduce noise
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)  # Increase contrast
        # Save processed image for debugging (optional)
        img.save("processed_captcha.png")
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

    # 5. Scroll down a bit to reveal the assignment list section
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(2)

    # 6. Check for the "Assignments List" section and decide message
    try:
        assignments_elements = driver.find_elements(By.XPATH, "//div[@class='sub-heading']/h5[contains(text(),'Assignments List')]")
        if assignments_elements and len(assignments_elements) > 0:
            assignment_container = assignments_elements[0].find_element(By.XPATH, "./ancestor::div[1]")
            assignment_text = assignment_container.text.strip()
            print("DEBUG: Full assignment container text:", assignment_text)
            # Normalize the text and check if it indicates no assignments
            normalized_text = " ".join(assignment_text.lower().split())
            if "you don't have any assignment" in normalized_text or "no assignment" in normalized_text:
                assignment_message = "ℹ You don't have any Assignment to upload."
            else:
                assignment_message = "📢 You have assignments to upload:\n" + assignment_text
            print("Assignment Check:", assignment_message)
            send_telegram_message(assignment_message)
        else:
            no_assignment_message = "ℹ No assignment list section found."
            print(no_assignment_message)
            send_telegram_message(no_assignment_message)
    except Exception as e:
        error_message = "❌ Error checking assignments: " + str(e)
        print(error_message)
        send_telegram_message(error_message)

# ========== KEEP BROWSER OPEN FOR DEBUGGING ==========
input("Press Enter to exit and close the browser...")
driver.quit()
