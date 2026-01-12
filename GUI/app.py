import tkinter as tk
from tkinter import font
from tkinter import ttk
from PIL import ImageTk, Image
import sv_ttk
import threading, json, time

from serial_client import open_first_available
import pico_runner
from export import save_to_pdf
from ring import build_ring
from noise_workflow import noise_measurement
from linear_workflow import linear_measurement#


# --------------- VARIABLES 
ARDUINO_PORTS = ["COM3", "COM5", "COM9"]
pico_plot_time = []
pico_plot_volt = []
pico_time = []
pico_volt = []
pico_pdf_time = []

# --------------- GUI VARIABLES
noise_win = None
AMLogo = Image.open('AMLogo.jpg')
scale = 0.8
w, h = AMLogo.size
smallLogo = AMLogo.resize((int(w*scale), int(h*scale)))


# --------------- PRESETS LADEN
preset_path = "preset_Teile.json"

def load_presets():
    try:
        with open (preset_path, "r", encoding="utf-8") as p:
            return json.load(p)
    except Exception as e:
        print("Fehler beim laden von Presets.", e)
presets = load_presets()

def set_entry(txt_entry, decimal_val):
    if isinstance(decimal_val, (int, float)):
        val = f"{decimal_val}".replace('.' , ',')
    else:
        val = str(decimal_val)
    txt_entry.delete(0, tk.END)
    txt_entry.insert(0, val)
    
def insert_preset(p):
    set_entry(txt_volt, p["sollSpannung"])
    set_entry(txt_angle, p["sollWinkel"])


# --------------- GUI FUNCTIONS
def close_window():
    root.destroy()

def open_noise_win():
    def close_wait_results():
        wait_win.destroy()

        if stop_event.is_set():
            global cancelled_win
            
            cancelled_win = tk.Toplevel(root)
            cancelled_win.title("Abbruch")
            cancelled_win.geometry(f"{scr_wid//4}x{scr_hei//4}+{scr_wid//2}+{scr_hei//2}")
            cancelled_win.grid_rowconfigure(0, weight=1)
            cancelled_win.grid_rowconfigure(1, weight=1)
            cancelled_win.grid_columnconfigure(0, weight=1)
            
            ttk.Label(cancelled_win, text="Vorgang wurde abgebrochen.").grid(row=0, column=0)
            ok_button = ttk.Button(cancelled_win, text="OK", command=cancelled_win.destroy)
            ok_button.grid(row=1, column=0, pady=(0, 20), ipadx=20)
            ok_button.focus_set()  
            cancelled_win.bind("<Return>", lambda event: ok_button.invoke())
        else:
            global noise_win
            if noise_win is not None and noise_win.winfo_exists():
                noise_win.destroy()

    try:
        txt_soll = float(txt_volt.get().strip().replace(',', '.'))
        txt_winkel = float(txt_angle.get().strip().replace(',', '.'))
        txt_geschw = float(txt_speed.get().strip().replace(',', '.'))

    except ValueError:
        error_win = tk.Toplevel(root)
        error_win.title("Falsche Eingabe!")
        error_win.geometry(f"{scr_wid//8}x{scr_hei//8}+{scr_wid//2}+{scr_hei//2}")
        error_win.resizable(False, False)
        error_win.transient(root)
        error_win.grab_set()
        error_win.grid_rowconfigure(0, weight=1)
        error_win.grid_rowconfigure(1, weight=1)
        error_win.grid_columnconfigure(0, weight=1)
        error_win.bell()
        ttk.Label(error_win, text="Leeres Feld gefunden!").grid(row=0, column=0)
        ok_button = ttk.Button(error_win, text="OK", command=error_win.destroy)
        ok_button.grid(row=1, column=0, ipadx=20)
        ok_button.focus_set()
        error_win.bind("<Return>", lambda event: ok_button.invoke())
        return
        
    wait_win = tk.Toplevel(root)
    wait_win.title("Datenmessung")
    wait_win.geometry(f"{scr_wid//8}x{scr_hei//8}+{scr_wid//2}+{scr_hei//2}")
    wait_win.transient(root)
    wait_win.grab_set()
    wait_win.resizable(False, False)
    ttk.Label(wait_win, text="Bitte warten...").pack(pady=30)

    
    stop_event = threading.Event()    
    def cancel_close():
        stop_event.set()
        wait_win.destroy()
    wait_win.protocol("WM_DELETE_WINDOW", cancel_close)


    threading.Thread(target=noise_measurement, args=(txt_winkel, txt_geschw, 
                                                   stop_event, close_wait_results), daemon=True).start()

