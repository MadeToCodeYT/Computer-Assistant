import speech_recognition as sr

r = sr.Recognizer()
r.pause_threshold = 1.5  # Seconds of silence before ending the phrase
r.energy_threshold = 500  # Adjust as needed for your mic volume

mic = sr.Microphone()

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

while True:
    print("Waiting for wake word...")
    text = listen_text()

    if "computer" in text:
        print("Wake word heard. Speak your command...")
        command = listen_text()
        print("Command:", command)