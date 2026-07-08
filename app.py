import tkinter as tk
import threading
import joblib
import os
import speech_recognition as sr
import edge_tts
import asyncio
import subprocess
import queue
import faulthandler
import cv2
import mediapipe as mp
from PIL import Image, ImageTk
from time import time
from math import sin
from extract_entities import extract_from_intent
from intent_router import route

faulthandler.enable()  # Prints a native stack trace to stderr if we segfault

model_path = "intent_model.joblib"

if not os.path.exists(model_path):
    import train_intent_model  # This will run the code inside the file, creating the model

model = joblib.load(model_path)
r = sr.Recognizer()
r.pause_threshold = 1.0  # Seconds of silence before ending the phrase
r.energy_threshold = 700  # Adjust as needed for your mic volume

mic = sr.Microphone()
voice = "en-AU-WilliamNeural"
cap = None
cameraOpen = False
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Camera capture + hand-tracking run on their own background thread so the
# (comparatively slow) cv2.read()/mediapipe work never blocks the Tk mainloop.
camera_lock = threading.Lock()
camera_thread_running = False
latest_camera_data = {"img": None, "gesture": "No Hand Found"}

FINGER_TIPS = [4, 8, 12, 16, 20]   # Thumb, Index, Middle, Ring, Pinky
FINGER_PIPS = [3, 6, 10, 14, 18]   # Just below the tips
GESTURES = {
    "Moving Cursor": ["Thumb", "Index", "Middle", "Ring", "Pinky"],
    "Moving Widget": []
}

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

video_bbox = [0, 0, 1300, 800]
# video_bbox = [25, 25, 1275, 775]
video_image_id = None
video_photo = None
hand_gesture_text = None

def bring_to_front():
    window.lift()
    window.attributes("-topmost", True)
    window.update()
    window.attributes("-topmost", False)
    window.focus_force()

canvas = tk.Canvas(window, width=windowWidth, height=windowHeight, bg="#333333", highlightthickness=0)
canvas.place(x=0, y=0)

for i in range(0, 2 * windowWidth // 25):
    canvas.create_line(25 * i, 0, 25 * i, windowHeight, width=1, fill="black", tags="grid")
    canvas.create_line(0, 25 * i, windowWidth, 25 * i, width=1, fill="black", tags="grid")

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
    global arc1, arc2

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
command_text_bg = None
commandCenter = [650, 620]

def updateCommandText():
    def update():
        global command_text, command_text_bg

        if command_text is not None:
            canvas.delete(command_text)
        if command_text_bg is not None:
            canvas.delete(command_text_bg)
        
        temp_text = canvas.create_text(
            *commandCenter,
            text=commandValue,
            font=("Arial", 15, "bold"),
            width=1000,
            anchor="center",
            fill="#999999"
        )

        bbox = canvas.bbox(temp_text)
        if bbox and cameraOpen and commandValue:
            rect_padding = 8
            command_text_bg = canvas.create_rectangle(
                bbox[0] - rect_padding,
                bbox[1] - rect_padding,
                bbox[2] + rect_padding,
                bbox[3] + rect_padding,
                fill="black",
                outline=""
            )
            # Raise text above the rectangle
            canvas.tag_raise(temp_text, command_text_bg)
        command_text = temp_text

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

def detect_gesture(result, frame_shape):
    """Pure function: mediapipe result -> gesture label. No Tk, no I/O."""
    if not result.multi_hand_landmarks:
        return "No Hand Found"

    hand_landmarks = result.multi_hand_landmarks[-1]  # Only look at one hand

    # Find hand type (left/right); default to right if not present
    hand_type = "Right"
    if hasattr(result, "multi_handedness"):
        try:
            hand_type = result.multi_handedness[-1].classification[0].label
        except Exception:
            pass

    h, w, _ = frame_shape
    landmarks_px = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]

    # Thumb: direction of "open" flips depending on handedness
    finger_states = []
    if hand_type == "Right":
        if landmarks_px[4][0] < landmarks_px[3][0]:
            finger_states.append("Thumb")
    else:
        if landmarks_px[4][0] > landmarks_px[3][0]:
            finger_states.append("Thumb")

    # Other fingers: tip.y < pip.y = open
    for i, name in zip([1, 2, 3, 4], ["Index", "Middle", "Ring", "Pinky"]):
        if landmarks_px[FINGER_TIPS[i]][1] < landmarks_px[FINGER_PIPS[i]][1]:
            finger_states.append(name)

    for gesture_name, required_fingers in GESTURES.items():
        if set(required_fingers) == set(finger_states):
            return gesture_name

    return "No Gesture Recognized"


