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
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# ========== Setup Chrome Driver ==========
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--remote-debugging-port=9222")

driver = uc.Chrome(options=chrome_options)
driver.get(ERP_URL)
time.sleep(3)

# ========== LOGIN PROCESS ==========
try:
    # Locate username field
    try:
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txt_username"))
        )
    except Exception:
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "txtusername"))
        )

    # Locate password field
    try:
        password_field = driver.find_element(By.ID, "txt_password")
    except Exception:
        password_field = driver.find_element(By.ID, "txtpassword")

    username_field.send_keys(ROLL_NUMBER)
    password_field.send_keys(PASSWORD)

    # CAPTCHA handling
    captcha_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "captchaCanvas"))
    captcha_element.screenshot("captcha.png")

    def process_captcha(image_path):
        img = Image.open(image_path).convert("L")
        img = img.filter(ImageFilter.MedianFilter())
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)
        return pytesseract.image_to_string(img, config="--psm 6").strip()

    captcha_text = process_captcha("captcha.png")
    captcha_input = driver.find_element(By.ID, "txtcaptcha")
    captcha_input.send_keys(captcha_text)

    login_button = driver.find_element(By.ID, "btnLogin")
    login_button.click()
    time.sleep(5)

    current_url = driver.current_url
    login_status = "✅ ERP Login Successful!" if "login" not in current_url.lower() else "❌ ERP Login Failed!"
    print(login_status)

except Exception as e:
    login_status = f"❌ Error during login: {str(e)}"
    print(login_status)

# ========== SEND TELEGRAM NOTIFICATION ==========
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

send_telegram_message(login_status)

# ========== ASSIGNMENT CHECKING LOGIC ==========
if "Successful" in login_status:
    try:
        # Close notice popup if exists
        try:
            notice_modal = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "noticemodal"))
            notice_modal.find_element(By.XPATH, ".//button[@class='close']").click()
        except Exception:
            pass

        # Navigate to assignments
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'LMS')]"))).click()
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Transactions')]"))).click()
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_imgNotify"))).click()
        
        time.sleep(3)
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(2)

        # Check for assignments table
        assignment_message = ""
        try:
            # Check if "no assignments" message exists
            no_assign_element = driver.find_elements(By.XPATH, "//p[contains(., 'don't have any Assignment')]")
            if no_assign_element:
                assignment_message = "ℹ You don't have any Assignment to upload."
            else:
                # Check table existence and content
                table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[@id='DataTables_Table_1']"))
                )
                rows = table.find_elements(By.XPATH, ".//tbody/tr")
                
                if len(rows) > 0:
                    assignments = []
                    for row in rows:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        if len(cols) >= 3:
                            assignments.append(
                                f"📚 {cols[0].text} | {cols[1].text} | Due: {cols[2].text}"
                            )
                    assignment_message = "📢 You have assignments to upload:\n" + "\n".join(assignments)
                else:
                    assignment_message = "ℹ No assignments found in table."
        except Exception as e:
            assignment_message = f"❌ Error checking assignments: {str(e)}"
        
        print("Assignment Check:", assignment_message)
        send_telegram_message(assignment_message)

    except Exception as e:
        error_message = f"❌ Navigation error: {str(e)}"
        print(error_message)
        send_telegram_message(error_message)

# ========== CLEANUP ==========
try:
    input("Press Enter to exit...")
except EOFError:
    pass
driver.quit()
