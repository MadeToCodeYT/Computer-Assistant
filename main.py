import joblib
from extract_entities import extract_from_intent
from intent_router import route
import os
import speech_recognition as sr
import edge_tts
import asyncio

model_path = "intent_model.joblib"

if not os.path.exists(model_path):
    import train_intent_model  # This will run the code inside the file, creating the file

model = joblib.load(model_path)
r = sr.Recognizer()
r.pause_threshold = 0.8  # Seconds of silence before ending the phrase
r.energy_threshold = 500  # Adjust as needed for your mic volume

mic = sr.Microphone()
voice = "en-AU-WilliamNeural"

def listen_text():
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.listen(source)  # Waits until user stops talking

    try:
        return r.recognize_google(audio).lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""

async def speak(text, output_file="computer_voice.mp3"):
    communicate = edge_tts.Communicate(text, voice, rate="-10%", volume="-20%")
    await communicate.save(output_file)
    import subprocess
    subprocess.run(['afplay', output_file])
   

while True:
    print("Waiting for wake word...")
    text = listen_text()

    if "computer" in text:
        print("Wake word heard. Speak your command...")
        command = listen_text()
        print("Command:", command)
        if not command.strip():
            continue
        intent = model.predict([command])[0]
        entities = extract_from_intent(intent, command)
        result = route(intent, entities)
        print(result + "\n")
        asyncio.run(speak(result))