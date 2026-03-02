import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image
import sv_ttk
import threading, json


from export import save_to_pdf, save_to_excel
import ring
import noise_workflow
import linear_workflow
import mech_ends_workflow
import elec_deg_workflow
from tester import tests
import side_functions
import pico_runner
import serial_client as sc

# --------------- APP VARIABLES 
# ARDUINO_PORTS = ["COM3", "COM5", "COM9"]
pico_plot_time = []
pico_plot_volt = []
pico_time = []
pico_volt = []
pico_pdf_time = []
pico_angle = []

# --------------- GUI VARIABLES
noise_win = None
linear_win = None
zero_win = None
cancelled_win = None

AMLogo = Image.open('AMLogo.jpg')
scale = 0.8
w, h = AMLogo.size
smallLogo = AMLogo.resize((int(w*scale), int(h*scale)))
text_rw_state = 'readonly'
deadzone_after_id = None
debounce_id = {"id": None}
output_ends = False

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
    if decimal_val is None:
        val = ""
    elif isinstance(decimal_val, (int, float)):
        val = f"{decimal_val}".replace('.' , ',')
    else:
        val = str(decimal_val)
    
    text_rw_state = 'normal'
    txt_entry.configure(state=text_rw_state)
    txt_entry.delete(0, tk.END) 
    txt_entry.insert(0, val)
    text_rw_state = 'readonly'
    txt_entry.configure(state=text_rw_state)
    
def insert_preset(p):
    set_entry(txt_volt, p["soll_spannung_linear"])
    set_entry(txt_angle, p["soll_winkel"])
    set_entry(txt_speed, p["soll_geschwindigkeit"])
    set_entry(txt_d11, p["d11"])
    set_entry(txt_d12, p["d12"])
    set_entry(txt_d21, p["d21"])
    set_entry(txt_d22, p["d22"])
    set_entry(txt_d31, p["d31"])
    set_entry(txt_d32, p["d32"])
    comment = (p.get("comment") or "").strip()
    msg.configure(text=comment)

    if comment == "":
        msg.grid_remove()
    else:
        msg.grid(row=8, column=0,pady=(10, 10), padx=(20, 0))

dropdown = {"win": None, "listbox": None}
MAX_SUGGESTIONS = 10

def only_digits(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())

def rank_presets(query: str, ids: list[str]) -> list[str]:
    matches = []
    q = query
    if not q:
        return []
    for pid in ids:
        if pid.startswith(q):
            matches.append(pid)
    matches.sort()
    return matches[:MAX_SUGGESTIONS]

def on_up_dropdown():
    if dropdown["win"] is not None and dropdown["win"].winfo_exists():
        dropdown["win"].destroy()
    dropdown["win"] = None
    dropdown["listbox"] = None
   
def open_dropdown(anchor_entry: ttk.Entry):
    if dropdown["win"] is not None and dropdown["win"].winfo_exists():
        return

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True) 
    win.configure(bg="#1c1c1c")

    lb = tk.Listbox(
    win,
    activestyle="none",
    exportselection=False,
    height=1,
    borderwidth=0,
    highlightthickness=1,
    relief="flat",
    )

    lb.configure(
        fg="white",
        bg="#2a2a2a",
        selectforeground="white",
        selectbackground="#444444",
        highlightbackground="#444444",
    )

    lb.pack(fill="both")

    dropdown["win"] = win
    dropdown["listbox"] = lb
    root.bind_all("<Button-1>", lambda e: click_outside(e, anchor_entry), add=True)

def position_dropdown(anchor_entry: ttk.Entry, n_rows: int):
    win = dropdown["win"]
    if win is None or not win.winfo_exists():
        return
    
    x = anchor_entry.winfo_rootx()
    y = anchor_entry.winfo_rooty() + anchor_entry.winfo_height()

    w = anchor_entry.winfo_width()
    row_h = 22
    h = max(1, min(n_rows, MAX_SUGGESTIONS)) * row_h + 2

    win.geometry(f"{w}x{h}+{x}+{y}")

def click_outside(event, anchor_entry: ttk.Entry):
    win = dropdown["win"]
    if win is None or not win.winfo_exists():
        return

    widget = event.widget
    if widget == anchor_entry or str(widget).startswith(str(win)):
        return
    select_from_list(preset_entry)
    on_up_dropdown()
    
