import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils import hide_all_buttons, switch_page
import requests
from PIL import Image
import numpy as np
import io
from datetime import datetime
import pathlib
import time
from streamlit_autorefresh import st_autorefresh
from asistente import *
import threading

CLIENT_ID = st.secrets["client_id"]
CLIENT_SECRET = st.secrets["client_secret"]
REDIRECT_URI = st.secrets["redirect_uri"]

SCOPE = "user-modify-playback-state user-read-playback-state playlist-read-private playlist-read-collaborative"

sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE,
                        cache_path=".cache")

token_info = sp_oauth.get_cached_token()

if not token_info:
    auth_url = sp_oauth.get_authorize_url()
    st.markdown(f"[Login to Spotify]({auth_url})")

    code_url = st.text_input("Paste the full URL you were redirected to after login:")
    if code_url:
        code = sp_oauth.parse_response_code(code_url)
        token_info = sp_oauth.get_access_token(code)

# Auto-refresh & hide default nav-links
hide_all_buttons()

# --- inject spotify.css ---
css_path = pathlib.Path(__file__).parents[1] / "styles" / "spotify.css"
css = css_path.read_text()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Toggle to enable/disable Spotify API calls
spotify_enabled = st.sidebar.checkbox("Enable Spotify API", False)

if spotify_enabled:
    # create a single container for your entire UI
    container = st.container()

    with container:
        # initialize pause state
        if "paused" not in st.session_state:
            st.session_state.paused = False

        if token_info:
            sp = spotipy.Spotify(auth=token_info["access_token"])
            try:
                playback = sp.current_playback()
            except requests.exceptions.ConnectionError as e:
                # log the error, wait a bit and retry once
                st.warning("Network hiccup fetching playback, retrying…")
                time.sleep(1)
                try:
                    playback = sp.current_playback()
                except Exception:
                    playback = None  # give up on this cycle

            if not playback:
                print(sp.devices())
                # playback = sp.start_playback()
            tab1, tab2, tab3 = st.tabs(["Now Playing", "Playlists", "Search Artist"])

            with tab1:
                # auto-refresh now-playing every 1s
                count = st_autorefresh(interval=1000, key="spotify_tab1_refresh")
                # hide the autorefresh component and its iframe to remove extra gap
                st.markdown(
                    """
                    <style>
                      [data-testid="stElementContainer"].st-key-spotify_tab1_refresh,
                      [data-testid="stElementContainer"].st-key-spotify_tab1_refresh iframe {
                        margin: 0 !important;
                        padding: 0 !important;
                        height: 0 !important;
                        overflow: hidden !important;
                        display: none !important;
                      }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                if playback and playback.get("item"):
                    track = playback["item"]
                    track_name = track["name"]
                    artist_name = ", ".join(artist["name"] for artist in track["artists"])
                    album_images = track["album"]["images"]

                    # Display album art if available
                    album_image_width = 300        # width of the album art in pixels
                    track_title_font_size = "1.8em"
                    artist_name_font_size = "1.1em"

                    progress_ms = playback['progress_ms']
                    duration_ms = track['duration_ms']
                    time_left_ms = duration_ms - progress_ms

                    # Calculate progress percentage
                    percentage = int((progress_ms / duration_ms) * 100)

                    # Update progress bar and text

                    if album_images:
                        album_cover_url = album_images[0]["url"]

                        # Compute average album color & resize image
                        response = requests.get(album_cover_url)
                        img = Image.open(io.BytesIO(response.content)).convert("RGB")
                        img = img.resize((50, 50))
                        img_arr = np.array(img)
                        pixels = img_arr.reshape(-1, 3)

                        # average color
                        avg_color = tuple(pixels.mean(axis=0).astype(int))
                        hex_color = f"#{avg_color[0]:02x}{avg_color[1]:02x}{avg_color[2]:02x}"

                        # brighten that average so its brightness equals the brightest pixel
                        sums = pixels.sum(axis=1)
                        max_b = sums.max()
                        avg_b = sums.mean() or 1
                        factor = max_b / avg_b
                        bright_avg = tuple(min(int(c * factor), 255) for c in avg_color)
                        bright_hex_color = f"#{bright_avg[0]:02x}{bright_avg[1]:02x}{bright_avg[2]:02x}"

                        # Save last colors
                        st.session_state.last_hex_color = hex_color
                        st.session_state.last_bright_hex_color = bright_hex_color
                        st.session_state.last_rgba_color = f"rgba({int(avg_color[0]*0.5)},{int(avg_color[1]*0.5)},{int(avg_color[2]*0.5)},1)"

                        # dynamic background gradient based on album color
                        st.markdown(f"""
                        <style>
                          [data-testid="stAppViewContainer"] {{
                            background: linear-gradient(145deg, {hex_color} 30%, #000000 100%) !important;
                          }}
                        </style>
                        """, unsafe_allow_html=True)

                        now_playing = f"""
                        <div style="
                            display: flex;
                            align-items: center;
                            background: rgba(0, 0, 0, 0.3);
                            backdrop-filter: blur(.1px);
                            -webkit-backdrop-filter: blur(.1px);
                            padding: 12px;
                            border-radius: 8px;
                        ">
                          <img src="{album_cover_url}" width="{album_image_width}" style="
                              border-radius: 4px;
                              margin-right: 24px;
                          "/>
                          <div style="color: white;">
                            <div style="
                                font-size: {track_title_font_size};
                                font-weight: bold;
                                line-height: 1.2;
                            ">{track_name}</div>
                            <div style="
                                font-size: {artist_name_font_size};
                                opacity: 0.8;
                                margin-top: 4px;
                            ">{artist_name}</div>
                          </div>
                        </div>
                        """
                        st.markdown(now_playing, unsafe_allow_html=True)

                        # dynamic sidebar styling using the same hex_color
                        darkness = .5
                        opacity_level = 1
                        darker_rgb = tuple(int(c * (1 - darkness)) for c in avg_color)
                        rgba_color = f"rgba({darker_rgb[0]}, {darker_rgb[1]}, {darker_rgb[2]}, {opacity_level})"

                        st.markdown(
                            f"""
                            <style>
                              section[data-testid="stSidebar"] {{
                                background-color: {rgba_color} !important;
                              }}
                              section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {{
                                background-color: {rgba_color} !important;
                              }}
                              section[data-testid="stSidebar"] a,
                              section[data-testid="stSidebar"] .stButton>button {{
                                color: white !important;
                              }}
                            </style>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Save last cover & colors
                        st.session_state.last_album_cover_url = album_cover_url
                        st.session_state.last_track_name = track_name
                        st.session_state.last_artist_name = artist_name
                    else:
                        # First try to reuse last known cover & colors
                        if st.session_state.get("last_hex_color") and st.session_state.get("last_album_cover_url"):
                            hex_color = st.session_state.last_hex_color
                            rgba_color = st.session_state.last_rgba_color
                            st.markdown(f"""
                            <style>
                              [data-testid="stAppViewContainer"] {{
                                background: linear-gradient(145deg, {hex_color} 30%, #000000 100%) !important;
                              }}
                              section[data-testid="stSidebar"] {{
                                background-color: {rgba_color} !important;
                              }}
                              section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {{
                                background-color: {rgba_color} !important;
                              }}
                            </style>
                            """, unsafe_allow_html=True)
                            st.markdown(f"""
                            <div style="display:flex; align-items:center; padding:12px; border-radius:8px;">
                              <img src="{st.session_state.last_album_cover_url}" width="100" style="border-radius:4px; margin-right:20px;"/>
                              <div style="color:white;">
                                <div style="font-size:1.5em; font-weight:bold;">{st.session_state.last_track_name}</div>
                                <div style="font-size:1em; opacity:0.8;">{st.session_state.last_artist_name}</div>
                              </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Fallback to default green
                            default_green = (30, 215, 96)
                            darkness = .35
                            opacity_level = 1
                            darker_rgb = tuple(int(c * (1 - darkness)) for c in default_green)
                            rgba_color = f"rgba({darker_rgb[0]}, {darker_rgb[1]}, {darker_rgb[2]}, {opacity_level})"
                            st.markdown(
                                f"""
                                <style>
                                  section[data-testid="stSidebar"] {{
                                    background-color: {rgba_color} !important;
                                  }}
                                  section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {{
                                    background-color: {rgba_color} !important;
                                  }}
                                  section[data-testid="stSidebar"] a,
                                  section[data-testid="stSidebar"] .stButton>button {{
                                    color: white !important;
                                  }}
                                </style>
                                """,
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                '<h2 style="color: white;">Pick a playlist or track to start listening!</h2>',
                                unsafe_allow_html=True
                            )
                    # progress bar (now updated on each refresh)
                    duration_ms = track["duration_ms"]
                    progress_ms = playback["progress_ms"]
                    percent = int((progress_ms / duration_ms) * 100)
                    st.progress(percent)

                    # custom track & fill colors
                    st.markdown(f"""
                    <style>
                      [data-baseweb="progress-bar"] > div > div {{
                        background-color: {st.session_state.get("last_rgba_color", "rgba(0,0,0,0.3)")} !important;
                      }}
                      [data-baseweb="progress-bar"] > div > div > div {{
                        background-color: {st.session_state.get("last_bright_hex_color", "#ffffff")} !important;
                      }}
                    </style>
                    """, unsafe_allow_html=True)

                    # inject frosted style + CSS shapes for playback buttons
                    st.markdown(f"""
                    <style>
                      /* common frosted glass panel */
                      [data-testid="stElementContainer"].st-key-back .stButton > button,
                      [data-testid="stElementContainer"].st-key-play .stButton > button,
                      [data-testid="stElementContainer"].st-key-pause .stButton > button,
                      [data-testid="stElementContainer"].st-key-skip .stButton > button {{
                        position: relative;
                        width: 100% !important;
                        height: 100px !important;
                        padding: 0 !important;
                        background: {st.session_state.get("last_rgba_color", "rgba(0,0,0,0.3)")} !important;
                        backdrop-filter: blur(10px);
                        -webkit-backdrop-filter: blur(10px);
                        border: none !important;
                        border-radius: 8px;
                        overflow: hidden;
                      }}

                      /* Back button: double left arrows */
                      [data-testid="stElementContainer"].st-key-back .stButton > button::before {{
                        content: "";
                        position: absolute;
                        left: 30%;
                        top: 50%;
                        transform: translate(-50%, -50%);
                        width: 0; height: 0;
                        border-top: 10px solid transparent;
                        border-bottom: 10px solid transparent;
                        border-right: 12px solid white;
                      }}
                      [data-testid="stElementContainer"].st-key-back .stButton > button::after {{
                        content: "";
                        position: absolute;
                        left: 45%;
                        top: 50%;
                        transform: translate(-50%, -50%);
                        width: 0; height: 0;
                        border-top: 10px solid transparent;
                        border-bottom: 10px solid transparent;
                        border-right: 12px solid white;
                      }}

                      /* Play button: single right arrow */
                      [data-testid="stElementContainer"].st-key-play .stButton > button::before {{
                        content: "";
                        position: absolute;
                        left: 50%;
                        top: 50%;
                        transform: translate(-45%, -50%);
                        width: 0; height: 0;
                        border-top: 12px solid transparent;
                        border-bottom: 12px solid transparent;
                        border-left: 18px solid white;
                      }}
                      [data-testid="stElementContainer"].st-key-play .stButton > button::after {{ content: ""; }}

                      /* Pause button: two vertical bars */
                      [data-testid="stElementContainer"].st-key-pause .stButton > button::before,
                      [data-testid="stElementContainer"].st-key-pause .stButton > button::after {{
                        content: "";
                        position: absolute;
                        top: 35%;
                        width: 4px;
                        height: 30px;
                        background: white;
                      }}
                      [data-testid="stElementContainer"].st-key-pause .stButton > button::before {{
                        left: 45%;
                        transform: translateX(-8px);
                      }}
                      [data-testid="stElementContainer"].st-key-pause .stButton > button::after {{
                        left: 55%;
                        transform: translateX(-8px);
                      }}

                      /* Skip button: double right arrows */
                      [data-testid="stElementContainer"].st-key-skip .stButton > button::before {{
                        content: "";
                        position: absolute;
                        left: 45%;
                        top: 50%;
                        transform: translate(-50%, -50%);
                        width: 0; height: 0;
                        border-top: 10px solid transparent;
                        border-bottom: 10px solid transparent;
                        border-left: 12px solid white;
                      }}
                      [data-testid="stElementContainer"].st-key-skip .stButton > button::after {{
                        content: "";
                        position: absolute;
                        left: 60%;
                        top: 50%;
                        transform: translate(-50%, -50%);
                        width: 0; height: 0;
                        border-top: 10px solid transparent;
                        border-bottom: 10px solid transparent;
                        border-left: 12px solid white;
                      }}
                    </style>
                    """, unsafe_allow_html=True)

                    # Playback controls (no more manual st.rerun or refresh flags)
                    playback_cols = st.columns(3)

                    with playback_cols[0]:
                        if st.button("Back", key="back", use_container_width=True, type="tertiary"):
                            sp.previous_track()
                    with playback_cols[1]:
                        # use session_state.paused to determine button
                        if st.session_state.get("paused", False):
                            if st.button("Play", key="play", use_container_width=True, type="tertiary"):
                                sp.start_playback()
                                st.session_state.paused = False
                        else:
                            if st.button("Pause", key="pause", use_container_width=True, type="tertiary"):
                                sp.pause_playback()
                                st.session_state.paused = True
                    with playback_cols[2]:
                        if st.button("Skip", key="skip", use_container_width=True, type="tertiary"):
                            sp.next_track()

            with tab2:
                st.markdown(
                    '<h3 style="color: white; margin-bottom: 1rem;">🎧 Your Top 5 Playlists</h3>',
                    unsafe_allow_html=True
                )

                # Fetch user's playlists
                playlists = sp.current_user_playlists(limit=5)["items"]

                cols = st.columns(5)

                for i, playlist in enumerate(playlists):
                    with cols[i]:
                        image_url = playlist["images"][0]["url"] if playlist["images"] else None

                        # --- inject CSS so the .st-key-play_{i} button shows the album cover as background ---
                        if image_url:
                            # inject frosted‐glass card style with image and title via CSS pseudo‐elements
                            st.markdown(f"""
                            <style>
                                /* make the button itself a frosted glass panel */
                                [data-testid="stElementContainer"].st-key-play_{i} .stButton > button {{
                                    position: relative;
                                    width: 100% !important;
                                    height: 180px !important;
                                    padding: 0 !important;
                                    border: none !important;
                                    background: {st.session_state.get("last_rgba_color", "rgba(255,255,255,0.15)")} !important;
                                    backdrop-filter: blur(10px);
                                    -webkit-backdrop-filter: blur(10px);
                                    overflow: hidden;
                                    border-radius: 8px;
                                }}
                                /* ::before shows the album cover inside the frosted panel */
                                [data-testid="stElementContainer"].st-key-play_{i} .stButton > button::before {{
                                    content: "";
                                    position: absolute;
                                    top: 10px;
                                    left: 10px;
                                    right: 10px;
                                    bottom: 40px;
                                    background: url({image_url}) no-repeat center center;
                                    background-size: cover;
                                    border-radius: 4px;
                                }}
                                /* ::after renders the playlist name below the cover */
                                [data-testid="stElementContainer"].st-key-play_{i} .stButton > button::after {{
                                    content: "{playlist['name']}";
                                    position: absolute;
                                    bottom: 8px;
                                    width: 100%;
                                    text-align: center;
                                    color: white;
                                    font-size: 0.9em;
                                    white-space: nowrap;
                                    overflow: hidden;
                                    text-overflow: ellipsis;
                                    padding: 0 5px;
                                }}
                            </style>
                            """, unsafe_allow_html=True)

                        # now render an “empty” button that is actually the cover
                        if st.button("", key=f"play_{i}", use_container_width=True, type="tertiary"):
                            try:
                                sp.start_playback(context_uri=playlist["uri"])
                                st.success(f"Now playing: {playlist['name']}")
                                st.rerun()
                            except Exception as e:
                                st.write(f"Could not start playback: Please use a device to start playing. {e}")

            with tab3:
                st.markdown('<h3 style="color:white;">🔍 Search and Play Artist</h3>', unsafe_allow_html=True)
                st.markdown('<p style="color:white; margin-bottom: 0.5rem;">Enter artist name:</p>', unsafe_allow_html=True)
                artist_query = st.text_input(
                    "Artist Name",
                    key="artist_query",
                    label_visibility="collapsed"
                )
                if st.button("Play Artist", key="play_artist", use_container_width=True, type="tertiary"):
                    if artist_query:
                        # Search for the artist
                        result = sp.search(q=artist_query, type="artist", limit=1)
                        if result["artists"]["items"]:
                            artist_id = result["artists"]["items"][0]["id"]
                            # Get artist's top tracks
                            top_tracks = sp.artist_top_tracks(artist_id, country='US')["tracks"]
                            if top_tracks:
                                track_uris = [track["uri"] for track in top_tracks]
                                sp.start_playback(uris=track_uris)
                                st.success(f"Now playing top tracks from {artist_query}")
                                st.rerun()
                            else:
                                st.warning("No top tracks found for this artist.")
                        else:
                            st.warning("Artist not found. Try another name.")
                    else:
                        st.warning("Please enter an artist name.")

                    # Buttons for playback control
                    left, spacer1, col, spacer2, right = st.columns([1, 1, 2, 1, 1])

                    with col:
                        col1, col2, col3 = st.columns([1, 1, 1])

                        with col1:
                            if st.button("← Back"):
                                sp.previous_track()
                                st.rerun()

                        with col2:
                            if playback and playback["is_playing"]:
                                if st.button("|| Pause", use_container_width=True, type="tertiary"):
                                    sp.pause_playback()
                                    st.rerun()
                            else:
                                if st.button("▶️ Play", use_container_width=True, type="tertiary"):
                                    sp.start_playback()
                                    st.rerun()

                        with col3:
                            if st.button("→ Skip"):
                                sp.next_track()
                                st.rerun()
else:
    st.markdown(
        "<h2 style='color:white;'>Spotify integration is disabled. Use the AI assistant via the 'Asistant' button below.</h2>",
        unsafe_allow_html=True
    )

# Sidebar for navigation and AI assistant (always shown)
with st.sidebar:

    # Display current time, centered at the top of the sidebar
    current_time = datetime.now().strftime("%H:%M")
    st.markdown(
        f"<div style='text-align:center; font-size:1.2rem; margin-bottom:1rem; color: white; font-weight: bold;'>{current_time}</div>",
        unsafe_allow_html=True
    )

    if 'button_pressed' not in st.session_state:
        st.session_state.button_pressed = False
        st.session_state.button_time = 0

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
        if st.button("Asistant", key="assist", type="tertiary"):
            st.session_state.button_pressed = True
            st.session_state.button_time = time.time()
            # invoke voice assistant, get JSON payload
            json_obj = prompt(API_KEY, spotify_prompt())
            func = json_obj.get("func", "")
            args = json_obj.get("args", {})
            # dispatch Spotify action
            try:
                if func == "search_artist":
                    print("searching artist:", args["artist_name"])
                    res = sp.search(q=f"artist:{args['artist_name']}", type="artist", limit=1)
                    items = res.get("artists", {}).get("items", [])
                    if items:
                        aid = items[0]["id"]
                        top = sp.artist_top_tracks(aid, country="US")["tracks"]
                        sp.start_playback(uris=[t["uri"] for t in top])
                elif func == "search_song":
                    print("searching song:", args["song_name"])
                    res = sp.search(q=f'track:"{args["song_name"]}"', type="track", limit=1)
                    items = res.get("tracks", {}).get("items", [])
                    if items:
                        sp.start_playback(uris=[items[0]["uri"]])
                elif func == "search_song_by_artist":
                    print("searching song by artist:", args["song_name"], "by", args["artist_name"])
                    res = sp.search(
                        q=f'track:"{args["song_name"]}" artist:"{args["artist_name"]}"',
                        type="track", limit=1
                    )
                    items = res.get("tracks", {}).get("items", [])
                    if items:
                        sp.start_playback(uris=[items[0]["uri"]])
            except Exception as e:
                st.error(f"Spotify action failed: {e}")
            # refresh UI
            st.rerun()

if st.session_state.button_pressed and (time.time() - st.session_state.button_time) > 5:
    st.session_state.button_pressed = False
    st.session_state.button_time = 0
    st.rerun()

button_style = """
<style>
    /* Estilo normal del botón */
    .element-container.st-key-assist button {
        transition: background-color 0.3s ease;
    }
    
    /* Estilo cuando está activo (rojo) */
    .element-container.st-key-assist button:active,
    .element-container.st-key-assist.button-active button {
        background-color: #ff4b4b !important;
        box-shadow: 0 0 10px #ff4b4b !important;
    }
</style>
"""
if st.session_state.button_pressed:
    button_style = button_style.replace(
        ".element-container.st-key-assist.button-active button", 
        ".element-container.st-key-assist button"
    )

st.markdown(button_style, unsafe_allow_html=True)

