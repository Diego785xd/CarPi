import sounddevice as sd
from scipy.io.wavfile import write
from pydub import AudioSegment
import os
import openai
from openai import OpenAI
import time
from gtts import gTTS
import pygame
import time
import streamlit as st  # added
import spotipy
import json
import datetime as _dt

API_KEY = st.secrets["openai"]["api_key"]
MP3_PATH  = "/Users/rossi/dev/pidev/UserAudio.mp3"


def search_artist(artist_name):
    return sp.search(q=f"artist:{artist_name}", type="artist", limit=1)

def search_song(song_name):
    return sp.search(q=f'track:"{song_name}"', type="track", limit=1)

def search_song_by_artist(song_name, artist_name):
    return sp.search(
        q=f'track:"{song_name}" artist:"{artist_name}"',
        type="track",
        limit=1
    )

def spotify_prompt():
    prompt = """
You are a playful Spotify Apple Car Assistant with access to the following tools:
1. search_artist(artist_name)
2. search_song(song_name)
3. search_song_by_artist(song_name, artist_name)

For each user request, respond ONLY with a JSON object:
{"res": "your playful response", "func": "<tool or empty>", "args": { ... }, "lang": "<language code>"}

Use 'lang' with values 'en' (English), 'es' (Spanish), or 'pt' (Portuguese) matching the language of the user's request. Default to 'en'.

Here are some examples:
###
# 1. English: Play an artist
User: "Play The Beatles"
Assistant: {"res": "Grooving to The Beatles vibes coming right up!", "func": "search_artist", "args": {"artist_name": "The Beatles"}, "lang": "en"}
###
# 2. English: Play a song by title
User: "Play Happy"
Assistant: {"res": "Feeling happy? Let's spin 'Happy' now!", "func": "search_song", "args": {"song_name": "Happy"}, "lang": "en"}
###
# 3. Spanish: Play a song when request in Spanish
User: "Reproduce que pasaria"
Assistant: {"res": "¡Melancólico, me gusta! Reproduciendo 'Qué pasaría' ahora mismo!", "func": "search_song", "args": {"song_name": "Feliz"}, "lang": "es"}
###
# 4. Portuguese: Play a specific song by artist when request in  Portuguese
User: "Toca Shape of You do Ed Sheeran"
Assistant: {"res": "Tocando 'Shape of You' do Ed Sheeran!", "func": "search_song_by_artist", "args": {"song_name": "Shape of You", "artist_name": "Ed Sheeran"}, "lang": "pt"}
###
# 5. Tell a joke (no tool needed)
User: "Tell me a joke"
Assistant: {"res": "Why don't scientists trust atoms? Because they make up everything!", "func": "", "args": {}, "lang": "en"}
###
# 6. Out-of-scope action
User: "Open the window"
Assistant: {"res": "Sorry, I can't help with that", "func": "", "args": {}, "lang": "en"}
###
Remember to always respond in a playful tone, do not use emojis, do not hallucinate functions and answer only in the JSON format specified without any additional text or explanation.
Now, go ahead and handle the user request:
"""
    return prompt

def maps_place(place):
    return place

def maps_prompt():
    prompt = """
Eres un asistente de Apple Car Maps juguetón con acceso a la siguiente herramienta:
1. maps_place(place): recibe el nombre o dirección y devuelve la ubicación solicitada

Para cada solicitud del usuario, responde SOLO con un objeto JSON:
{"res": "tu respuesta juguetona", "func": "<tool o vacío>", "args": {...}, "lang": "es"}

Aquí van 3 ejemplos en español:
###
# 1. Ir a un sitio
Usuario: "Llévame al Parque Central"
Asistente: {"res": "¡Claro! Preparando la ruta hacia el Parque Central...", "func": "maps_place", "args": {"place": "Parque Central"}, "lang": "es"}
###
# 2. Sin usar herramienta
Usuario: "¿Cuenta un chiste"
Asistente: {"res": "Qué le dijo un ciego a otro?, no nos vemos", "func": "", "args": {}, "lang": "es"}
###
# 3. Fuera de alcance
Usuario: "Abre la puerta"
Asistente: {"res": "Lo siento, no puedo ayudar con eso", "func": "", "args": {}, "lang": "es"}
###

Recuerda siempre responder en formato JSON especificado sin texto adicional ni explicaciones.
Ahora, maneja la solicitud del usuario:
"""
    return prompt