def select_from_list(anchor_entry: ttk.Entry):
    lb = dropdown["listbox"]
    if lb is None:
        return
    sel = lb.curselection()
    if not sel:
        return
    pid = lb.get(sel[0])
    anchor_entry.delete(0, tk.END)
    anchor_entry.insert(0, pid)
    on_up_dropdown()

    if pid in presets:
        insert_preset(presets[pid])

def _update_dropdown(anchor_entry: ttk.Entry, query_var: tk.StringVar, preset_ids: list[str]):
    q_raw = query_var.get()
    q = only_digits(q_raw)

    if q_raw != q:
        query_var.set(q)
        return
    if not q:
        on_up_dropdown()
        return

    suggestions = rank_presets(q, preset_ids)
    if not suggestions:
        on_up_dropdown()
        return

    open_dropdown(anchor_entry)
    lb = dropdown["listbox"]
    lb.delete(0, tk.END)
    for s in suggestions:
        lb.insert(tk.END, s)
    lb.selection_clear(0, tk.END)
    lb.selection_set(0)
    lb.activate(0)
    n = len(suggestions)
    lb.configure(height=min(n, MAX_SUGGESTIONS)) 
    position_dropdown(anchor_entry, n) 

def decimal_conversion(s: str):
    s = (s or "").strip().replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None
    

# --------------- GUI FUNCTIONS
def on_up_window():
    root.destroy()

def start_measurements(modes, meas_volt, meas_angle, meas_speed):
    wait_win = tk.Toplevel(root)
    wait_win.title("Datenmessung")
    wait_win.geometry(f"{small_wid}x{170}+{scr_wid//2}+{scr_hei//2}")
    wait_win.transient(root)
    wait_win.grab_set()
    wait_win.resizable(False, False)
    
    status_label = ttk.Label(wait_win, text="Bitte warten...")
    status_label.pack(pady=(0,20), expand=True)
    stop_event = threading.Event()   

    mech_angle_var.set("Mechanischer Winkel: --")
    elec_angle_var.set("Elektrischer Winkel: --")

    def cancel():
        stop_event.set()
        wait_win.destroy()
    wait_win.protocol("WM_DELETE_WINDOW", cancel)

    def worker():
        #ser_arduino.busy = True    
        try:
            global measurements_finished
            measurements_finished = False
            global measurements_noise_found
            measurements_noise_found = False
            visible_total = sum(1 for m in modes if m[4] is True)
            visible_i = 0
            
            ser_ard = sc.connect_ard()
            ser_multi = sc.connect_multi()
            ser_psu = sc.connect_psu()

            ring.clear_noise_marks()

            for (workflow, workflow_args, title, needs_config, visible) in modes:
                if visible:
                    visible_i += 1
                    root.after(0, lambda t=title, i=visible_i, n=visible_total:
                            status_label.configure(text=f"Messung {i}/{n}:\n\n{t}", justify='center'))
                if needs_config:
                    #workflow.config(root, txt_speed, ser_arduino)
                    workflow.config(root, txt_speed, ser_ard, ser_psu, ser_multi)

                workflow.measurement(meas_volt, meas_angle, meas_speed, *workflow_args ,stop_event, lambda: None)
                
                if mech_ends_workflow.safety_cancel is True:
                    root.after(0, open_safety_win)
                    stop_event.set()
                    break
                if stop_event.is_set():
                    root.after(0, open_cancelled_window)
                    break
                if pico_runner.out_volt is True and modes:
                    stop_event.set()
                    measurements_noise_found = True
                    root.after(0, open_noise_found_win)
                    break
                if workflow is mech_ends_workflow or end_lin_checked is True:
                    val = getattr(mech_ends_workflow, "total_mech", None)
                    if isinstance(val, (int, float)):
                        root.after(0, lambda v=val: mech_angle_var.set(
                            f"Mechanischer Winkel: {v:.2f}°"
                        ))
                    else:
                        root.after(0, lambda: mech_angle_var.set(
                            "Mechanischer Winkel: --"
                        ))
                if workflow is elec_deg_workflow:
                    val = getattr(elec_deg_workflow, "total_elec", None)
                    if isinstance(val, (int, float)):
                        root.after(0, lambda v=val: elec_angle_var.set(
                            f"Elektrischer Winkel: {v:.2f}°"
                        ))
                    #else:
                    #    root.after(0, lambda: elec_angle_var.set(
                    #        "Elektrischer Winkel: --"
                    #    ))
            if not stop_event.is_set() or measurements_noise_found:
                measurements_finished = True
            ring.set_circle_text(pico_angle, noise_checked)
            
        except Exception as e:
            print("Fehler bei measurements:", e)


        if ser_ard: 
            ser_ard.close()
            print("[SERIAL] Arduino close")
        if ser_multi: 
            ser_multi.close()
            print("[SERIAL] Multimeter close")
        if ser_psu: 
            ser_psu.close()
            print("[SERIAL] PSU close")
        root.after(0, autosave_chk)
        root.after(0, wait_win.destroy)
    
    threading.Thread(target=worker, daemon=True).start()

