# 🔍 LabelLens

LabelLens is an AI-powered consumer safety analyst and ingredient inspector. By leveraging Google's Gemini Vision API, the app allows users to upload photos of food, supplement, or cosmetic labels and instantly cross-reference the ingredients against their personal dietary restrictions, allergies, and lifestyle preferences.

## ✨ Features
* **Visual Ingredient Analysis:** Upload any photo of a nutrition label or ingredient list.
* **Personalized Health Profiles:** Filter results based on common restrictions (Vegan, Gluten-Free, Keto, Peanut Allergy) and custom preferences (e.g., "avoid microplastics", "non-comedogenic").
* **Sneaky Ingredient Detection:** Identifies hidden allergens and demystifies complex chemical names into simple terms.
* **Interactive Chat:** Ask follow-up questions about specific ingredients directly in the app.
* **Instant Export:** Generate a concise safety summary and export it instantly via **Email** or a custom **Telegram Bot**.

## 🛠️ Tech Stack
* **Frontend/Framework:** [Streamlit](https://streamlit.io/)
* **AI Model:** Google Gemini (`gemini-3.8-flash` / `1.5-flash`) via the `google-genai` SDK
* **Export Integrations:** Python `smtplib` (Gmail SMTP) & `python-telegram-bot`
* **Image Processing:** `Pillow` (PIL)

## 📋 Prerequisites
To run this app locally, you will need three free credentials:
1. **Gemini API Key:** Get one from [Google AI Studio](https://aistudio.google.com/).
2. **Gmail App Password:** Turn on 2-Step Verification for your Google account and generate a 16-letter App Password at `myaccount.google.com/apppasswords`.
3. **Telegram Bot Token:** Message `@BotFather` on Telegram and use the `/newbot` command.

## 💡 Usage
1.Open the local Streamlit URL in your browser.
2.Enter your Name and Email to log in.
3.Set your dietary preferences in the sidebar.
4.Upload a photo of an ingredient label and click Analyze Label.
5.Read the safety breakdown, ask follow-up questions, or export the summary to your Email or Telegram! 