import streamlit as st
from streamlit_autorefresh import st_autorefresh
from utils import hide_all_buttons, switch_page
import requests
from PIL import Image
import numpy as np
import io
from datetime import datetime
import pathlib
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import datetime as _dt
import json
import os
import base64
import re

st.set_page_config(layout="wide")
ICON_HEIGHT     = 6       # em units for button height
EMOGI_SIZE      = 30       # px for emoji font-size
FONT_SIZE       = 1.5        # rem for label font-size
LABEL_SPACING   = 0  
AUTOREFRESH_INTERVAL = 5000  # ms for auto-refresh interval

# Auto-refresh every 5 seconds (5000 ms)
st_autorefresh(interval=AUTOREFRESH_INTERVAL, limit=None, key="refresh")
hide_all_buttons()

# --- inject common.css ---
css_path = pathlib.Path(__file__).parents[1] / "styles" / "common.css"
css = css_path.read_text()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --- override gradient variables ---
SIDEBAR_BG_COLOR    = "#6461A0"  # page-specific sidebar color
BG_DEGREE   = "145deg"
BG_COLOR1   = "#03012C"
BG_PERCENT1 = "20%"
BG_COLOR2   = "#BCCCE0"
BG_PERCENT2 = "99%"

st.markdown(f"""
<style>
:root {{
  --bg-degree: {BG_DEGREE};
  --bg-color1: {BG_COLOR1};
  --bg-percent1: {BG_PERCENT1};
  --bg-color2: {BG_COLOR2};
  --bg-percent2: {BG_PERCENT2};
  --sidebar-bg-color: {SIDEBAR_BG_COLOR};
}}
</style>
""", unsafe_allow_html=True)

# Set page title
st.title("📨 Mail")

# Mail constants
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_FILE = 'token_gmail.json'

# Load Gmail client config from Streamlit secrets; stop if missing
try:
    secret_val = st.secrets["calendar"]["file"]
except KeyError:
    st.error("🚨 Gmail credentials missing. Please add a [calendar] section in .streamlit/secrets.toml.")
    st.stop()

if isinstance(secret_val, str):
    CLIENT_CONFIG = json.loads(secret_val)
elif isinstance(secret_val, dict):
    CLIENT_CONFIG = secret_val
else:
    st.error("🚨 Invalid format for Gmail credentials.")
    st.stop()

# Save credentials to disk
def save_credentials(creds):
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())

# Load saved credentials
def load_credentials():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token:
            return Credentials.from_authorized_user_info(json.load(token), SCOPES)
    return None

# Build Gmail service
def get_gmail_service():
    creds = load_credentials()
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use in‐memory client config instead of external file
            flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
            creds = flow.run_local_server(port=0)
        save_credentials(creds)
    return build('gmail', 'v1', credentials=creds)

# Strip HTML tags from email body
def clean_email_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Display a list of recent emails
def show_emails(service, max_results=10):
    try:
        results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    except Exception as e:
        st.error(f"Error al obtener correos: {str(e)}")
        return

    messages = results.get('messages', [])
    if not messages:
        st.warning("No se encontraron correos recientes")
        return

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name']=='Subject'), 'Sin asunto')
        sender = next((h['value'] for h in headers if h['name']=='From'), 'Desconocido')
        date = next((h['value'] for h in headers if h['name']=='Date'), 'Fecha desconocida')

        try:
            parts = msg['payload'].get('parts')
            data = parts[0]['body'].get('data') if parts else msg['payload']['body'].get('data','')
            text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            text = clean_email_text(text)
        except:
            text = "[No se pudo cargar el contenido]"

        with st.expander(f"{subject} - {sender}"):
            st.write(f"**De:** {sender}")
            st.write(f"**Fecha:** {date}")
            st.write(f"**Asunto:** {subject}")
            st.write("---")
            st.write(text[:500] + "..." if len(text)>500 else text)

# Main interface
if 'gmail_service' not in st.session_state:
    if st.button("Conectar con Gmail"):
        try:
            service = get_gmail_service()
            st.session_state.gmail_service = service
            st.success("✅ Conectado a Gmail")
            show_emails(service)
        except Exception as e:
            st.error(f"Error al conectar: {str(e)}")
else:
    show_emails(st.session_state.gmail_service)

with st.sidebar:
    # Display current time, centered at the top of the sidebar
    current_time = datetime.now().strftime("%H:%M")
    st.markdown(
        f"<div style='text-align:center; font-size:1.2rem; margin-bottom:1rem; color: white; font-weight: bold;'>{current_time}</div>",
        unsafe_allow_html=True
    )

    cols2 = st.columns([1, 2, 1])
    with cols2[1]:
        if st.button("Maps", key="maps", type="tertiary"):
            switch_page("Maps")
        if st.button("Calendar", key="calendar", type="tertiary"):
            switch_page("Calendar")
        if st.button("Weather", key="weather", type="tertiary"):
            switch_page("Weather")
        if st.button("Home", key="home", type="tertiary"):
            switch_page("Home")


