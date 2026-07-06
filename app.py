import tkinter as tk
import threading
import joblib
import os
import speech_recognition as sr
import edge_tts
import asyncio
import subprocess
from time import time
from math import sin
from extract_entities import extract_from_intent
from intent_router import route


model_path = "intent_model.joblib"

if not os.path.exists(model_path):
    import train_intent_model  # This will run the code inside the file, creating the file

model = joblib.load(model_path)
r = sr.Recognizer()
r.pause_threshold = 1.0  # Seconds of silence before ending the phrase
r.energy_threshold = 700  # Adjust as needed for your mic volume

mic = sr.Microphone()
voice = "en-AU-WilliamNeural"

window = tk.Tk()
window.title("Computer Assistant")
windowWidth = 1300
windowHeight = 800
window.geometry(f"{windowWidth}x{windowHeight}+{(window.winfo_screenwidth()-windowWidth)//2}+{(window.winfo_screenheight()-windowHeight)//2}")
window.resizable(False, False)

def bring_to_front():
    window.lift()
    window.attributes("-topmost", True)
    window.update()
    window.attributes("-topmost", False)
    window.focus_force()

canvas = tk.Canvas(window, width=windowWidth, height=windowHeight, bg="white", highlightthickness=0)
canvas.place(x=0, y=0)

canvas.create_rectangle(0, 0, windowWidth, windowHeight, fill="#333333", outline="")

for i in range(0, 2 * windowWidth // 25):
    # Draw diagonal lines from left to right across the canvas
    canvas.create_line(25 * i, 0, 25 * i, windowHeight, width=1, fill="black")
    # Draw horizontal lines across the canvas
    canvas.create_line(0, 25 * i, windowWidth, 25 * i, width=1, fill="black")

# Circle at the center of the screen
canvas.create_oval(
    560, 310, 740, 490,
    fill="#222222",
    outline="#bbbbbb",
    width=4
)

additionalSpin = 0
totalAddSpin = 0
def animateArcs():
    global arc1, arc2, additionalSpin, totalAddSpin

    def update():
        global arc1, arc2, additionalSpin, totalAddSpin

        degree = 30 * sin(time())
        if arc1:
            canvas.delete(arc1)
        if arc2:
            canvas.delete(arc2)
        arc1 = canvas.create_arc(540, 290, 760, 510, start=45 + degree - totalAddSpin, extent=60, style=tk.ARC, outline="#bbbbbb", width=5)
        arc2 = canvas.create_arc(540, 290, 760, 510, start=225 + degree - totalAddSpin, extent=60, style=tk.ARC, outline="#bbbbbb", width=5)

        if additionalSpin > 0:
            increment = max(1, int(additionalSpin * 0.15))
            totalAddSpin += increment
            additionalSpin -= increment

        canvas.after(16, update)  # ~60 fps

    arc1 = None
    arc2 = None
    update()

# Text for inside the circle
canvas.create_text(
    650, 400,
    text="Computer",
    fill="white",
    font=("Arial", 15, "bold")
)

# Text for current state
state = "Idle"
currentStateText = None
def updateStateText():
    global currentStateText

    def update():
        global currentStateText

        if currentStateText is not None:
            canvas.delete(currentStateText)

        if state in ["Listening", "Speaking"]:
            num_dots = (int(time()) % 3) + 1
            newState = state + "." * num_dots
        else:
            newState = state

        currentStateText = canvas.create_text(
            650, 560,
            text=newState,
            fill="#bbbbbb",
            font=("Arial", 13)
        )

        window.after(100, update)

    update()

# Text for command/response
commandValue = ""
command_text = None

def updateCommandText():
    global command_text

    def update():
        global command_text

        if command_text is not None:
            canvas.delete(command_text)
        
        command_text = canvas.create_text(
            650, 620,
            text=commandValue,
            fill="#999999",
            font=("Arial", 15, "bold"),
            width=1000,
            anchor="center"
        )
   
        window.after(100, update)

    update()


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
    global state, commandValue

    communicate = edge_tts.Communicate(text, voice, rate="-10%", volume="-20%")
    await communicate.save(output_file)
    state = "Speaking"
    subprocess.run(["afplay", output_file])

    commandValue = "" # Reset the value   

def model_mainloop():
    global state, commandValue, additionalSpin

    state = "Idle"
    text = listen_text()

    if "computer" in text:
        window.after(0, bring_to_front)
        state = "Listening"
        additionalSpin = 180
        command = listen_text()
        commandValue = command

        if command.strip():
            intent = model.predict([command])[0]
            entities = extract_from_intent(intent, command)
            result = route(intent, entities)
            commandValue = result

            asyncio.run(speak(result))

    window.after(0, start_model)


def start_model():
    threading.Thread(target=model_mainloop, daemon=True).start()



window.after(0, updateStateText)
window.after(0, updateCommandText)
window.after(0, animateArcs)
window.after(0, start_model)
window.mainloop()