def mail_prompt():
    prompt = """
Eres un asistente de correo juguetón con acceso a las siguientes funciones:
1. get_last_email_header(service): devuelve el título del último correo (Subject, From, Date).
2. summarize_last_mail(service): devuelve un resumen conciso del último correo.

Para cada solicitud, responde SOLO con un objeto JSON:
{"res": "tu respuesta juguetona", "func": "<función o vacío>", "args": {}, "lang": "<código de idioma>"}

Determina el valor de "lang" en función del idioma predominante en el contenido del correo obtenido, no en el idioma de la petición del usuario.

Ejemplos:
###
# Usuario: "¿Cuál es el asunto del último correo?"
# (el correo está en español)
Asistente: {"res": "¡Aquí tienes el asunto del último correo!", "func": "get_last_email_header", "args": {}, "lang": "es"}
###
# Usuario: "Resume mi último correo"
# (el correo está en inglés)
Asistente: {"res": "Sure, here’s the summary:", "func": "summarize_last_mail", "args": {}, "lang": "en"}
###
# Usuario: "Abre la puerta"
Asistente: {"res": "Lo siento, no puedo ayudar con eso", "func": "", "args": {}, "lang": "es"}
###

Recuerda responder SOLO con el JSON sin texto adicional. Ahora, maneja la solicitud del usuario:
"""
    return prompt


# --- NEW: retrieve header of the last email ---
def get_last_email_header(service):
    results = service.users().messages().list(userId='me', maxResults=1).execute()
    messages = results.get('messages', [])
    if not messages:
        return None
    msg = service.users().messages().get(
        userId='me',
        id=messages[0]['id'],
        format='metadata',
        metadataHeaders=['Subject','From','Date']
    ).execute()
    headers = msg['payload'].get('headers', [])
    subject = next((h['value'] for h in headers if h['name']=='Subject'), 'Sin asunto')
    sender  = next((h['value'] for h in headers if h['name']=='From'),    'Desconocido')
    date    = next((h['value'] for h in headers if h['name']=='Date'),    'Fecha desconocida')
    return f"Subject: {subject}\nFrom: {sender}\nDate: {date}"

# --- NEW: retrieve header + body text of the last email ---
def get_last_email_full_text(service):
    results = service.users().messages().list(userId='me', maxResults=1).execute()
    messages = results.get('messages', [])
    if not messages:
        return None
    msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()
    headers = msg['payload'].get('headers', [])
    subject = next((h['value'] for h in headers if h['name']=='Subject'), 'Sin asunto')
    sender  = next((h['value'] for h in headers if h['name']=='From'),    'Desconocido')
    try:
        parts = msg['payload'].get('parts')
        data  = parts[0]['body'].get('data') if parts else msg['payload']['body'].get('data','')
        text  = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        text  = clean_email_text(text)
    except:
        text = "[No se pudo cargar el contenido]"
    return f"Subject: {subject}\nFrom: {sender}\n\n{text}"