def measurement_chk():
    global end_lin_checked
    end_lin_checked = False
    mech_ends_workflow.safety_cancel = False
    pico_runner.out_volt = False
    try:
        meas_volt = float(txt_volt.get().strip().replace(',', '.'))
        meas_angle = float(txt_angle.get().strip().replace(',', '.'))
        meas_speed = float(txt_speed.get().strip().replace(',', '.'))
    except ValueError:
        print("Eingabefehler bei Sollwerten!")
        return
    
    d11 = decimal_conversion(d11_var.get())
    d12 = decimal_conversion(d12_var.get())
    d21 = decimal_conversion(d21_var.get())
    d22 = decimal_conversion(d22_var.get())
    d31 = decimal_conversion(d31_var.get())
    d32 = decimal_conversion(d32_var.get())

    modes = []
    ends_checked = chk_ends_mode.get()
    modes.append((mech_ends_workflow, (), "Mech. Endwinkel", True, ends_checked))
    if ends_checked: print("[CHECKBOX] Mech. Ends")

    global noise_checked
    noise_checked = chk_noise_mode.get()
    if noise_checked:
        pico_plot_time.clear()
        pico_plot_volt.clear()
        modes.append((noise_workflow, (pico_plot_volt, pico_plot_time), "Rauschprüfung", True, True))
        print("[CHECKBOX] Rauschen")
    
    
    if chk_linear_mode.get() and chk_elec_mode.get():
        end_lin_checked = True
        modes.append((linear_workflow, (d11, d12, d21, d22, d31, d32), "Elektr. Winkel\n+\nLinearitätsprüfung", True, True))
        print("[CHECKBOX] Linearität und Elektr. Winkel")

    elif chk_elec_mode.get():
        modes.append((elec_deg_workflow, (d12, d21, d22, d31), "Elektr. Winkel", True, True))
        print("[CHECKBOX] Elektr. Winkel")
    
    elif chk_linear_mode.get():
        modes.append((linear_workflow, (d11, d12, d21, d22, d31, d32), "Linearitätsprüfung", True, True))
        print("[CHECKBOX] Linearität")
    

    if len(modes) == 1 and ends_checked is False:
        open_nocheck_window()
        print("Keine Messungen gewählt.")
        return
    
    #send_modes(chk_ends_mode.get(), chk_elec_mode.get(), chk_noise_mode.get(), chk_linear_mode.get())
    start_measurements(modes, meas_volt, meas_angle, meas_speed)

def export_pdf():
    save_to_pdf(txt9, pico_plot_time, pico_pdf_time, pico_plot_volt, pico_volt)

def export_excel():
    save_to_excel(
        txt9,
        linear_workflow.result["daten"],
        linear_workflow.result["linear_sollV"],
        linear_workflow.result["linear_lin"],
        linear_workflow.result["summary_vals"],
        linear_workflow.result["lin_max"],
        linear_workflow.result["lin_min"],
        linear_workflow.result["error_lin_idx"],
    )

def advanced_chk():
    if advanced_mode.get():
        text_rw_state = 'normal'
        advanced_visible(True)
    else:
        text_rw_state = 'readonly'
        advanced_visible(False)

    for fields in (txt_volt, txt_angle, txt_speed, txt_d11, txt_d12, txt_d21, txt_d22, txt_d31, txt_d32):
        fields.configure(state=text_rw_state)
        
def autosave_chk():
    if autosave_var.get():
        if measurements_finished and chk_linear_mode.get() is True and not pico_runner.out_volt:
            export_excel()
        if measurements_finished and chk_noise_mode.get() is True:
            export_pdf()

def update_deadzone_ring(*_):
    global deadzone_after_id
    if deadzone_after_id is not None:
        root.after_cancel(deadzone_after_id)
    deadzone_after_id = root.after(50, instant_deadzone_ring)

