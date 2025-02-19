**ERP Assignment Tracker**

A Python & Selenium-based automation script that logs into the JECRC ERP portal, checks for new assignments, and sends notifications via Telegram at scheduled times.

**1. Project Overview**

Problem Statement
Manually checking the JECRC ERP portal for new assignments was inefficient:

Required logging in multiple times a day.
No notifications, increasing the chances of missing deadlines.
Tedious navigation through multiple menus.
Solution
This script automates the process by:

Logging into the ERP portal using Selenium.
Extracting assignment details from the system.
Sending notifications via Telegram at 11 AM, 2 PM, and 8 PM IST.
Running automatically through GitHub Actions, eliminating manual checks.

**2. Installation & Setup**

Prerequisites
Python 3.11+
Google Chrome installed
Chrome WebDriver (compatible with your Chrome version)
A Telegram bot (to send notifications)
Steps to Install & Run Locally
Step 1: Clone the Repository
sh
Copy
Edit
git clone https://github.com/your-username/erp-assignment-tracker.git  
cd erp-assignment-tracker  
Step 2: Install Dependencies
sh
Copy
Edit
pip install -r requirements.txt  
Step 3: Run the Script Manually
sh
Copy
Edit
python erp_login.py  
Automating Execution with GitHub Actions
This script is scheduled to run automatically at:

11:00 AM IST
2:00 PM IST
8:00 PM IST
To trigger it manually, go to GitHub Actions → Run Workflow.

**3. How It Works**

The script logs into the JECRC ERP portal using the provided credentials.
It navigates to the assignment section and extracts data.
If new assignments are found, a Telegram notification is sent with details.
If no assignments are available, a message stating "No assignments to upload" is sent.
Example Telegram Messages
✅ When assignments are found:
css
Copy
Edit
You have assignments to upload:
Assignment 2 - COMPILER CONSTRUCTION - 17-Feb-2025  
Assignment 1 - COMPILER CONSTRUCTION - 17-Feb-2025  
❌ When no assignments are found:
vbnet
Copy
Edit
You don't have any Assignment to upload.

**4. Technical Details**

Project Structure
bash
Copy
Edit
📁 ERP-Automation/
│── 📄 erp_login.py         # Main automation script  
│── 📄 requirements.txt     # Python dependencies  
│── 📄 README.md            # Project documentation  
│── 📄 .github/workflows/erp.yml  # GitHub Actions workflow  
Key Technologies Used
Python – Core scripting language
Selenium – Automating browser interactions
Tesseract OCR – Solving CAPTCHA
GitHub Actions – Automating scheduled execution
Telegram Bot API – Sending notifications

**5. Challenges & Solutions**

  1. CAPTCHA Blocking Login

Problem: The ERP system requires CAPTCHA verification, making automation difficult.
Solution: Integrated Tesseract OCR to dynamically extract and solve the CAPTCHA.

  2. Pop-ups & Slow Page Loading

Problem: Unexpected pop-ups and slow loading affected navigation.
Solution: Used WebDriverWait to handle delays and close pop-ups dynamically.

  3. Assignments Table Not Always Visible

Problem: The table sometimes didn’t load, causing errors.
Solution:

If no table is found → Assume no assignments and send a message.
If a table is found but contains only one row stating ‘No Assignments’ → Send a message indicating no assignments.
If assignments exist → Extract and send details via Telegram.

  4. Telegram Notification Setup

Problem: Ensuring secure communication with Telegram API.
Solution: Used GitHub Secrets to store the API token securely, preventing exposure.

**6.Future Improvements**

  a Enhance CAPTCHA solving with AI-based OCR models.
  
  b  Integrate WhatsApp notifications as an alternative to Telegram.
  
  c Develop a GUI version for user-friendly interaction.