def resize_cover(frame, target_w, target_h):
    """Scale `frame` up to fully cover a target_w x target_h box while
    keeping its aspect ratio, then center-crop the overflow. Avoids the
    stretched/distorted look a plain cv2.resize gives when the camera's
    aspect ratio doesn't match the display box."""
    h, w = frame.shape[:2]
    scale = max(target_w / w, target_h / h)
    new_w, new_h = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(frame, (new_w, new_h))

    x0 = (new_w - target_w) // 2
    y0 = (new_h - target_h) // 2
    return resized[y0:y0 + target_h, x0:x0 + target_w]

def camera_worker():
    """Runs on a background thread: owns the camera and the Hands() model.
    Never touches Tk widgets -- it just drops the latest finished frame into
    latest_camera_data for the UI thread to pick up whenever it's ready."""
    global cap

    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    # Capture at a modest fixed resolution instead of whatever the camera's
    # default happens to be (often 1080p) -- less data to move/convert/detect on.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 60)

    display_w = video_bbox[2] - video_bbox[0]
    display_h = video_bbox[3] - video_bbox[1]

    # video_bbox doesn't change size at runtime, so this can be built once
    # instead of every single frame.
    alpha_layer = Image.new("L", (display_w, display_h), int(255 * 0.75))

    # A dedicated Hands instance for this thread. max_num_hands=1 and
    # model_complexity=0 use the lighter/faster model, which is all we need
    # since detect_gesture() only ever looks at one hand.
    hands_local = mp_hands.Hands(
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    while cameraOpen:
        if not cap.isOpened():
            continue

        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # convert once, reuse below

        # Detect on the small native-resolution frame, NOT an upscaled copy --
        # mediapipe's cost scales with input size, and we don't need 1300x800
        # for landmark accuracy.
        result = hands_local.process(rgb_frame)
        gesture_display = detect_gesture(result, frame.shape)

        display_rgb = resize_cover(rgb_frame, display_w, display_h)
        img = Image.fromarray(display_rgb).convert("RGBA")
        img.putalpha(alpha_layer)

        with camera_lock:
            latest_camera_data["img"] = img
            latest_camera_data["gesture"] = gesture_display

    hands_local.close()
    if cap is not None:
        cap.release()
        cap = None


def start_camera():
    global camera_thread_running
    if not camera_thread_running:
        camera_thread_running = True
        threading.Thread(target=camera_worker, daemon=True).start()


def update_camera_frame():
    """Runs on the Tk mainloop via window.after. Only touches the canvas --
    all the slow camera/mediapipe work happens in camera_worker() above, so
    this stays cheap and the UI never blocks on cap.read()."""
    global video_image_id, video_photo, hand_gesture_text

    if not cameraOpen:
        return

    with camera_lock:
        img = latest_camera_data["img"]
        gesture_display = latest_camera_data["gesture"]

    if img is not None:
        video_photo = ImageTk.PhotoImage(image=img)

        if hand_gesture_text is not None:
            canvas.delete(hand_gesture_text)

        hand_gesture_text = canvas.create_text(
            video_bbox[0] + 20, video_bbox[1] + 20,
            text=gesture_display,
            fill="black",
            anchor="nw",
            font=("Arial", 18, "bold"),
            tags="gesture_text"
        )

        if video_image_id is None:
            # Video background
            canvas.create_rectangle(
                *video_bbox,
                fill="#444444", outline="", tags="video_bg"
            )
            video_image_id = canvas.create_image(
                video_bbox[0], video_bbox[1],
                image=video_photo, anchor="nw", tags="video"
            )
        else:
            canvas.itemconfig(video_image_id, image=video_photo)
        canvas.tag_lower("grid", "video_bg")
        canvas.tag_lower("video_bg", "video")
        canvas.tag_raise("gesture_text")

    window.after(15, update_camera_frame)

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
                start_camera()  # launch the background capture/mediapipe thread

                # Move circle bbox to the bottom right
                task_queue.put(lambda: smooth_move("circle", [1090, 530, 1270, 720]))
           
                # Move command text to the bottom center
                task_queue.put(lambda: smooth_move("command", [650, 765]))
                
                # Show the camera frame
                task_queue.put(update_camera_frame)

                result = "Opening Camera test..."
            else:
                result = route(intent, entities)

            commandValue = result
            asyncio.run(speak(result))

    # Loop again
    task_queue.put(start_model)


def start_model():
    threading.Thread(target=model_mainloop, daemon=True).start()

def on_close():
    global cameraOpen
    cameraOpen = False  # camera_worker sees this and releases cap itself
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_close)

window.after(0, process_queue)
window.after(0, updateCircle)
window.after(0, updateStateText)
window.after(0, updateCommandText)
window.after(0, animateArcs)
window.after(0, start_model)
window.mainloop()