def instant_deadzone_ring():
    global deadzone_after_id
    deadzone_after_id = None

    d11 = decimal_conversion(d11_var.get())
    d12 = decimal_conversion(d12_var.get())
    d21 = decimal_conversion(d21_var.get())
    d22 = decimal_conversion(d22_var.get())
    d31 = decimal_conversion(d31_var.get())
    d32 = decimal_conversion(d32_var.get())

    deadzone_angles = []
    for angles in (d11, d12, d21, d22, d31, d32):
        if angles is not None:
            deadzone_angles.append(angles)
    
    ring.mark_deadzone(deadzone_angles)

def show_current_position():
    side_functions.show_pos()
    cur_pos_var.set(f"Position Tick: {side_functions.cur_pos}")


def goto_execute():
    goto_speed = float(txt_speed.get().strip().replace(',', '.'))
    goto_pos = float(txt_go.get().strip())
    def worker():
        side_functions.goto(goto_pos, goto_speed)
    threading.Thread(target=worker, daemon=True).start()

def advanced_visible(visible: bool):
    widgets = (but_go, advanced_warning, txt_go, but_cur_pos, lbl_cur_pos)
    if visible:
        open_advanced_window()
        for w in widgets:
            w.grid()
    else:
        for w in widgets:
            w.grid_remove()


# --------------- SAFETY WARNING WIPER TOO CLOSE
def open_safety_win():
    global safety_cancel_win
    safety_cancel_win = tk.Toplevel(root)
    safety_cancel_win.title("Fehler")
    safety_cancel_win.geometry(f"{small_wid}x{170}+{scr_wid//2}+{scr_hei//2}")
    safety_cancel_win.grid_rowconfigure(0, weight=1)
    safety_cancel_win.grid_rowconfigure(1, weight=1)
    safety_cancel_win.grid_columnconfigure(0, weight=1)
    safety_cancel_win.resizable(False, False)
    safety_cancel_win.transient(root)
    safety_cancel_win.grab_set()

    ttk.Label(safety_cancel_win, text="Schleifer zu nah am Anschlag.\nBitte Richtung Mitte positionieren.").grid(row=0, column=0, pady=(20,0))
    ok_button = ttk.Button(safety_cancel_win, text="OK", command=safety_cancel_win.destroy)
    ok_button.grid(row=1, column=0, pady=(0, 0), ipadx=20)
    ok_button.focus_set()  
    safety_cancel_win.bind("<Return>", lambda event: ok_button.invoke())

# --------------- NOISE DETECTED WARNING
def open_noise_found_win():
    global noise_found_win
    noise_found_win = tk.Toplevel(root)
    noise_found_win.title("Fehler")
    noise_found_win.geometry(f"{small_wid}x{170}+{scr_wid//2}+{scr_hei//2}")
    noise_found_win.grid_rowconfigure(0, weight=1)
    noise_found_win.grid_rowconfigure(1, weight=1)
    noise_found_win.grid_columnconfigure(0, weight=1)
    noise_found_win.resizable(False, False)
    noise_found_win.transient(root)
    noise_found_win.grab_set()

    ttk.Label(noise_found_win, text="Rauschen gefunden.\nRestliche Messungen werden abgebrochen.").grid(row=0, column=0, pady=(20,0))
    ok_button = ttk.Button(noise_found_win, text="OK", command=noise_found_win.destroy)
    ok_button.grid(row=1, column=0, pady=(0, 0), ipadx=20)
    ok_button.focus_set()  
    noise_found_win.bind("<Return>", lambda event: ok_button.invoke())


# --------------- NO CHECKBOXES WARNING
def open_nocheck_window():
    global nocheck_win
    nocheck_win = tk.Toplevel(root)
    nocheck_win.title("Fehler")
    nocheck_win.geometry(f"{small_wid}x{small_hei}+{scr_wid//2}+{scr_hei//2}")
    nocheck_win.grid_rowconfigure(0, weight=1)
    nocheck_win.grid_rowconfigure(1, weight=1)
    nocheck_win.grid_columnconfigure(0, weight=1)
    nocheck_win.resizable(False, False)
    nocheck_win.transient(root)
    nocheck_win.grab_set()

    ttk.Label(nocheck_win, text="Bitte eine Messung ankreuzen.").grid(row=0, column=0, pady=(20,0))
    ok_button = ttk.Button(nocheck_win, text="OK", command=nocheck_win.destroy)
    ok_button.grid(row=1, column=0, pady=(0, 0), ipadx=20)
    ok_button.focus_set()  
    nocheck_win.bind("<Return>", lambda event: ok_button.invoke())