# --- NEW: summarize last email ---
def summarize_last_mail(service):
    """
    Recupera el último correo y genera un resumen usando ChatGPT.
    """
    full_text = get_last_email_full_text(service)
    if not full_text:
        return "No hay correos electrónicos para resumir"
    client = OpenAI(api_key=API_KEY)
    prompt = (
        "Por favor, resume de forma concisa el siguiente correo:\n\n"
        f"{full_text}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un asistente que resume correos de forma clara y breve."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content


def prompt(key, promtAi):
    pygame.mixer.init()

    #Graba Audio y lo guarda
    print(f"Grabando audio de 5 segundos....")
    # record 5 seconds of mono audio to avoid channel mismatch
    audio_data = sd.rec(int(5 * 44100), samplerate=44100, channels=1, dtype='int16')
    sd.wait()
    write("UserAudio.mp3", 44100, audio_data)

    write("temp.wav", 44100, audio_data)

    audio = AudioSegment.from_wav("temp.wav")
    audio.export("UserAudio.mp3", format = "mp3")
    os.remove("temp.wav")

    #Pasar de voz a texto
    client = OpenAI(api_key=key)
    
    with open(MP3_PATH, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    print("El usuario dice: ")
    print(transcript)

    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": promtAi},
            {"role": "user", "content": transcript}
        ],
        max_tokens=200
    )
    
    aiRes = respuesta.choices[0].message.content

    print("\nRespuesta del modelo: ")
    try:
        # Parse the assistant response as JSON
        json_obj = json.loads(aiRes)
        # Pretty-print the JSON
        print(json.dumps(json_obj, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        # Fallback if it's not valid JSON
        print("Invalid JSON response:", aiRes)

    

    aiAudio = gTTS(text=json_obj["res"], lang=json_obj["lang"], slow=False)

    aiAudio.save("Respuesta.mp3")

    pygame.mixer.music.load("Respuesta.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

    print(f"""{json_obj['func']}({json_obj['args']})""")
    return json_obj


def say_tts(texto, languaje):
    pygame.mixer.init()

    
    aiAudio = gTTS(text=texto, lang=languaje, slow=False)

    aiAudio.save("Respuesta.mp3")

    pygame.mixer.music.load("Respuesta.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

def get_next_event(events):
    """
    Given a list of events with ISO 'start' strings and 'title',
    return a dict with the closest event's title, event hour (HH:MM),
    event date (DD Month YYYY), today's date, and current hour.
    """
    items = []
    for ev in events:
        # normalize to ISO and parse; ensure UTC tzinfo for date-only or 'Z'
        raw = ev['start']
        dt = _dt.datetime.fromisoformat(raw.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_dt.timezone.utc)
        items.append((dt, ev['title']))
    if not items:
        return None
    # pick the soonest event
    next_dt, next_title = min(items, key=lambda x: x[0])
    return {
        'title': next_title,
        'hour': next_dt.strftime('%H:%M'),
        'date': next_dt.strftime('%d %B %Y'),
        'today': _dt.datetime.now().strftime('%d %B %Y'),
        'current_hour': _dt.datetime.now().strftime('%H:%M')
    }

def create_event(title: str,
                 start_date: _dt.date,
                 start_time: _dt.time,
                 end_date: _dt.date,
                 end_time: _dt.time,
                 service):
    """
    Creates a Google Calendar event on the 'primary' calendar
    given a title and start/end dates & times.
    """
    start_dt = _dt.datetime.combine(start_date, start_time)
    end_dt   = _dt.datetime.combine(end_date,   end_time)
    event_body = {
        'summary': title,
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'UTC'},
        'end':   {'dateTime': end_dt.isoformat(),   'timeZone': 'UTC'},
    }
    return service.events().insert(
        calendarId='primary',
        body=event_body
    ).execute()


def calendar_prompt(events):
    prompt = f"""
You are a playful Apple Car Calendar Assistant with access to the following tools:
1. get_next_event(events): devuelve los detalles del próximo evento.
2. create_event(title, start_date, start_time, end_date, end_time, service): programa un nuevo evento.

Aquí tienes el contexto de tu próximo evento: {get_next_event(events)}

Para cada solicitud del usuario, responde SOLO con un objeto JSON:
{{"res": "<tu respuesta juguetona>", "func": "<herramienta o vacío>", "args": {{...}}, "lang": "<código de idioma>"}}

Ejemplos:
###
User: "How much time until my next event?"
Assistant: {{"res": "Your meeting starts in 2 hours and 15 minutes!", "func": "get_next_event", "args": {{}}, "lang": "en"}}
###
User: "Programa cita con el dentista mañana a las 15:00"
Assistant: {{"res": "¡Listo! He agendado tu cita con el dentista.", "func": "create_event", "args": {{"title":"cita con el dentista","start_date":"2023-10-05","start_time":"15:00","end_date":"2023-10-05","end_time":"16:00","service":{{}}}}, "lang": "es"}}
###
User: "Reproduce música"
Assistant: {{"res": "Lo siento, no puedo ayudar con eso", "func":"", "args": {{}}, "lang":"es"}}

Ahora, procesa la solicitud del usuario:
"""
    return prompt


