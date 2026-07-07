import tkinter as tk
import threading
import joblib
import os
import speech_recognition as sr
import edge_tts
import asyncio
import subprocess
import queue
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
cameraOpen = False
task_queue = queue.Queue()

def process_queue():
    while True:
        try:
            task_queue.get_nowait()()
        except queue.Empty:
            break
    window.after(25, process_queue)

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

canvas = tk.Canvas(window, width=windowWidth, height=windowHeight, bg="#333333", highlightthickness=0)
canvas.place(x=0, y=0)

for i in range(0, 2 * windowWidth // 25):
    canvas.create_line(25 * i, 0, 25 * i, windowHeight, width=1, fill="black")
    canvas.create_line(0, 25 * i, windowWidth, 25 * i, width=1, fill="black")

# Circle bounding box variables: [x1, y1, x2, y2]
circle_bbox = [560, 310, 740, 490]

circle_oval = None
circle_text = None

def updateCircle():
    global circle_oval, circle_text
    # Remove existing shapes/text if they exist
    if circle_oval is not None:
        canvas.delete(circle_oval)
    if circle_text is not None:
        canvas.delete(circle_text)

    circle_oval = canvas.create_oval(
        *circle_bbox,
        fill="#222222",
        outline="#bbbbbb",
        width=4
    )

    # Get the center of the bounding box
    x_center = (circle_bbox[0] + circle_bbox[2]) // 2
    y_center = (circle_bbox[1] + circle_bbox[3]) // 2

    circle_text = canvas.create_text(
        x_center, y_center,
        text="Computer",
        fill="white",
        font=("Arial", 15, "bold")
    )

    canvas.after(16, updateCircle)

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

        # Relative to the circle_bbox
        arc_bbox = [
            circle_bbox[0] - 20,  # left
            circle_bbox[1] - 20,  # top
            circle_bbox[2] + 20,  # right
            circle_bbox[3] + 20   # bottom
        ]
        arc1 = canvas.create_arc(*arc_bbox, start=45 + degree - totalAddSpin, extent=60, style=tk.ARC, outline="#bbbbbb", width=5)
        arc2 = canvas.create_arc(*arc_bbox, start=225 + degree - totalAddSpin, extent=60, style=tk.ARC, outline="#bbbbbb", width=5)
 

        if additionalSpin > 0:
            increment = max(1, int(additionalSpin * 0.15))
            totalAddSpin += increment
            additionalSpin -= increment

        canvas.after(16, update)

    arc1 = None
    arc2 = None
    update()

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
            (circle_bbox[0] + circle_bbox[2]) // 2, (circle_bbox[1] + circle_bbox[3]) // 2 + 140, # Relative to circle_bbox
            text=newState,
            fill="#bbbbbb",
            font=("Arial", 13)
        )

        window.after(100, update)

    update()

# Text for command/response
commandValue = ""
command_text = None
commandCenter = [650, 620]

def updateCommandText():
    global command_text

    def update():
        global command_text

        if command_text is not None:
            canvas.delete(command_text)
        
        command_text = canvas.create_text(
            *commandCenter,
            text=commandValue,
            fill="#999999",
            font=("Arial", 15, "bold"),
            width=1000,
            anchor="center"
        )

        window.after(100, update)

    update()

def smooth_move(widget, new_position):
    global circle_bbox, commandCenter

    closeness = []
    if widget == "circle":
        for i in range(len(circle_bbox)):
            increment = int((new_position[i] - circle_bbox[i]) * 0.2)
            circle_bbox[i] += increment
            closeness.append(abs(new_position[i] - circle_bbox[i]))
    elif widget == "command":
        for i in range(len(commandCenter)):
            increment = int((new_position[i] - commandCenter[i]) * 0.15)
            commandCenter[i] += increment
            closeness.append(abs(new_position[i] - commandCenter[i]))

    if all(c < 1 for c in closeness):
        if widget == "circle":
            circle_bbox = new_position
        elif widget == "command":
            commandCenter = new_position
    else:
        window.after(16, smooth_move, widget, new_position)

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
    global state, commandValue, additionalSpin, cameraOpen

    state = "Idle"
    text = listen_text()

    if "computer" in text:
        task_queue.put(bring_to_front)
        state = "Listening"
        additionalSpin = 180
        command = listen_text()
        commandValue = command

        if command.strip():
            intent = model.predict([command])[0]
            entities = extract_from_intent(intent, command)
            if intent == "openapp" and entities.get("appName", None) == "Camera":
                cameraOpen = True
                # Move circle bbox to the bottom right
                task_queue.put(lambda: smooth_move("circle", [1090, 530, 1270, 720]))
           
                # Move command text to the bottom center
                task_queue.put(lambda: smooth_move("command", [650, 775]))
                
                result = "Opening Camera test..."
            else:
                result = route(intent, entities)

            commandValue = result
            asyncio.run(speak(result))

    # Loop again
    task_queue.put(start_model)


def start_model():
    threading.Thread(target=model_mainloop, daemon=True).start()

window.after(0, process_queue)
window.after(0, updateCircle)
window.after(0, updateStateText)
window.after(0, updateCommandText)
window.after(0, animateArcs)
window.after(0, start_model)
window.mainloop()