# --------------- ADVANCED MODE WARNING
def open_advanced_window():
    global advanced_win
    advanced_win = tk.Toplevel(root)
    advanced_win.title("Fehler")
    advanced_win.geometry(f"{420}x{180}+{scr_wid//2}+{scr_hei//2}")
    advanced_win.grid_rowconfigure(0, weight=1)
    advanced_win.grid_rowconfigure(1, weight=1)
    advanced_win.grid_columnconfigure(0, weight=1)
    advanced_win.resizable(False, False)
    advanced_win.transient(root)
    advanced_win.grab_set()

    adv_win_warning = ttk.Label(advanced_win, text="Erweiteter Modus wurde aktiviert:\n- Parameter sind veränderbar.\n" \
    "- Positionsanfahrt freigeschaltet. (Ticks)\n- Positionsanzeige freigeschaltet. (Ticks)")
    adv_win_warning.grid(row=0, column=0)
    adv_win_warning.config(justify='center')
    ok_button = ttk.Button(advanced_win, text="OK", command=advanced_win.destroy)
    ok_button.grid(row=1, column=0, ipadx=20)
    ok_button.focus_set()  
    advanced_win.bind("<Return>", lambda event: ok_button.invoke())


# --------------- OPEN ZERO WINDOW
def open_zero_window():
    meas_speed = float(txt_speed.get().strip().replace(',', '.'))
    def on_up_wait_results():
        wait_win.destroy()

        if stop_event.is_set():
            root.after(0, open_cancelled_window)
        else:
            global zero_win
            if zero_win is not None and zero_win.winfo_exists():
                zero_win.destroy()

            zero_win = tk.Toplevel(root)
            zero_win.title("Fertig")
            zero_win.geometry(f"{small_wid}x{170}+{scr_wid//2}+{scr_hei//2}")
            zero_win.grid_rowconfigure(0, weight=1)
            zero_win.grid_rowconfigure(1, weight=1)
            zero_win.grid_columnconfigure(0, weight=1)
            zero_win.resizable(False, False)
            
            ttk.Label(zero_win, text="Position ist auf 0.").grid(row=0, column=0, pady=(20,0))
            ok_button = ttk.Button(zero_win, text="OK", command=zero_win.destroy)
            ok_button.grid(row=1, column=0, pady=(0, 0), ipadx=20)
            ok_button.focus_set()
            zero_win.bind("<Return>", lambda event: ok_button.invoke())
        
    wait_win = tk.Toplevel(root)
    wait_win.title("Position nullen")
    wait_win.geometry(f"{small_wid}x{small_hei}+{scr_wid//2}+{scr_hei//2}")
    wait_win.transient(root)
    wait_win.grab_set()
    wait_win.resizable(False, False)
    ttk.Label(wait_win, text="Bitte warten...").pack(expand=True, pady=(0, 30))

    stop_event = threading.Event()    
    def cancel_on_up():
        stop_event.set()
        wait_win.destroy()
    wait_win.protocol("WM_DELETE_WINDOW", cancel_on_up)
    threading.Thread(target=side_functions.go_zero, args=(meas_speed, stop_event, on_up_wait_results), daemon=True).start()
    

def open_cancelled_window():
    global cancelled_win 
    cancelled_win = tk.Toplevel(root)
    cancelled_win.title("Abbruch")
    cancelled_win.geometry(f"{small_wid}x{small_hei}+{scr_wid//2}+{scr_hei//2}")
    cancelled_win.grid_rowconfigure(0, weight=1)
    cancelled_win.grid_rowconfigure(1, weight=1)
    cancelled_win.grid_columnconfigure(0, weight=1)
    cancelled_win.resizable(False, False)

    ttk.Label(cancelled_win, text="Vorgang wurde abgebrochen.").grid(row=0, column=0, pady=(20,0))
    ok_button = ttk.Button(cancelled_win, text="OK", command=cancelled_win.destroy)
    ok_button.grid(row=1, column=0, ipadx=20)
    ok_button.focus_set()  
    cancelled_win.bind("<Return>", lambda event: ok_button.invoke())


# --------------- GUI
root = tk.Tk()
scr_wid = root.winfo_screenwidth()
scr_hei = root.winfo_screenheight()
small_wid = 300
small_hei = 170

