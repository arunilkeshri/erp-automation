# ERP Automation 🔐📚

## 🚀 About the Project

**ERP Automation** was built out of the constant struggle of logging into college ERP systems just to check if there are any assignments or updates.  
So, as a student tired of doing the same clicks daily, I made a Python bot that automates the whole process — from login to notification. Yep, even the CAPTCHA is handled!

---

## 🧠 What It Does

This script:
- 🧩 Logs into your college ERP system
- 🔓 Automatically solves CAPTCHA using OCR (Tesseract)
- 🧭 Navigates through ERP menus
- 📋 Extracts assignment data
- 📩 Sends Telegram messages with assignment info
- 📆 Runs **daily** using **GitHub Actions**, so you never miss an update

---

## ⚙️ Built With

- 🐍 Python  
- 🌐 Selenium + undetected-chromedriver  
- 👁️ Tesseract OCR  
- 📲 Telegram Bot API  
- 🛠️ GitHub Actions (for scheduling daily checks)

---

## 💼 Why I Made This

> As a student, I just wanted to avoid opening ERP every morning and still stay updated.  
> This bot became my silent assistant, doing it all in the background.

No more missed assignments. No more “Oh, I didn’t see it”. Just clean, daily updates on Telegram.

---

## 💻 How It Works

1. **Login Automation:** Username + password filled in → CAPTCHA cracked via OCR → Login complete.
2. **ERP Navigation:** The bot finds its way to the assignments section automatically.
3. **Data Extraction:** Pulls assignment details and checks for new content.
4. **Telegram Notification:** Sends a neat message to your phone if anything new pops up.
5. **Scheduled Runs:** It’s hooked to GitHub Actions for daily execution — totally hands-free.

---

## 🔐 Security & Config

- All credentials are handled securely via **GitHub Secrets**  
- Uses environment variables so your personal data is never exposed

---

## 🙋‍♂️ Made by

👨‍💻 **Arunil Keshri**  
🎓 B.Tech (CSE) student  
📬 [Connect on LinkedIn](https://www.linkedin.com/in/arunil-keshri-9bb36625a/)

> "This bot does my ERP work, so I can focus on what really matters — learning, growing, and sometimes... sleeping."

---

## 📄 License

Open to all. Modify, fork, contribute — just mention the original work 😊

---
