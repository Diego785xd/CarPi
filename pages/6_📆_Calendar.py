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
import time
from asistente import *

st.set_page_config(layout="wide")
ICON_HEIGHT     = 6       # em units for button height
EMOGI_SIZE      = 30       # px for emoji font-size
FONT_SIZE       = 1.5        # rem for label font-size
LABEL_SPACING   = 0  
AUTOREFRESH_INTERVAL = 60000  # ms for auto-refresh interval

# Auto-refresh every 5 seconds (5000 ms)
st_autorefresh(interval=AUTOREFRESH_INTERVAL, limit=None, key="refresh")
hide_all_buttons()

# --- inject common.css ---
css_path = pathlib.Path(__file__).parents[1] / "styles" / "common.css"
css = css_path.read_text()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --- override gradient variables ---
SIDEBAR_BG_COLOR    = "#3E5641"  # page-specific sidebar color
BG_DEGREE   = "145deg"
BG_COLOR1   = "#83bca9"
BG_PERCENT1 = "20%" 
BG_COLOR2   = "#F2E9DC"
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

# Configuración de OAuth2
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'token.json'

# Load client config from secrets.toml
CLIENT_CONFIG = json.loads(st.secrets["calendar"]["file"])

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_credentials(creds)
            return creds
    return None

def save_credentials(creds):
    with open(CREDENTIALS_FILE, 'w') as token:
        token.write(creds.to_json())

def get_google_calendar_service():
    creds = load_credentials()
    if not creds:
        flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
        creds = flow.run_local_server(port=0)
        save_credentials(creds)
    return build('calendar', 'v3', credentials=creds)

def get_events_for_fullcalendar(service):
    now = _dt.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=50,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    formatted = []
    for ev in events_result.get('items', []):
        formatted.append({
            'title': ev.get('summary', 'Sin título'),
            'start': ev['start'].get('dateTime', ev['start'].get('date')),
            'color': '#FF9F89' if 'meet' in ev.get('summary','').lower() else '#2570A1'
        })
    return formatted



# --- Main Calendar UI --

# establish or reuse Calendar service
if 'service' not in st.session_state:
    try:
        st.session_state.service = get_google_calendar_service()
        st.success("✅ ¡Conectado a Google Calendar!")
    except Exception as e:
        st.error(f"❌ No se pudo conectar a Google Calendar: {e}")

if 'service' in st.session_state:
    events = get_events_for_fullcalendar(st.session_state.service)
    with st.expander("➕ Create new event"):
        title      = st.text_input("Title of the event")
        # separate date/time inputs
        start_date = st.date_input("Initial date")
        start_time = st.time_input("Initial time")
        end_date   = st.date_input("Final date")
        end_time   = st.time_input("Final time")
        if st.button("Crear evento", type="tertiary", key="create_event"):
            create_event(
                title, start_date, start_time,
                end_date, end_time,
                st.session_state.service
            )
            st.success("✅ Event Created.")
    calendario_html = f"""
    <!DOCTYPE html><html><head>
      <meta charset='utf-8' />
      <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css' rel='stylesheet' />
      <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js'></script>
      <style>#calendar{{height:80vh;width:100%;}}</style>
    </head><body>
      <div id='calendar'></div>
      <script>
        document.addEventListener('DOMContentLoaded', function() {{
          var cal = new FullCalendar.Calendar(document.getElementById('calendar'), {{
            initialView:'dayGridMonth',
            headerToolbar:{{left:'prev,next today',center:'title',right:'dayGridMonth,timeGridWeek,timeGridDay'}},
            events: {json.dumps(events)},
            editable:true,
            eventDrop:function(info){{ alert("Evento movido: "+info.event.title+" a "+info.event.start.toISOString()); }}
          }});
          cal.render();
        }});
      </script>
    </body></html>
    """
    st.components.v1.html(calendario_html, height=800)

# show assistant result if exists
if st.session_state.get("calendar_output"):
    st.write(st.session_state.calendar_output)

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

        # Assistant button
        if st.button("Assistant", key="assist", type="tertiary"):
            st.session_state.assist_pressed = True
            st.session_state.assist_time = time.time()
            json_obj = prompt(API_KEY, calendar_prompt(events))
            result = json_obj.get("res", "")
            func = json_obj.get("func", "")                     # { changed code }
            args = json_obj.get("args", {}) 
            args["service"] = st.session_state.service 
            if func == "create_event":
                create_event(**args)
            #st.session_state.calendar_output = result
            st.rerun()

# reset assistant flag after 5 seconds
if st.session_state.get("assist_pressed") and (time.time() - st.session_state.get("assist_time", 0)) > 5:
    st.session_state.assist_pressed = False
    st.session_state.assist_time = 0
    st.rerun()