root.minsize(width=1280, height=800)
root.geometry("1280x800")
#root.geometry(f"{scr_wid - scr_wid//5}x{scr_hei - scr_hei//5}+0+0")
root.title("Rauschprüfung")
root.resizable(True, True)
root.configure(bg="#1c1c1c")

root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(1, weight=1)

left_frame  = ttk.Frame(root)
right_frame = ttk.Frame(root)
left_frame.grid(row=1, column=0, sticky="nw", padx=12, pady=12)
right_frame.grid(row=1, column=1, sticky="nw",  padx=12, pady=12)
ring_area = ttk.Frame(root)
ring_area.grid(row=1, column=2, sticky="nw", padx=(0,30), pady=12)

img = ImageTk.PhotoImage(smallLogo)
panel = tk.Label(root, image=img)
panel.image = img    
panel.grid(row=0, column=0, columnspan=2,padx=24, pady=24, sticky="nw")

right_frame.grid_columnconfigure(1, weight=0)
# right_frame.grid_rowconfigure(0, weight=0)

#ser_arduino = serial_manager(root, on_button=measurement_chk)
#ser_arduino.connect()

vcmd = (root.register(lambda P: (P.count(',') <= 1 and all(ch.isdigit() or ch == ',' for ch in P))), "%P")

ttk.Label(left_frame, text="Auftragsnummer:").grid(row=4, column=0, sticky="w", pady=(20, 0), padx=(20,0))
txt9 = ttk.Entry(left_frame, width=20)
txt9.grid(row=5, column=0, pady=(0, 10), padx=(20,0))

autosave_var = tk.BooleanVar(value=True)
chk_autosave = ttk.Checkbutton(left_frame, text="Automatisches Speichern", variable=autosave_var, command=autosave_chk)
chk_autosave.grid(row=6, column=0, sticky="w", pady=(20, 0), padx=(20, 0))

advanced_mode = tk.BooleanVar(value=False)
chk_advanced_mode = ttk.Checkbutton(left_frame, text="Erweiteter Modus", variable=advanced_mode, command=advanced_chk)
chk_advanced_mode.grid(row=7, column=0, sticky="w", pady=(20, 0), padx=(20, 0))

msg = tk.Message(left_frame, width=200, bg="#CCCCCC", fg="#C00000", font='Arial 10 bold')


ttk.Label(right_frame, text="Sollspannung in V").grid(row=1, column=0, sticky="w", pady=(40, 0), padx=(10,0))
txt_volt = ttk.Entry(right_frame, width=12, validate="key", validatecommand=vcmd)
txt_volt.grid(row=2, column=0, pady=(0, 0), padx=(20,0))
txt_volt.insert(0, "10,0")
txt_volt.configure(state=text_rw_state)

ttk.Label(right_frame, text="Gesamtwinkel in °").grid(row=3, column=0, sticky="w", pady=(40, 0), padx=(10,0))
txt_angle = ttk.Entry(right_frame, width=12, validate="key", validatecommand=vcmd)
txt_angle.grid(row=4, column=0, pady=(0, 0), padx=(20,0))
txt_angle.insert(0, "330,0")
txt_angle.configure(state=text_rw_state)

ttk.Label(right_frame, text="Max. Geschw. in U/min:").grid(row=5, column=0, sticky="w", pady=(40, 0), padx=(10,0))
txt_speed = ttk.Entry(right_frame, width=12, validate="key", validatecommand=vcmd)
txt_speed.grid(row=6, column=0, pady=(0, 0), padx=(20,0))
txt_speed.insert(0, "60,0")
txt_speed.configure(state=text_rw_state)

d11_var = tk.StringVar(value="0,0")
ttk.Label(right_frame, text="Totzone 1 Links in °").grid(row=1, column=1, sticky="w", pady=(40, 0), padx=(10,0))
txt_d11 = ttk.Entry(right_frame, width=12, validate="key", validatecommand=vcmd, textvariable=d11_var)
txt_d11.grid(row=2, column=1, pady=(0, 0), padx=(20,0))
txt_d11.insert(0, "0,0")
txt_d11.configure(state=text_rw_state)

d12_var = tk.StringVar(value="40,0")
ttk.Label(right_frame, text="Totzone 1 Rechts in °").grid(row=1, column=2, sticky="w", pady=(40, 0), padx=(18,0))
txt_d12 = ttk.Entry(right_frame, width=12, validate="key", validatecommand=vcmd, textvariable=d12_var)
txt_d12.grid(row=2, column=2, pady=(0, 0), padx=(30,0))
txt_d12.insert(0, "40,0")
txt_d12.configure(state=text_rw_state)