def open_linear_win():
    def close_wait_results():
        wait_win.destroy()

        if stop_event.is_set():
            global cancelled_win
            
            cancelled_win = tk.Toplevel(root)
            cancelled_win.title("Abbruch")
            cancelled_win.geometry(f"{scr_wid//4}x{scr_hei//4}+{scr_wid//2}+{scr_hei//2}")
            cancelled_win.grid_rowconfigure(0, weight=1)
            cancelled_win.grid_rowconfigure(1, weight=1)
            cancelled_win.grid_columnconfigure(0, weight=1)
            
            ttk.Label(cancelled_win, text="Vorgang wurde abgebrochen.").grid(row=0, column=0)
            ok_button = ttk.Button(cancelled_win, text="OK", command=cancelled_win.destroy)
            ok_button.grid(row=1, column=0, pady=(0, 20), ipadx=20)
            ok_button.focus_set()  
            cancelled_win.bind("<Return>", lambda event: ok_button.invoke())
        else:
            global linear_win
            if linear_win is not None and linear_win.winfo_exists():
                linear_win.destroy()

    try:
        txt_soll = float(txt_volt.get().strip().replace(',', '.'))
        txt_winkel = float(txt_angle.get().strip().replace(',', '.'))
        txt_geschw = float(txt_speed.get().strip().replace(',', '.'))

    except ValueError:
        error_win = tk.Toplevel(root)
        error_win.title("Falsche Eingabe!")
        error_win.geometry(f"{scr_wid//8}x{scr_hei//8}+{scr_wid//2}+{scr_hei//2}")
        error_win.resizable(False, False)
        error_win.transient(root)
        error_win.grab_set()
        error_win.grid_rowconfigure(0, weight=1)
        error_win.grid_rowconfigure(1, weight=1)
        error_win.grid_columnconfigure(0, weight=1)
        error_win.bell()
        ttk.Label(error_win, text="Leeres Feld gefunden!").grid(row=0, column=0)
        ok_button = ttk.Button(error_win, text="OK", command=error_win.destroy)
        ok_button.grid(row=1, column=0, ipadx=20)
        ok_button.focus_set()
        error_win.bind("<Return>", lambda event: ok_button.invoke())
        return
        
    wait_win = tk.Toplevel(root)
    wait_win.title("Datenmessung")
    wait_win.geometry(f"{scr_wid//8}x{scr_hei//8}+{scr_wid//2}+{scr_hei//2}")
    wait_win.transient(root)
    wait_win.grab_set()
    wait_win.resizable(False, False)
    ttk.Label(wait_win, text="Bitte warten...").pack(pady=30)

    
    stop_event = threading.Event()    
    def cancel_close():
        stop_event.set()
        wait_win.destroy()
    wait_win.protocol("WM_DELETE_WINDOW", cancel_close)


    threading.Thread(target=linear_measurement, args=(txt_winkel, txt_geschw, 
                                                   stop_event, close_wait_results), daemon=True).start()

    

def go_zero(stop_event, on_finish):
    try:
        ser_Arduino = open_first_available(ARDUINO_PORTS, baud=115200, timeout=5)
        ser_Arduino.reset_input_buffer() 
        ser_Arduino.reset_output_buffer()
        time.sleep(1)
        print("zero geschrieben")
        ser_Arduino.write(b"ZERO\n")
        ser_Arduino.timeout = 0.1
        while True:
            if stop_event.is_set():
                ser_Arduino.write(b"STOP\n")
                ser_Arduino.flush()
                time.sleep(0.2)
                break
            line = ser_Arduino.readline().decode('utf-8').strip()
            print("Empfangen:", line) #debug
            if line == 'READY':
                break
            if line == 'CANCEL':
                break
        ser_Arduino.close()
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

    root.after(0, on_finish)


