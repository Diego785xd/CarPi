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
from st_rtsp_main import RTSPVideoStream
import cv2

st.set_page_config(layout="wide")
ICON_HEIGHT     = 6       # em units for button height
EMOGI_SIZE      = 30       # px for emoji font-size
FONT_SIZE       = 1.5        # rem for label font-size
LABEL_SPACING   = 0  
AUTOREFRESH_INTERVAL = 5000  # ms for auto-refresh interval

# Auto-refresh every 5 seconds (5000 ms)
#st_autorefresh(interval=AUTOREFRESH_INTERVAL, limit=None, key="refresh")
hide_all_buttons()

# --- inject common.css ---
css_path = pathlib.Path(__file__).parents[1] / "styles" / "common.css"
css = css_path.read_text()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --- override gradient variables ---
SIDEBAR_BG_COLOR    = "#3d405b"  # page-specific sidebar color
BG_DEGREE   = "145deg"
BG_COLOR1   = "#e07a5f"
BG_PERCENT1 = "20%"
BG_COLOR2   = "#f4f1de"
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

# Initialize HOG descriptor for people detection
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

st.title("Webcam Live Feed")
run = st.checkbox('Run')
FRAME_WINDOW = st.image([])
camera = cv2.VideoCapture("rtsp://10.48.62.63:8554/unicast")

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

while run:
    ret, frame = camera.read()
    if not ret:
        break

    # Detect people
    rects, _ = hog.detectMultiScale(
        frame,
        winStride=(8, 8),
        padding=(8, 8),
        scale=1.05
    )
    # Draw bounding boxes around detected people
    for (x, y, w, h) in rects:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Convert to RGB for Streamlit
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    FRAME_WINDOW.image(frame_rgb)
else:
    st.write('Stopped')