d21_var = tk.StringVar(value="140,0")
ttk.Label(right_frame, text="Totzone 2 Links in °").grid(row=3, column=1, sticky="w", pady=(40, 0), padx=(10,0))
txt_d21 = ttk.Entry(right_frame, width=12, validate="key", validatecommand=vcmd, textvariable=d21_var)
txt_d21.grid(row=4, column=1, pady=(0, 0), padx=(20,0))
txt_d21.insert(0, "140,0")
txt_d21.configure(state=text_rw_state)

d22_var = tk.StringVar(value="190,0")
ttk.Label(right_frame, text="Totzone 2 Rechts in °").grid(row=3, column=2, sticky="w", pady=(40, 0), padx=(18,0))
txt_d22 = ttk.Entry(right_frame, width=12, validate="key", validatecommand=vcmd, textvariable=d22_var)
txt_d22.grid(row=4, column=2, pady=(0, 0), padx=(30,0))
txt_d22.insert(0, "190,0")
txt_d22.configure(state=text_rw_state)

d31_var = tk.StringVar(value="290,0")
ttk.Label(right_frame, text="Totzone 3 Links in °").grid(row=5, column=1, sticky="w", pady=(40, 0), padx=(10,0))
txt_d31 = ttk.Entry(right_frame, width=12, validate="key", validatecommand=vcmd, textvariable=d31_var)
txt_d31.grid(row=6, column=1, pady=(0, 0), padx=(20,0))
txt_d31.insert(0, "290,0")
txt_d31.configure(state=text_rw_state)

d32_var = tk.StringVar(value="330,0")
ttk.Label(right_frame, text="Totzone 3 Rechts in °").grid(row=5, column=2, sticky="w", pady=(40, 0), padx=(18,0))
txt_d32 = ttk.Entry(right_frame, width=12, validate="key", validatecommand=vcmd, textvariable=d32_var)
txt_d32.grid(row=6, column=2, pady=(0, 0), padx=(30,0))
txt_d32.insert(0, "330,0")
txt_d32.configure(state=text_rw_state)

for var in (d11_var, d12_var, d21_var, d22_var, d31_var, d32_var):
    var.trace_add("write", update_deadzone_ring)

ttk.Label(left_frame, text="Teilenummer:").grid(row=0, column=0, sticky="w", pady=(10, 0), padx=(20,0))
search_var = tk.StringVar()
preset_entry = ttk.Entry(left_frame, textvariable=search_var, width=16)
preset_entry.grid(row=1, column=0, sticky="w", padx=(20,0))
preset_entry.focus_set()
preset_ids = list(presets.keys())

search_var.trace_add("write", lambda *_: _update_dropdown(preset_entry, search_var, preset_ids))

def on_enter(event=None):
    if dropdown["win"] is not None:
        select_from_list(preset_entry)
        return "break"
    # wenn Dropdown zu ist, aber exakter match:
    pid = preset_entry.get().strip()
    if pid in presets:
        insert_preset(presets[pid])
    return "break"

def on_down(event=None):
    lb = dropdown["listbox"]
    if lb is None:
        return
    i = lb.curselection()[0] if lb.curselection() else 0
    j = min(i + 1, lb.size() - 1)
    lb.selection_clear(0, tk.END)
    lb.selection_set(j)
    lb.activate(j)
    return "break"

def on_up(event=None):
    lb = dropdown["listbox"]
    if lb is None:
        return
    i = lb.curselection()[0] if lb.curselection() else 0
    j = max(i - 1, 0)
    lb.selection_clear(0, tk.END)
    lb.selection_set(j)
    lb.activate(j)
    return "break"

preset_entry.bind("<Return>", on_enter)
preset_entry.bind("<Down>", on_down)
preset_entry.bind("<Up>", on_up)
preset_entry.bind("<Escape>", lambda e: (on_up_dropdown(), "break"))

def bind_listbox_click():
    if dropdown["listbox"] is not None:
        dropdown["listbox"].bind("<ButtonRelease-1>", lambda e: select_from_list(preset_entry))
    root.after(200, bind_listbox_click)

bind_listbox_click()