def export_pdf():
    save_to_pdf(txt9, pico_plot_time, pico_pdf_time, pico_plot_volt, pico_volt)

# --------------- OPEN ZERO WINDOW
def open_zero_window():
    def close_wait_results():
        wait_win.destroy()

        if stop_event.is_set():
            global cancelled_win
            
            cancelled_win = tk.Toplevel(root)
            cancelled_win.title("Abbruch")
            cancelled_win.geometry(f"{scr_wid//4}x{scr_hei//4}+{scr_wid//2}+{scr_hei//2}")
            cancelled_win.grid_rowconfigure(0, weight=1)
            cancelled_win.grid_rowconfigure(1, weight=1)
            cancelled_win.grid_columnconfigure(0, weight=1)
            
            ttk.Label(cancelled_win, text="Vorgang wurde abgebrochen.").grid(row=0, column=0)
            ok_button = ttk.Button(cancelled_win, text="OK", command=cancelled_win.destroy)
            ok_button.grid(row=1, column=0, pady=(0, 20), ipadx=20)
            ok_button.focus_set()  
            cancelled_win.bind("<Return>", lambda event: ok_button.invoke())
        else:
            global noise_win
            if noise_win is not None and noise_win.winfo_exists():
                noise_win.destroy()

            noise_win = tk.Toplevel(root)
            noise_win.title("Fertig")
            noise_win.geometry(f"{scr_wid//4}x{scr_hei//4}+{scr_wid//2}+{scr_hei//2}")
            noise_win.grid_rowconfigure(0, weight=1)
            noise_win.grid_rowconfigure(1, weight=1)
            noise_win.grid_columnconfigure(0, weight=1)
            
            ttk.Label(noise_win, text="Position ist auf 0.").grid(row=0, column=0)
            ok_button = ttk.Button(noise_win, text="OK", command=noise_win.destroy)
            ok_button.grid(row=1, column=0, pady=(0, 20), ipadx=20)
            ok_button.focus_set()  
            noise_win.bind("<Return>", lambda event: ok_button.invoke())
        
    wait_win = tk.Toplevel(root)
    wait_win.title("Position nullen")
    wait_win.geometry(f"{scr_wid//8}x{scr_hei//8}+{scr_wid//2}+{scr_hei//2}")
    wait_win.transient(root)
    wait_win.grab_set()
    wait_win.resizable(False, False)
    ttk.Label(wait_win, text="Bitte warten...").pack(pady=30)

    stop_event = threading.Event()    
    def cancel_close():
        stop_event.set()
        wait_win.destroy()
    wait_win.protocol("WM_DELETE_WINDOW", cancel_close)
    threading.Thread(target=go_zero, args=(stop_event, close_wait_results), daemon=True).start()


# --------------- GUI
root = tk.Tk()
scr_wid = root.winfo_screenwidth()
scr_hei = root.winfo_screenheight()
root.geometry(f"{scr_wid - scr_wid//5}x{scr_hei - scr_hei//5}+0+0")
root.title("Rauschprüfung")
root.resizable(False, False)


root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(1, weight=1)

left_frame  = ttk.Frame(root)
right_frame = ttk.Frame(root)
left_frame.grid(row=1, column=0, sticky="nw", padx=12, pady=12)
right_frame.grid(row=1, column=1, sticky="nw",  padx=12, pady=12)
ring_area = ttk.Frame(root)
ring_area.grid(row=1, column=2, sticky="nw",  padx=120, pady=12)

img = ImageTk.PhotoImage(smallLogo)
panel = tk.Label(root, image=img)
panel.image = img    
panel.grid(row=0, column=0, columnspan=2,padx=24, pady=24, sticky="nw")

ttk.Label(left_frame, text="Bauteil Preset:").grid(row=0, column=0, sticky="w", pady=(10, 0), padx=(20,0))
preset_names = list(presets.keys()) 
preset_combo = ttk.Combobox(left_frame, values=preset_names, state="readonly", width=16)
preset_combo.grid(row=1, column=0, sticky="w", padx=(20,0))
preset_combo.current(0)

