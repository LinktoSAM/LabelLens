import re
import asyncio
import smtplib
from email.mime.text import MIMEText
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from telegram import Bot

# Import prompts from prompts.py
from prompts import WELCOME_MESSAGE_TEMPLATE, LABEL_LENS_SYSTEM_PROMPT, EXPORT_SUMMARY_PROMPT
import smtplib
import ssl
from email.mime.text import MIMEText

def send_email(to_address, subject, body):
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = GMAIL_ADDRESS
    message["To"] = to_address

    # macOS Fix: Create an unverified SSL context to bypass local certificate missing errors
    context = ssl._create_unverified_context()

    try:
        # Use Port 465 with the unverified context
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=15) as server:
            server.set_debuglevel(1)  # <--- This prints the exact network traffic to your terminal
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(message)
    except Exception as e:
        print(f"\n--- SMTP CRASH LOG ---\n{e}\n----------------------\n")
        raise e
# Allowed major email providers
ALLOWED_DOMAINS = ["gmail.com", "yahoo.com", "icloud.com", "outlook.com", "hotmail.com"]

def validate_email(email: str) -> tuple[bool, str]:
    email = email.strip().lower()
    pattern = r"^[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$"
    match = re.match(pattern, email)
    if not match:
        return False, "Please enter a valid email address (e.g., user@gmail.com)."
    
    domain = match.group(1)
    if domain not in ALLOWED_DOMAINS:
        allowed_str = ", ".join([f"@{d}" for d in ALLOWED_DOMAINS])
        return False, f"Temporary or unsupported email domain. Please use one of: {allowed_str}."
    
    return True, ""

# --- APP SETUP ---
st.set_page_config(page_title="LabelLens", page_icon="🔍")

# Cache the client so HTTP connections remain open across Streamlit script reruns
@st.cache_resource
def get_gemini_client(api_key: str):
    return genai.Client(api_key=api_key)

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = get_gemini_client(api_key)
except KeyError:
    st.error("Please add your GEMINI_API_KEY to .streamlit/secrets.toml")
    st.stop()

# Telegram Setup
TELEGRAM_BOT_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "")

def send_telegram(chat_id, text):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    asyncio.run(bot.send_message(chat_id=chat_id, text=text))

# Email Setup
GMAIL_ADDRESS = st.secrets.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = st.secrets.get("GMAIL_APP_PASSWORD", "")

def send_email(to_address, subject, body):
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = GMAIL_ADDRESS
    message["To"] = to_address

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(message)

# Initialize Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE_TEMPLATE}]
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "image_analyzed" not in st.session_state:
    st.session_state.image_analyzed = False

# --- LANDING PAGE ---
if not st.session_state.logged_in:
    st.title("Welcome to LabelLens 🔍")
    st.write("Please enter your details to get started.")
    
    with st.form("login_form"):
        user_name = st.text_input("Name")
        user_email = st.text_input("Email ID", placeholder="example@gmail.com")
        submitted = st.form_submit_button("Start Inspecting")
        
        if submitted:
            if not user_name.strip():
                st.error("Please enter your Name.")
            else:
                is_valid, err_msg = validate_email(user_email)
                if not is_valid:
                    st.error(err_msg)
                else:
                    st.session_state.user_name = user_name.strip()
                    st.session_state.user_email = user_email.strip().lower()
                    st.session_state.logged_in = True
                    st.rerun()
                
    st.stop()

# --- MAIN APP UI ---
st.title(f"🔍 LabelLens - Welcome, {st.session_state.user_name}!")

# --- SIDEBAR: USER PROFILE & ACTIONS ---
with st.sidebar:
    st.header("👤 Your Profile")
    st.caption(f"Logged in as: **{st.session_state.user_email}**")
    
    common_restrictions = st.multiselect(
        "Common Restrictions & Allergies",
        options=["Vegan", "Vegetarian", "Gluten-Free", "Dairy-Free", "Peanut Allergy", "Tree Nut Allergy", "No Added Sugar", "Keto"],
    )
    
    other_preferences = st.text_area(
        "Other Restrictions/Preferences", 
        placeholder="e.g., Avoid microplastics, non-comedogenic..."
    )
    
    user_preferences = f"Selected common restrictions: {', '.join(common_restrictions)}. Other specific preferences: {other_preferences}"
    
    st.divider()
    
    st.header("📤 Export Action")
    
    telegram_chat_id = st.text_input(
        "Telegram Chat ID", 
        placeholder="e.g., 123456789", 
        help="Message your bot first, then get your Chat ID from @userinfobot"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        send_email_btn = st.button("Email", use_container_width=True)
    with col2:
        send_telegram_btn = st.button("Telegram", use_container_width=True)

    if send_email_btn or send_telegram_btn:
        if not st.session_state.chat_session:
            st.warning("Analyze a label first before exporting!")
        elif send_telegram_btn and not TELEGRAM_BOT_TOKEN:
            st.error("TELEGRAM_BOT_TOKEN is missing")
        elif send_telegram_btn and not telegram_chat_id.strip():
            st.warning("Please enter your Telegram Chat ID above.")
        elif send_email_btn and (not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD):
            st.error("GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing ")
        else:
            target_type = "Telegram" if send_telegram_btn else "Email"
            
            with st.spinner(f"Drafting and sending summary for {target_type}..."):
                response = st.session_state.chat_session.send_message(EXPORT_SUMMARY_PROMPT)
                
                if send_telegram_btn:
                    try:
                        send_telegram(telegram_chat_id.strip(), response.text)
                        st.success("Summary successfully sent via Telegram!")
                    except Exception as e:
                        st.error(f"Failed to send Telegram message: {e}")
                
                elif send_email_btn:
                    try:
                        send_email(
                            to_address=st.session_state.user_email,
                            subject="LabelLens Safety Summary",
                            body=response.text
                        )
                        st.success(f"Summary successfully sent to {st.session_state.user_email}!")
                    except Exception as e:
                        st.error(f"Failed to send email: {e}")

# --- MAIN UI: UPLOAD & CHAT ---
uploaded_file = st.file_uploader(
    "Upload an ingredient label", 
    type=["jpg", "jpeg", "png"],
    max_upload_size=100
)

if uploaded_file and not st.session_state.image_analyzed:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Label", use_container_width=True)
    
    if st.button("Analyze Label"):
        if not common_restrictions and not other_preferences.strip():
            st.warning("Please enter your dietary preferences in the sidebar first!")
        else:
            with st.spinner("Inspecting ingredients..."):
                system_instruction = LABEL_LENS_SYSTEM_PROMPT.format(user_preferences=user_preferences)
                
                st.session_state.chat_session = client.chats.create(
                    model="gemini-3.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                    )
                )
                
                initial_prompt = "Please analyze this label based on my profile."
                response = st.session_state.chat_session.send_message([image, initial_prompt])
                
                st.session_state.messages.append({"role": "user", "content": "*(Uploaded a label image)*"})
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.session_state.image_analyzed = True
                st.rerun()

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input Box for Follow-up Questions
if prompt := st.chat_input("Ask a follow-up question..."):
    if not st.session_state.chat_session:
        st.warning("Please upload and analyze a label first!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.spinner("Thinking..."):
            response = st.session_state.chat_session.send_message(prompt)
            
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        with st.chat_message("assistant"):
            st.markdown(response.text)