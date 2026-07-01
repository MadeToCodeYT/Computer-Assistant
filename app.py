# window size: 1100x700 fixed

import tkinter as tk
from time import time
from math import sin

window = tk.Tk()
window.title("Computer Assistant")
window.geometry(f"1100x700+{(window.winfo_screenwidth()-1100)//2}+{(window.winfo_screenheight()-700)//2}")

canvas = tk.Canvas(window, width=1100, height=700, bg="white", highlightthickness=0)
canvas.place(x=0, y=0)

canvas.create_rectangle(0, 0, 1100, 700, fill="#333333", outline="")

for i in range(0, 2 * 1100 // 25):
    # Draw diagonal lines from left to right across the canvas
    canvas.create_line(25 * i, 0, 25 * i, 700, width=1, fill="black")
    # Draw horizontal lines across the canvas
    canvas.create_line(0, 25 * i, 1100, 25 * i, width=1, fill="black")

# Circle at the center of the screen
canvas.create_oval(
    470, 270, 630, 430, # Bounding box (x1,y1),(x2,y2)
    fill="#222222",
    outline="#bbbbbb",
    width=4
)

def animateArcs():
    global arc1
    global arc2

    def update():
        global arc1, arc2
   
        degree = 30 * sin(time())
        if arc1:
            canvas.delete(arc1)
        if arc2:
            canvas.delete(arc2)
        arc1 = canvas.create_arc(450, 250, 650, 450, start=45+degree, extent=60, style=tk.ARC, outline="#bbbbbb", width=5)
        arc2 = canvas.create_arc(450, 250, 650, 450, start=225+degree, extent=60, style=tk.ARC, outline="#bbbbbb", width=5)

        canvas.after(16, update)  # ~60 fps

    arc1 = None
    arc2 = None
    update() # Starts the chain

# Text for inside the circle
canvas.create_text(
    550, 350,
    text="Computer",
    fill="white",
    font=("Arial", 15, "bold")
)

# Text for current state
canvas.create_text(
    550, 485,
    text="Idle",
    fill="#bbbbbb",
    font=("Arial", 13)
)


window.after(0, animateArcs())
window.after(2000, window.destroy)
window.mainloop()