# ERP Automation

ERP Automation is a Python project developed as part of a student initiative to streamline routine tasks in an ERP system. The project automatically logs in to the ERP portal, handles CAPTCHA verification using OCR, navigates through the menus, extracts assignment details, and sends notifications via Telegram.

## Description

This project leverages Selenium with undetected-chromedriver, Tesseract OCR, and the Telegram Bot API to automate tedious tasks within an ERP system. It is designed to:
- **Automate Login:** Fill in credentials, solve CAPTCHA, and log into the ERP portal.
- **Navigate Menus:** Automatically traverse through the ERP interface to reach the assignments section.
- **Extract Assignment Data:** Scrape assignment details and determine if there are any new updates.
- **Send Notifications:** Notify users via Telegram about successful logins and assignment status.

ERP Automation is scheduled to run daily using GitHub Actions, ensuring that the latest assignment details are always at your fingertips.

## Features

- **Automated ERP Login:** Automatically enters credentials and solves CAPTCHA using OCR.
- **Web Navigation:** Efficiently navigates the ERP interface to access necessary sections.
- **Assignment Extraction:** Retrieves and sends assignment information via Telegram.
- **Scheduled Execution:** Integrated with GitHub Actions to run daily.
- **Customizable:** Easily configurable using environment variables and repository secrets.

## Technologies Used

- **Python**
- **Selenium & undetected-chromedriver**
- **Tesseract OCR**
- **Telegram Bot API**
- **GitHub Actions**
