import math
import tkinter as tk
from tkinter import font


# --------------- GUI RING VARIABLES
ring_canvas = None
ring_box = None
noise_times = []


# --------------- GUI RING FUNCTIONS
def build_ring(frame, ring_size = 300, ring_thickness = 4, bg="#969696"):
    global ring_canvas, ring_box
    ring_canvas = tk.Canvas(
        frame, width=ring_size+30, height=ring_size+30,
        bg=bg
    )
    ring_canvas.pack()
    canv_x = canv_y = ring_size // 2 + 15
    radius = (ring_size // 2) - 18
    ring_box = (canv_x - radius, canv_y - radius, canv_x + radius, canv_y + radius)
    ring_canvas.create_arc(ring_box, start=0, extent=359.9,
                           style="arc", width=ring_thickness, outline="#1c1c1c")
    
    for deg in range(0, 360, 10):
        long_tick = (deg % 30 == 0)
        L = 30 if long_tick else 12
        rad = math.radians(deg - 90)
        x0 = canv_x + (radius + ring_thickness/2) * math.cos(rad)
        y0 = canv_y + (radius + ring_thickness/2) * math.sin(rad)
        x1 = canv_x + (radius + L) * math.cos(rad)
        y1 = canv_y + (radius + L) * math.sin(rad)
        ring_canvas.create_line(x0, y0, x1, y1, width=4, fill="#ffffff")

def mark_deadzone(total_ticks, ring_size = 300, ring_thickness = 4):
    fix_direction = -90
    line_span = (total_ticks/4096)*360
    line_side = line_span/2
    L = 50

    clear_noise_marks()
    
    for deg in range(-1,2,2):
        canv_x = canv_y = ring_size // 2 + 15
        radius = (ring_size // 2) - 18
        rad = math.radians(deg*line_side + fix_direction)
        x0 = canv_x + (radius + ring_thickness/2- L/2) * math.cos(rad)
        y0 = canv_y + (radius + ring_thickness/2- L/2) * math.sin(rad)
        x1 = canv_x + (radius + L+ L/2) * math.cos(rad)
        y1 = canv_y + (radius + L+ L/2) * math.sin(rad)
        iid = ring_canvas.create_line(x0, y0, x1, y1, width=8, fill="#00ffff")
        noise_times.append(iid)

def mark_ends(total_ticks, ring_size = 300, ring_thickness = 4):
    fix_direction = -90
    line_span = (total_ticks/4096)*360
    line_side = line_span/2
    L = 50

    clear_noise_marks()
    
    for deg in range(-1,2,2):
        canv_x = canv_y = ring_size // 2 + 15
        radius = (ring_size // 2) - 18
        rad = math.radians(deg*line_side + fix_direction)
        x0 = canv_x + (radius + ring_thickness/2- L/2) * math.cos(rad)
        y0 = canv_y + (radius + ring_thickness/2- L/2) * math.sin(rad)
        x1 = canv_x + (radius + L+ L/2) * math.cos(rad)
        y1 = canv_y + (radius + L+ L/2) * math.sin(rad)
        iid = ring_canvas.create_line(x0, y0, x1, y1, width=8, fill="#00ffff")
        noise_times.append(iid)

def clear_noise_marks():
    global noise_times
    for iid in noise_times:
        ring_canvas.delete(iid)
    noise_times = []

def mark_noise_segments(angle_arr, ring_thickness = 4, color="#ff0000"):
    global noise_times
    fix_direction = -90

    angle_pos = [0] * 73
    angle_mult = 5
    for i in range(1, len(angle_pos), 1):
        for j in range(len(angle_arr)):
            if angle_arr[j] < angle_mult * i and angle_arr[j] >= angle_mult * (i-1):
                angle_pos[i] = 1
                break
    
    for i in range(1, len(angle_pos),1):
        tol_left = angle_mult*i + fix_direction+3
        tol_right = -6
        if(angle_pos[i] == 1):
            iid = ring_canvas.create_arc(ring_box, start=tol_left, extent=tol_right,
                                     style="arc", width=ring_thickness+10, outline="#ff0000")
            noise_times.append(iid)

def set_circle_text(pico_angle):
    x0, y0, x1, y1 = ring_box
    canv_x = (x0 + x1) / 2
    canv_y = (y0 + y1) / 2
    text_font = font.Font(family="Arial", size=20, weight="bold")

    if not pico_angle:
        iid = ring_canvas.create_text(
                canv_x, canv_y, text="In Ordnung", fill="#00ff33",
                font=text_font, anchor="center")
    else:
        iid = ring_canvas.create_text(
                canv_x, canv_y, text="Fehler", fill="#ff0000",
                font=text_font, anchor="center")
    noise_times.append(iid)