chk_ends_mode = tk.BooleanVar(value=False)
chk_elec_mode = tk.BooleanVar(value=False)
chk_noise_mode = tk.BooleanVar(value=False)
chk_linear_mode = tk.BooleanVar(value=False)
chk_meas_ends = ttk.Checkbutton(right_frame, text="Mech. Enden", variable=chk_ends_mode)
chk_meas_ends.grid(row=7, column=0, sticky="w", pady=(60, 0), padx=(20, 0))
chk_elec_deg = ttk.Checkbutton(right_frame, text="Elektr. Winkel", variable=chk_elec_mode)
chk_elec_deg.grid(row=7, column=2, sticky="w", pady=(60, 0), padx=(20, 0))
chk_noise = ttk.Checkbutton(right_frame, text="Rauschen", variable=chk_noise_mode)
chk_noise.grid(row=7, column=1, sticky="w", pady=(60, 0), padx=(20, 0))
chk_linearity = ttk.Checkbutton(right_frame, text="Linearität", variable=chk_linear_mode)
chk_linearity.grid(row=7, column=3, sticky="w", pady=(60, 0), padx=(20, 0))

mech_angle_var = tk.StringVar(value="Mechanischer Winkel: --")
lbl_mech = ttk.Label(right_frame, textvariable=mech_angle_var, font="Verdana 12 bold")
lbl_mech.grid(row=9, column=0, columnspan=4, sticky="w", padx=(20, 0), pady=(12, 0))

elec_angle_var = tk.StringVar(value="Elektrischer Winkel: --")
lbl_elec = ttk.Label(right_frame, textvariable=elec_angle_var, font="Verdana 12 bold")
lbl_elec.grid(row=10, column=0, columnspan=4, sticky="w", padx=(20, 0), pady=(12, 0))

cur_pos_var = tk.StringVar(value="Position Tick: --")
lbl_cur_pos = ttk.Label(right_frame, textvariable=cur_pos_var, font="Verdana 12 bold")
lbl_cur_pos.grid(row=8, column=0, columnspan=4, sticky="w", padx=(20, 0), pady=(12, 0))

# lbl_go = ttk.Label(right_frame, text="Anfahrt:")
# lbl_go.grid(row=8, column=2, pady=(20,0))
txt_go = ttk.Entry(right_frame, width=5, validate="key", validatecommand=vcmd)
txt_go.grid(row=9, column=2)

advanced_warning = tk.Message( width=350, bg="#FF0000", fg="#E3E3E3", font='Arial 16 bold')
advanced_warning.grid(row=0, column=1, pady=(10, 10), padx=(200,0))
advanced_warning.config(text="ACHTUNG:\nERWEITERTER MODUS AKTIVIERT")

ttk.Button(left_frame, text="Linearität speichern", command=export_excel,width=18).grid(row=9, column=0, pady=(20, 5), padx=(20,0), ipadx=10)
ttk.Button(left_frame, text="Rauschkurve speichern", command=export_pdf, width=18).grid(row=10, column=0, pady=(5, 5), padx=(20,0), ipadx=10)
ttk.Button(left_frame, text="Position 0", command=open_zero_window, width=18).grid(row=11, column=0, pady=(20, 5), padx=(20,0), ipadx=10)
#ttk.Button(right_frame, text="Mech. Enden", command=start_mech_ends_measurement,width=12).grid(row=8, column=0, pady=(180, 5), padx=(20,0))
#ttk.Button(right_frame, text="Elektr. Winkel", command=start_elec_deg_measurement,width=12).grid(row=8, column=1, pady=(180, 5), padx=(20,0))
#ttk.Button(right_frame, text="Rauschen", command=start_noise_measurement,width=12).grid(row=8, column=2, pady=(180, 5), padx=(20,0))
#ttk.Button(right_frame, text="Netzteil Test", command=tests,width=12).grid(row=9, column=3, pady=(20, 5), padx=(20,0))
ttk.Button(right_frame, text="Messen", command=measurement_chk, width=12).grid(row=8, column=3, pady=(20, 5), padx=(10,0))
but_cur_pos = ttk.Button(right_frame, text="Curr Position", command=show_current_position)
but_cur_pos.grid(row=8, column=2, pady=(12, 5), padx=(10,0))
but_go = ttk.Button(right_frame, text="Go To", command=goto_execute)
but_go.grid(row=10, column=2, pady=(5, 5))

root.bind("<Escape>", lambda event: on_up_window())

# --------------- MAIN
ring.build_ring(ring_area)
advanced_visible(False)
instant_deadzone_ring()
sv_ttk.set_theme("dark")
root.mainloop()