def on_select_preset(event=None):
    name = preset_combo.get()
    if name in presets:
        insert_preset(presets[name])

preset_combo.bind("<<ComboboxSelected>>", on_select_preset)


right_frame.grid_columnconfigure(1, weight=0)
# right_frame.grid_rowconfigure(0, weight=0)

vcmd = (root.register(lambda P: (P.count(',') <= 1 and all(ch.isdigit() or ch == ',' for ch in P))), "%P")

ttk.Label(left_frame, text="Auftragsnummer:").grid(row=4, column=0, sticky="w", pady=(20, 0), padx=(20,0))
txt9 = ttk.Entry(left_frame, width=20)
txt9.grid(row=5, column=0, pady=(0, 10), padx=(20,0))

ttk.Label(right_frame, text="Sollspannung in V:").grid(row=1, column=0, sticky="w", pady=(40, 0), padx=(10,0))
txt_volt = ttk.Entry(right_frame, width=20, validate="key", validatecommand=vcmd)
txt_volt.grid(row=2, column=0, pady=(0, 0), padx=(0,0))
txt_volt.insert(0, "5,0")
txt_volt.focus_set()
ttk.Label(right_frame, text="Gesamtwinkel in Grad:").grid(row=3, column=0, sticky="w", pady=(40, 0), padx=(10,0))
txt_angle = ttk.Entry(right_frame, width=20, validate="key", validatecommand=vcmd)
txt_angle.grid(row=4, column=0, pady=(0, 0), padx=(0,0))
txt_angle.insert(0, "330,0")
ttk.Label(right_frame, text="Max. Geschwindigkeit in U/min:").grid(row=5, column=0, sticky="w", pady=(40, 0), padx=(10,0))
txt_speed = ttk.Entry(right_frame, width=20, validate="key", validatecommand=vcmd)
txt_speed.grid(row=6, column=0, pady=(0, 0), padx=(0,0))
txt_speed.insert(0, "60,0")


# txtgo = ttk.Entry(left_frame, width=20, validate="key", validatecommand=vcmd)
# txtgo.grid(row=3, column=1, pady=(0, 0), padx=(0,0))

ttk.Button(left_frame, text="Abbrechen", command=close_window).grid(row=7, column=0, pady=(4, 5), padx=(0,0), ipadx=40)
ttk.Button(left_frame, text="Messen", command=open_noise_win).grid(row=6, column=0, pady=(80, 5), padx=(0,0), ipadx=40)
ttk.Button(right_frame, text="Rauschkurve speichern", command=export_pdf).grid(row=7, column=0, pady=(107, 5), padx=(0,0), ipadx=10)
ttk.Button(left_frame, text="Position 0", command=open_zero_window).grid(row=8, column=0, pady=(80, 5), padx=(0,0), ipadx=40)
# ttk.Button(left_frame, text="0.1 Links", command=go_left).grid(row=6, column=1, pady=(4, 5), padx=(0,0), ipadx=40)
# ttk.Button(left_frame, text="0.1 Rechts", command=go_Right).grid(row=7, column=1, pady=(4, 5), padx=(0,0), ipadx=40)
# ttk.Button(left_frame, text="Conn Serial", command=ser_Connect).grid(row=5, column=1, pady=(4, 5), padx=(0,0), ipadx=40)
# ttk.Button(left_frame, text="Curr Position", command=curr_Pos).grid(row=8, column=1, pady=(4, 5), padx=(0,0), ipadx=40)
# ttk.Button(left_frame, text="Go To", command=goto).grid(row=4, column=1, pady=(4, 5), padx=(0,0), ipadx=40)

txt_volt.bind("<Return>", lambda event: open_noise_win())
txt_angle.bind("<Return>", lambda event: open_noise_win())
txt9.bind("<Return>", lambda event: open_noise_win())
root.bind("<Escape>", lambda event: close_window())


# --------------- MAIN
build_ring(ring_area)
on_select_preset()
sv_ttk.set_theme("dark")
root.mainloop()