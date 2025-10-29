# ============================================
# 🎓 JECRC ERP LMS → Assignment Auto Fetcher
# (Updated October 2025)
# ============================================

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests

# --------------------------------------------
# CONFIG
# --------------------------------------------
ERP_URL = "https://jecrcuniversity.edu.in/ERP"  # replace if different
USERNAME = "YOUR_ERP_USERNAME"
PASSWORD = "YOUR_ERP_PASSWORD"

TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# --------------------------------------------
# SETUP DRIVER
# --------------------------------------------
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# --------------------------------------------
# LOGIN
# --------------------------------------------
print("Opening ERP...")
driver.get(ERP_URL)

try:
    # Fill username & password
    wait.until(EC.presence_of_element_located((By.ID, "txtUserName"))).send_keys(USERNAME)
    driver.find_element(By.ID, "txtPassword").send_keys(PASSWORD)
    driver.find_element(By.ID, "btnLogin").click()
    print("Login successful ✅")
except Exception as e:
    print("⚠️ Login error:", e)
    driver.quit()
    exit()

time.sleep(3)

# --------------------------------------------
# STEP 1: Handle Notice Popup (if present)
# --------------------------------------------
try:
    print("Checking for notice popup...")
    notice_close = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "#noticemodal > div > div > div.modal-header > button > span")
    ))
    driver.execute_script("arguments[0].click();", notice_close)
    print("Notice popup closed ✅")
except:
    print("No notice popup found, continuing...")

# --------------------------------------------
# STEP 2: Click LMS
# --------------------------------------------
try:
    print("Clicking LMS...")
    lms_menu = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "#ctl00_mainMenu > ul > li:nth-child(3) > a")
    ))
    driver.execute_script("arguments[0].click();", lms_menu)
    print("LMS opened ✅")
    time.sleep(2)
except Exception as e:
    print("⚠️ Error clicking LMS:", e)

# --------------------------------------------
# STEP 3: Click Transaction under LMS
# --------------------------------------------
try:
    print("Opening Transactions...")
    trans_link = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "#ctl00_mainMenu\\:submenu\\:9 > li:nth-child(1) > a")
    ))
    driver.execute_script("arguments[0].click();", trans_link)
    print("Transactions opened ✅")
    time.sleep(3)
except Exception as e:
    print("⚠️ Error opening Transactions:", e)

# --------------------------------------------
# STEP 4: Click Bell Icon
# --------------------------------------------
try:
    print("Clicking bell icon...")
    bell = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_imgNotify")
    ))
    driver.execute_script("arguments[0].click();", bell)
    print("Bell icon clicked 🔔")
    time.sleep(2)
except Exception as e:
    print("⚠️ Bell icon not found or already clicked:", e)

# --------------------------------------------
# STEP 5: Scroll to Assignment Section
# --------------------------------------------
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(3)

# --------------------------------------------
# STEP 6: Extract Assignment Table
# --------------------------------------------
assignments = ""
try:
    print("Extracting assignments...")
    table = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "#DataTables_Table_0")
    ))
    assignments = table.text.strip()
    print("Assignments found ✅\n")
    print(assignments)
except:
    assignments = "❌ You don't have any assignments currently."
    print(assignments)

# --------------------------------------------
# STEP 7: Send to Telegram
# --------------------------------------------
try:
    print("Sending to Telegram...")
    message = f"📘 *JECRC ERP Assignments*\n\n{assignments}"
    send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.get(send_url, params=params)
    print("Assignments sent to Telegram ✅")
except Exception as e:
    print("⚠️ Telegram sending failed:", e)

# --------------------------------------------
# (Optional) Quit browser
# --------------------------------------------
time.sleep(2)
driver.quit()
print("Done ✅")
