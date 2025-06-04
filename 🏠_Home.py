import streamlit as st
import time
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from utils import hide_all_buttons, switch_page
st.set_page_config(page_title="AutoOS", layout="wide",initial_sidebar_state=st.session_state.setdefault("sidebar_state","collapsed"))
USER_NAME = "Diego"
GENDER = "MALE"

st_autorefresh(interval=5000, key="auto_timer")



st.markdown(
    """
    <style>


      header[data-testid="stHeader"],
      .stAppHeader {
        display: none !important;
      }

      /* 2) Hide MainMenu & footer */
      #MainMenu { visibility: hidden !important; }
      footer     { visibility: hidden !important; }

      /* 3) Hide both old & new deploy buttons */
      .stDeployButton,
      .stAppDeployButton {
        display: none !important;
      }

      /* 4) (Optional) Hide the run/stop/share toolbar entirely */
      [data-testid="stStatusWidget"] {
        visibility: hidden !important;
      }

      /* 5) Your layout tweaks */
      .block-container {
        padding-top: 0rem !important;
      }
      .block-container h1 {
        margin-top: 0 !important;
        padding-top: 0 !important;
      }
      [data-testid="stAppViewContainer"] {
        background: linear-gradient(145deg, #1446A0 5%, #C1EEFF 100%) !important;
      }
      a, a:visited {
        color: white !important;
        text-decoration: none !important;
        cursor: pointer;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

hour = time.localtime().tm_hour
if hour < 12:
  greeting, emoji = "Good morning", "☀️"
elif hour < 18:
  greeting, emoji = "Good afternoon", "🌤️"
else:
  greeting, emoji = "Good night", "🌙"

welcome_message = f"{greeting}, {USER_NAME}! {emoji}"


hide_all_buttons()

st.markdown(
    """
    <style>
    /* hide the header “back” button but leave it in the DOM */
    button[data-testid="stBaseButton-headerNoPadding"][kind="headerNoPadding"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# right before your cols = st.columns(5)
current_time = time.strftime("%H:%M", time.localtime())
st.markdown(
  f"""
  <div style="
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  ">
    <span style="
      font-size: 1.5rem;
      color: white;
      font-weight: bold;
      margin: 0;
    ">{welcome_message}</span>
    <span style="
      font-size: 1.5rem;
      color: white;
      margin: 0;
    ">{current_time}</span>
  </div>
  """,
  unsafe_allow_html=True,
)

ICON_HEIGHT     = 10       # em units for button height
EMOGI_SIZE      = 60       # px for emoji font-size
FONT_SIZE       = 1.5        # rem for label font-size
LABEL_SPACING   = 0      # rem between emoji and label

st.markdown(
  f"""
  <style>
    /* —— Shared button styles —— */
    .element-container button[kind="tertiary"] {{
    height: {ICON_HEIGHT}em;
    width: 100% !important;
    background: rgba(255,255,255,0.2) !important;
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    margin-bottom: 1rem !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    }}
    .element-container button > div {{
    display: none !important;  /* hide default label */
    }}

    /* —— Spotify button —— */
    .element-container.st-key-spotify button::before {{
    content: "🎵";
    font-size: {EMOGI_SIZE}px;
    }}
    .element-container.st-key-spotify button::after {{
    content: "Spotify";
    margin-top: {LABEL_SPACING}rem;
    font-size: {FONT_SIZE}rem;
    color: white !important;
    }}

    /* —— Maps button —— */
    .element-container.st-key-maps button::before {{
    content: "🗺️";
    font-size: {EMOGI_SIZE}px;
    }}
    .element-container.st-key-maps button::after {{
    content: "Maps";
    margin-top: {LABEL_SPACING}rem;
    font-size: {FONT_SIZE}rem;
    color: white !important;
    }}

    /* —— Weather button —— */
    .element-container.st-key-weather button::before {{
    content: "☀️";
    font-size: {EMOGI_SIZE}px;
    }}
    .element-container.st-key-weather button::after {{
    content: "Weather";
    margin-top: {LABEL_SPACING}rem;
    font-size: {FONT_SIZE}rem;
    color: white !important;
    }}

    /* —— Camera button —— */
    .element-container.st-key-camera button::before {{
    content: "📷";
    font-size: {EMOGI_SIZE}px;
    }}
    .element-container.st-key-camera button::after {{
    content: "Camera";
    margin-top: {LABEL_SPACING}rem;
    font-size: {FONT_SIZE}rem;
    color: white !important;
    }}

    /* —— Mail button —— */
    .element-container.st-key-mail button::before {{
    content: "📨";
    font-size: {EMOGI_SIZE}px;
    }}
    .element-container.st-key-mail button::after {{
    content: "Mail";
    margin-top: {LABEL_SPACING}rem;
    font-size: {FONT_SIZE}rem;
    color: white !important;
    }}

    /* —— Calendar button —— */
    .element-container.st-key-calendar button::before {{
    content: "📅";
    font-size: {EMOGI_SIZE}px;
    }}
    .element-container.st-key-calendar button::after {{
    content: "Calendar";
    margin-top: {LABEL_SPACING}rem;
    font-size: {FONT_SIZE}rem;
    color: white !important;
    }}
  </style>
  """,
  unsafe_allow_html=True,
)
# First row of 3 frosted columns
cols = st.columns(3)

for idx, col in enumerate(cols):
  with col:
    if idx == 0:
      if st.button("Spotify", key="spotify", use_container_width=True, type="tertiary"):
        switch_page("Spotify")
    elif idx == 1:
      if st.button("Maps", key="maps", use_container_width=True, type="tertiary"):
        switch_page("Maps")
    elif idx == 2:
      if st.button("Weather", key="weather", use_container_width=True, type="tertiary"):
        switch_page("Weather")

# Second row of 3 new frosted columns
cols_inf = st.columns(3)

for idx, col in enumerate(cols_inf):
  with col:
    if idx == 0:
      if st.button("Camera", key="camera", use_container_width=True, type="tertiary"):
        switch_page("Camera")
    elif idx == 1:
      if st.button("Mail", key="mail", use_container_width=True, type="tertiary"):
        switch_page("Mail")
    elif idx == 2:
      if st.button("Calendar", key="calendar", use_container_width=True, type="tertiary"):
        switch_page("Calendar")

