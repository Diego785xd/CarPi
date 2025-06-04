import openmeteo_requests
import streamlit as st
import pandas as pd
import requests_cache
from retry_requests import retry

# new imports for styling & sidebar
from streamlit_autorefresh import st_autorefresh
from utils import hide_all_buttons, switch_page
import pathlib
from datetime import datetime
import altair as alt
st.set_page_config(page_title="Weather Dashboard", layout="wide")
# --- config constants for styling & refresh ---
ICON_HEIGHT           = 6        # em
EMOGI_SIZE            = 30       # px
FONT_SIZE             = 1.5      # rem
LABEL_SPACING         = 0
AUTOREFRESH_INTERVAL  = 5000     # ms
SIDEBAR_BG_COLOR      = "#e65f13"  # page-specific sidebar color

BG_DEGREE             = "145deg"
BG_COLOR1             = "#ff7900"
BG_PERCENT1           = "45%"
BG_COLOR2             = "#ffb600"
BG_PERCENT2           = "99%"

# ─── styling & auto-refresh setup ───────────────────────────────────────────────
st_autorefresh(interval=AUTOREFRESH_INTERVAL, limit=None, key="weather_refresh")
hide_all_buttons()

# inject common.css
css_path = pathlib.Path(__file__).parents[1] / "styles" / "common.css"
css = css_path.read_text()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# override CSS vars
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

# replace previous Vega CSS with stronger selector
st.markdown("""
<style>
.stVegaLiteChart.vega-embed,
.stVegaLiteChart.vega-embed .chart-wrapper {
  background-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# ─── sidebar with current time & nav ───────────────────────────────────────────
with st.sidebar:
    current_time = datetime.now().strftime("%H:%M")
    st.markdown(
        f"<div style='text-align:center; font-size:1.2rem; margin-bottom:1rem; "
        f"color:white; font-weight:bold;'>{current_time}</div>",
        unsafe_allow_html=True
    )
    cols2 = st.columns([1,2,1])
    with cols2[1]:
        if st.button("Maps",     key="maps",     type="tertiary"): switch_page("Maps")
        if st.button("Calendar", key="calendar", type="tertiary"): switch_page("Calendar")
        if st.button("Weather",  key="weather",  type="tertiary"): switch_page("Weather")
        if st.button("Home",     key="home",     type="tertiary"): switch_page("Home")

# ─── 1. Setup Open-Meteo client with caching & retries ──────────────────────────
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# ─── 2. Fetch weather data ─────────────────────────────────────────────────────
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 19.5975,
    "longitude": -99.2271,
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation_probability",
        "uv_index",
    ],
    "current": [
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "rain",
        "precipitation",
    ],
    "timezone": "auto",
    "forecast_days": 1,
}
responses = openmeteo.weather_api(url, params=params)
response = responses[0]

# ─── 3. Extract current conditions ──────────────────────────────────────────────
current = response.Current()
current_vars = {
    "Temperature (°C)": current.Variables(0).Value(),
    "Humidity (%)": current.Variables(1).Value(),
    "Feels Like (°C)": current.Variables(2).Value(),
    "Rain (mm)": current.Variables(3).Value(),
    "Precipitation (mm)": current.Variables(4).Value(),
}
st.markdown("""
<style>
/* target the main app container and force all text to white */
[data-testid="stAppViewContainer"] * {
    color: white !important;
}
/* optional: make metric numbers & labels white too */
.stMetricValue, .stMetricLabel {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ─── 4. Build hourly DataFrame ─────────────────────────────────────────────────
hourly = response.Hourly()
times = pd.date_range(
    start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
    end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
    freq=pd.Timedelta(seconds=hourly.Interval()),
    inclusive="left",
)

df_hourly = pd.DataFrame({
    "time": times,
    "Temperature (°C)": hourly.Variables(0).ValuesAsNumpy(),
    "Humidity (%)": hourly.Variables(1).ValuesAsNumpy(),
    "Feels Like (°C)": hourly.Variables(2).ValuesAsNumpy(),
    "Precipitation Prob. (%)": hourly.Variables(3).ValuesAsNumpy(),
    "UV Index": hourly.Variables(4).ValuesAsNumpy(),
})
df_hourly = df_hourly.set_index("time")

# ─── 5. Streamlit UI ────────────────────────────────────────────────────────────

#st.title("🌤️ Weather Dashboard — CDMX")

# Current conditions
st.subheader("Current Conditions")
cols = st.columns(len(current_vars))
for col, (name, val) in zip(cols, current_vars.items()):
    col.metric(label=name, value=round(val, 1))

st.markdown("---")

# Hourly graphs
st.subheader("Hourly Forecast (Next 24 h)")

# Temperature & Feels Like
temp_df = df_hourly.reset_index()
temp_chart = (
    alt.Chart(temp_df)
       .transform_fold(
           ["Temperature (°C)", "Feels Like (°C)"],
           as_=["Variable", "Value"]
       )
       .mark_line()
       .encode(
           x=alt.X("time:T", title="Time"),
           y=alt.Y("Value:Q", title="°C"),
           color=alt.Color("Variable:N", title="")
       )
       .properties(title="Temperature & Feels Like")
       .configure_view(fill="transparent")
       .configure(background="transparent")
)
st.altair_chart(temp_chart, use_container_width=True)

# Humidity
hum_chart = (
    alt.Chart(temp_df)
       .mark_line(color="#1f77b4")
       .encode(
           x=alt.X("time:T", title="Time"),
           y=alt.Y("Humidity (%):Q", title="Humidity (%)")
       )
       .properties(title="Humidity")
       .configure_view(fill="transparent")
       .configure(background="transparent")
)
st.altair_chart(hum_chart, use_container_width=True)

# UV Index
uv_chart = (
    alt.Chart(temp_df)
       .mark_line(color="#ff7f0e")
       .encode(
           x=alt.X("time:T", title="Time"),
           y=alt.Y("UV Index:Q", title="UV Index")
       )
       .properties(title="UV Index")
       .configure_view(fill="transparent")
       .configure(background="transparent")
)
st.altair_chart(uv_chart, use_container_width=True)
