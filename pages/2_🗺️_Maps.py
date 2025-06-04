import streamlit as st
import requests
import urllib.parse
import pathlib
from datetime import datetime
from utils import hide_all_buttons, switch_page

# --- Configuración CSS ---
# Inyectar common.css
css_path = pathlib.Path(__file__).parents[1] / "styles" / "common.css"
css = css_path.read_text()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

hide_all_buttons()
# Inyectar maps.css
maps_css_path = pathlib.Path(__file__).parents[1] / "styles" / "maps.css"
maps_css = maps_css_path.read_text()
st.markdown(f"<style>{maps_css}</style>", unsafe_allow_html=True)

# Variables de gradiente
BG_DEGREE = "145deg"
BG_COLOR1 = "#57A1F2"
BG_PERCENT1 = "30%"
BG_COLOR2 = "#F7F7F7"
BG_PERCENT2 = "99%"
SIDEBAR_BG_COLOR = "#3484F0"

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



# --- Función principal de mapas (código original sin modificar) ---
GOOGLE_API_KEY = st.secrets['maps']['map-key']
ORIGIN = "19.4270256,-99.1676657"  # Ángel de la Independencia, CDMX

st.title("Maps")

# Entrada de texto del usuario
destination = st.text_input("Escribe tu destino:")

if destination:
    # Codificamos los valores para URL
    origin_encoded = urllib.parse.quote(ORIGIN)
    destination_encoded = urllib.parse.quote(destination)

    # Llamada a Directions API
    directions_url = (
        f"https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origin_encoded}&destination={destination_encoded}&key={GOOGLE_API_KEY}"
    )
    response = requests.get(directions_url)
    data = response.json()

    if data["status"] == "OK":
        # Mostramos duración y distancia
        leg = data["routes"][0]["legs"][0]
        # Mostramos mapa embebido con ruta
        embed_url = (
            f"https://www.google.com/maps/embed/v1/directions"
            f"?key={GOOGLE_API_KEY}&origin={origin_encoded}&destination={destination_encoded}"
        )

        st.markdown(
            f'<iframe width="100%" height="500" frameborder="0" style="border:0" '
            f'src="{embed_url}" allowfullscreen></iframe>',
            unsafe_allow_html=True
        )
    else:
        st.error("No se pudo encontrar la ruta. Verifica el destino.")

# --- Barra lateral ---
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