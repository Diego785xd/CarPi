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

API_KEY = st.secrets["openai"]["api_key"]
aiPromt = "Eres un asistente de voz en auto. Te voy a enviar una transcripción de audio y quiero que conrtestes de la mejor manera posible."
idioma = 'es'

def promt(key, promtAi, language):
    pygame.mixer.init()

    #Graba Audio y lo guarda
    print(f"Grabando audio de 5 segundos....")
    audio_data = sd.rec(int(5 * 44100), samplerate=44100, channels=2, dtype='int16')
    sd.wait()
    write("UserAudio.mp3", 44100, audio_data)

    write("temp.wav", 44100, audio_data)

    audio = AudioSegment.from_wav("temp.wav")
    audio.export("UserAudio.mp3", format = "mp3")
    os.remove("temp.wav")

    #Pasar de voz a texto
    client = OpenAI(api_key=key)
    
    with open("/home/pi/dev/Carplay/UserAudio.mp3", "rb") as audio_file:
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
    print(aiRes)

    aiAudio = gTTS(text=aiRes, lang=language, slow=False)

    aiAudio.save("Respuesta.mp3")

    pygame.mixer.music.load("Respuesta.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)