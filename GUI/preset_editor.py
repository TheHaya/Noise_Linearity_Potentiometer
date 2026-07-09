import tkinter as tk
from tkinter import Canvas, Scrollbar, LEFT, RIGHT, BOTH, Y, VERTICAL, Frame, Label
from tkinter import ttk
from tkinter import messagebox
import json, os, shutil, datetime, tempfile, sys
import sv_ttk
from PIL import ImageTk, Image
from tkinter import filedialog


# def resource_path(rel_path: str) -> str:
#     base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
#     return os.path.join(base, rel_path)

# ------------------ BACKEND FUNCTIONS

# def get_preset_file_path() -> str:
#     if getattr(sys, "frozen", False):
#         base_dir = os.path.dirname(sys.executable)
#     else:
#         base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#     return os.path.join(base_dir, "preset_Teile.json")

# if __name__ == "__main__": pass


def resource_path(rel_path: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel_path)
# PRESET_PATH = get_preset_file_path()

# --------------- PRESETS LADEN
tol_total_mech_deg_pos = None
tol_total_mech_deg_neg = None
tol_total_elec_deg_pos = None
tol_total_elec_deg_neg = None
tol_position_deadzone_cw_pos = None
tol_position_deadzone_cw_neg = None
tol_position_deadzone_ccw_pos = None
tol_position_deadzone_ccw_neg = None
tol_total_deadzone_pos = None
tol_total_deadzone_neg = None
tol_active_cw_pos = None
tol_active_cw_neg = None
tol_active_ccw_pos = None
tol_active_ccw_neg = None
tol_linearity_pos = None
tol_linearity_neg = None
tol_resistance_pos = None
tol_resistance_neg = None
relay_switch_pol = None

preset_path = resource_path("preset_Teile.json")

FIELD_SCHEMA = [
    {   #1
        "key": "soll_spannung_rauschen",
        "label": "Soll-Spannung Rauschen [V]",
        "group": "Sollwerte",
        "type": float,
        "min": 0.0,
        "max": 20.0,
        "required": True,
    },
    {   #2
        "key": "soll_spannung_linear",
        "label": "Soll-Spannung Linearität [V]",
        "group": "Sollwerte",
        "type": float,
        "min": 0.0,
        "max": 20.0,
        "required": True,
    },
    {   #3
        "key": "soll_spannung_widerstand",
        "label": "Soll-Spannung Widerstand [V]",
        "group": "Sollwerte",
        "type": float,
        "min": 0.0,
        "max": 20.0,
        "required": True,
    },
    {   #4
        "key": "soll_winkel",
        "label": "Mechanischer Soll-Winkel [deg]",
        "group": "Sollwerte",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #5
        "key": "soll_geschwindigkeit",
        "label": "Maximale Drehgeschwindigkeit [rpm]",
        "group": "Sollwerte",
        "type": float,
        "min": 0,
        "max": 120,
        "required": True,
    },
    {   #6
        "key": "d11",
        "label": "Deadzone 1-1 [deg]",
        "group": "Totzonen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #7
        "key": "d12",
        "label": "Deadzone 1-2 [deg]",
        "group": "Totzonen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #8
        "key": "d21",
        "label": "Deadzone 2-1 [deg]",
        "group": "Totzonen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #9
        "key": "d22",
        "label": "Deadzone 2-2 [deg]",
        "group": "Totzonen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #10
        "key": "d31",
        "label": "Deadzone 3-1 [deg]",
        "group": "Totzonen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #11
        "key": "d32",
        "label": "Deadzone 3-2 [deg]",
        "group": "Totzonen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #12
        "key": "tol_drehwinkel_mech_pos",
        "label": "Tol. Drehwinkel mech. + [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #13
        "key": "tol_drehwinkel_mech_neg",
        "label": "Tol. Drehwinkel mech. - [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #14
        "key": "tol_drehwinkel_elec_pos",
        "label": "Tol. Drehwinkel elek. + [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #15
        "key": "tol_drehwinkel_elec_neg",
        "label": "Tol. Drehwinkel elek. - [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #16
        "key": "tol_position_mittelanzapfung_cw_pos",
        "label": "Tol. Mittelanzapfung + [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #17
        "key": "tol_position_mittelanzapfung_cw_neg",
        "label": "Tol. Mittelanzapfung - [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },  
    {   #18
        "key": "tol_position_mittelanzapfung_ccw_pos",
        "label": "Tol. Mittelanzapfung + [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #19
        "key": "tol_position_mittelanzapfung_ccw_neg",
        "label": "Tol. Mittelanzapfung - [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #20
        "key": "tol_gesamt_mittelanzapfung_pos",
        "label": "Tol. Mittelanzapfung + [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #21
        "key": "tol_gesamt_mittelanzapfung_neg",
        "label": "Tol. Mittelanzapfung - [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #22
        "key": "tol_active_cw_pos",
        "label": "Tol. AktivCW + [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #23
        "key": "tol_active_cw_neg",
        "label": "Tol. AktivCW - [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #24
        "key": "tol_active_ccw_pos",
        "label": "Tol. AktivCCW + [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #25
        "key": "tol_active_ccw_neg",
        "label": "Tol. AktivCCW - [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #26
        "key": "tol_linear_pos",
        "label": "Tol. Linearität + [%]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #27
        "key": "tol_linear_neg",
        "label": "Tol. Linearität - [%]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #28
        "key": "tol_widerstand_pos",
        "label": "Tol. Widerstand + [%]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #29
        "key": "tol_widerstand_neg",
        "label": "Tol. Widerstand - [%]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #30
        "key": "relay_polarity_switch",
        "label": "Relais Polaritätswechsler",
        "group": "Relais",
        "type": int,
        "min": 0,
        "max": 1,
        "required": True,
    },
    {   #31
        "key": "comment",
        "label": "Kommentar",
        "group": "Kommentar",
        "type": str,
        "required": False,
    },
]


AMLogo = Image.open(resource_path("AMLogo.jpg"))
scale = 0.8
w, h = AMLogo.size
smallLogo = AMLogo.resize((int(w*scale), int(h*scale)))
entries = {}

def set_entry(txt_entry, decimal_val):
    if decimal_val is None:
        val = ""
    elif isinstance(decimal_val, (int, float)):
        val = f"{decimal_val}".replace(".", ",")
    else:
        val = str(decimal_val)

    txt_entry.delete(0, tk.END)
    txt_entry.insert(0, val)

def insert_preset(p):
    for field in FIELD_SCHEMA:
        key = field["key"]

        if key not in entries:
            continue

        value = p.get(key, "")
        set_entry(entries[key], value)

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

def get_schema_keys():
    return [field["key"] for field in FIELD_SCHEMA]

def build_default_preset():
    preset = {}

    for field in FIELD_SCHEMA:
        field_type = field["type"]
        if field_type is float:
            preset[field["key"]] = 0.0
        elif field_type is int:
            preset[field["key"]] = 0
        else:
            preset[field["key"]] = ""
    return preset

def germanfy_preset(data: dict) -> dict:
    germanfied = {}

    for label, value in data.items():
        preset = build_default_preset()

        for field in FIELD_SCHEMA:
            key = field["key"]
            raw_value = value.get(key, preset[key])

            if field["type"] is float:
                if isinstance(raw_value, str):
                    raw_value = raw_value.replace(",", ".")
                try:
                    preset[key] = float(raw_value)
                except (TypeError, ValueError):
                    preset[key] = 0.0

            elif field["type"] is int:
                try:
                    preset[key] = int(raw_value)
                except (TypeError, ValueError):
                    preset[key] = 0

            elif field["type"] is str:
                try:
                    preset[key] = str(raw_value)
                except (TypeError):
                    preset[key] = ""
            else:
                preset[key] = ""
    
        germanfied[str(label)] = preset

    return germanfied


def load_presets(path: str) -> dict:
    if not os.path.exists(path):
        messagebox.showwarning(
            "Datei fehlt",
            f"Die Datei wurde nicht gefunden:\n{path}\n\nEs wird mit leerem Bestand gestartet."
        )
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Root-Element ist kein Objekt.")

        return germanfy_preset(data)

    except Exception as exc:
        messagebox.showerror(
            "Fehler beim Laden",
            f"preset_Teile.json konnte nicht geladen werden.\n\nDetails:\n{exc}"
        )
        return {}
presets = load_presets(preset_path)

def save_presets(path: str, data: dict) -> bool:
    directory = os.path.dirname(path)
    filename = os.path.basename(path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(directory, f"preset_Teile_backup_{timestamp}.json")

    try:
        if os.path.exists(path):
            shutil.copy2(path, backup_path)

        fd, temp_path = tempfile.mkstemp(
            prefix="preset_teile_",
            suffix=".json",
            dir=directory
        )
        os.close(fd)

        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        os.replace(temp_path, path)
        return True

    except Exception as exc:
        if "temp_path" in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

        messagebox.showerror(
            "Fehler beim Speichern",
            f"Die JSON-Datei konnte nicht gespeichert werden.\n\nDetails:\n{exc}"
        )
        return False
    
def serialize_presets(presets: dict) -> dict:
    result = {}

    for teilnummer in sorted(presets.keys()):
        ordered_preset = {}
        for field in FIELD_SCHEMA:
            key = field["key"]
            ordered_preset[key] = presets[teilnummer].get(key, build_default_preset()[key])

        result[teilnummer] = ordered_preset

    return result


def browse_files():
    filename = filedialog.askopenfilename(initialdir="/",
                                          title = "Datei auswählen",
                                          filetypes= (".json-Datei",
                                                      "*.json"))
    lbl_open_file.configure(text="Datei geöffnet: " + filename)
# ------------------ FRONTEND FUNCTIONS

print("Programm wird gestartet...")

# def main():
global root
root = tk.Tk()
scr_wid = root.winfo_screenwidth()
scr_hei = root.winfo_screenheight()
small_wid = 300
small_hei = 170

root.minsize(width=680, height=800)
root.geometry("800x800")
#root.geometry(f"{scr_wid - scr_wid//5}x{scr_hei - scr_hei//5}+0+0")
root.title("Altmann .json Editor")
root.resizable(True, True)
root.configure(bg="#1c1c1c")

# root.grid_columnconfigure(0, weight=0)
# root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=0)
# root.grid_rowconfigure(1, weight=1)
sv_ttk.set_theme("dark")
root.grid_rowconfigure(1, weight = 1)
root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=0)
root.grid_columnconfigure(3, weight=0)
left_frame  = ttk.Frame(root)
right_frame = ttk.Frame(root)
left_frame.grid(row=1, column=0, sticky="nw", padx=12, pady=12)
ring_area = ttk.Frame(root)

canvas = Canvas(root, highlightthickness=0, borderwidth=0)
canvas.grid(row=1, column=1, sticky="nsew", padx=12, pady=12)

scrollbar = ttk.Scrollbar(root,orient="vertical", command=canvas.yview)
scrollbar.grid(row=1, column=2, sticky="ns")

canvas.configure(yscrollcommand=scrollbar.set)
scrollable_frame = ttk.Frame(canvas)

canvas_window = canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
# scrollable_frame.bind("<Configure>", lambda e:
#                       canvas.configure(scrollregion=canvas.bbox("all")))

def update_scrollregion(event=None):
    canvas.configure(scrollregion=canvas.bbox("all"))


def fit_scrollable_frame(event):
    canvas.itemconfigure(canvas_window, width=event.width)

def on_mousewheel(event):
    delta = int(event.delta / 120)

    if delta == 0:
        return "break"

    canvas.yview_scroll(-delta * 1, "units")
    return "break"


scrollable_frame.bind("<Configure>", update_scrollregion)
canvas.bind("<Configure>", fit_scrollable_frame)
def bind_mousewheel_recursive(widget):
    widget.bind("<MouseWheel>", on_mousewheel, add="+")
    for child in widget.winfo_children():
        bind_mousewheel_recursive(child)


canvas.bind("<MouseWheel>", on_mousewheel, add="+")
scrollable_frame.after_idle(lambda: bind_mousewheel_recursive(scrollable_frame))

img = ImageTk.PhotoImage(smallLogo)
panel = tk.Label(root, image=img)
panel.image = img    
panel.grid(row=0, column=0, columnspan=2,padx=24, pady=24, sticky="nw")

right_frame.grid_columnconfigure(1, weight=0)



but_open_file = ttk.Button(left_frame, text="Öffnen...", command=browse_files)
but_open_file.grid(row=2, column=0, pady=(5, 100), padx=(20,0), ipadx=10)
lbl_open_file = ttk.Label(left_frame, text="Bitte Datei öffnen.")
lbl_open_file.grid(row=1, column=0, pady=(5, 5), padx=(20,0), ipadx=10)

lbl_partnr = ttk.Label(left_frame, text="Teilnummer")
lbl_partnr.grid(row=5, column=0, pady=(5, 5), padx=(20,0), ipadx=10)
search_var = tk.StringVar()
global preset_entry
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

but_save = ttk.Button(left_frame, text="Preset speichern", command=save_presets)
but_save.grid(row=8, column=0, pady=(5, 5), padx=(20,0), ipadx=10)

but_saveas = ttk.Button(left_frame, text="Datei speichern unter...")
but_saveas.grid(row=9, column=0, pady=(5, 5), padx=(20,0), ipadx=10, sticky="s")


lbl_soll_V_noise = ttk.Label(scrollable_frame, text="Sollspannung Rauschen")
lbl_soll_V_noise.grid(row=1, column=0, pady=(5, 5), padx=(20,0))
txt_soll_V_noise = ttk.Entry(scrollable_frame)
txt_soll_V_noise.grid(row=1, column=1, pady=(5, 5), padx=(20,0))

lbl_soll_V_linear = ttk.Label(scrollable_frame, text="Sollspannung Linearität")
lbl_soll_V_linear.grid(row=2, column=0, pady=(5, 5), padx=(20,0))
txt_soll_V_linear = ttk.Entry(scrollable_frame)
txt_soll_V_linear.grid(row=2, column=1, pady=(5, 5), padx=(20,0))

lbl_soll_V_resist = ttk.Label(scrollable_frame, text="Sollspannung Widerstand")
lbl_soll_V_resist.grid(row=3, column=0, pady=(5, 5), padx=(20,0))
txt_soll_V_resist = ttk.Entry(scrollable_frame)
txt_soll_V_resist.grid(row=3, column=1, pady=(5, 5), padx=(20,0))

lbl_soll_mech_angle = ttk.Label(scrollable_frame, text="Mech. Sollwinkel")
lbl_soll_mech_angle.grid(row=4, column=0, pady=(5, 5), padx=(20,0))
txt_soll_mech_angle = ttk.Entry(scrollable_frame)
txt_soll_mech_angle.grid(row=4, column=1, pady=(5, 5), padx=(20,0))

lbl_soll_speed = ttk.Label(scrollable_frame, text="Max. Drehgeschwindigkeit")
lbl_soll_speed.grid(row=5, column=0, pady=(5, 5), padx=(20,0))
txt_soll_speed = ttk.Entry(scrollable_frame)
txt_soll_speed.grid(row=5, column=1, pady=(5, 5), padx=(20,0))

lbl_d11 = ttk.Label(scrollable_frame, text="Position Kurzschluss 1 Anfang")
lbl_d11.grid(row=7, column=0, pady=(5, 5), padx=(20,0))
txt_d11 = ttk.Entry(scrollable_frame)
txt_d11.grid(row=7, column=1, pady=(5, 5), padx=(20,0))

lbl_d12 = ttk.Label(scrollable_frame, text="Position Kurzschluss 1 Ende")
lbl_d12.grid(row=8, column=0, pady=(5, 5), padx=(20,0))
txt_d12 = ttk.Entry(scrollable_frame)
txt_d12.grid(row=8, column=1, pady=(5, 5), padx=(20,0))

lbl_d21 = ttk.Label(scrollable_frame, text="Position Kurzschluss 2 Anfang")
lbl_d21.grid(row=9, column=0, pady=(5, 5), padx=(20,0))
txt_d21 = ttk.Entry(scrollable_frame)
txt_d21.grid(row=9, column=1, pady=(5, 5), padx=(20,0))

lbl_d22 = ttk.Label(scrollable_frame, text="Position Kurzschluss 2 Ende")
lbl_d22.grid(row=10, column=0, pady=(5, 5), padx=(20,0))
txt_d22 = ttk.Entry(scrollable_frame)
txt_d22.grid(row=10, column=1, pady=(5, 5), padx=(20,0))

lbl_d31 = ttk.Label(scrollable_frame, text="Position Kurzschluss 3 Anfang")
lbl_d31.grid(row=11, column=0, pady=(5, 5), padx=(20,0))
txt_d31 = ttk.Entry(scrollable_frame)
txt_d31.grid(row=11, column=1, pady=(5, 5), padx=(20,0))

lbl_d32 = ttk.Label(scrollable_frame, text="Position Kurzschluss 3 Ende")
lbl_d32.grid(row=12, column=0, pady=(5, 5), padx=(20,0))
txt_d32 = ttk.Entry(scrollable_frame)
txt_d32.grid(row=12, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_mech_pos = ttk.Label(scrollable_frame, text="Tol. Mech. Winkel Positiv")
lbl_tol_mech_pos.grid(row=14, column=0, pady=(5, 5), padx=(20,0))
txt_tol_mech_pos = ttk.Entry(scrollable_frame)
txt_tol_mech_pos.grid(row=14, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_mech_neg = ttk.Label(scrollable_frame, text="Tol. Mech. Winkel Negativ")
lbl_tol_mech_neg.grid(row=15, column=0, pady=(5, 5), padx=(20,0))
txt_tol_mech_neg = ttk.Entry(scrollable_frame)
txt_tol_mech_neg.grid(row=15, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_elec_pos = ttk.Label(scrollable_frame, text="Tol. Elek. Winkel Positiv")
lbl_tol_elec_pos.grid(row=16, column=0, pady=(5, 5), padx=(20,0))
txt_tol_elec_pos = ttk.Entry(scrollable_frame)
txt_tol_elec_pos.grid(row=16, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_elec_neg = ttk.Label(scrollable_frame, text="Tol. Elek. Winkel Positiv")
lbl_tol_elec_neg.grid(row=17, column=0, pady=(5, 5), padx=(20,0))
txt_tol_elec_neg = ttk.Entry(scrollable_frame)
txt_tol_elec_neg.grid(row=17, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_position_mid_cw_pos = ttk.Label(scrollable_frame, text="Tol. Position Mittelanzapfung CW Positiv")
lbl_tol_position_mid_cw_pos.grid(row=18, column=0, pady=(5, 5), padx=(20,0))
txt_tol_position_mid_cw_pos = ttk.Entry(scrollable_frame)
txt_tol_position_mid_cw_pos.grid(row=18, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_position_mid_cw_neg = ttk.Label(scrollable_frame, text="Tol. Position Mittelanzapfung CW Negativ")
lbl_tol_position_mid_cw_neg.grid(row=19, column=0, pady=(5, 5), padx=(20,0))
txt_tol_position_mid_cw_neg = ttk.Entry(scrollable_frame)
txt_tol_position_mid_cw_neg.grid(row=19, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_position_mid_ccw_pos = ttk.Label(scrollable_frame, text="Tol. Position Mittelanzapfung CCW Positiv")
lbl_tol_position_mid_ccw_pos.grid(row=20, column=0, pady=(5, 5), padx=(20,0))
txt_tol_position_mid_ccw_pos = ttk.Entry(scrollable_frame)
txt_tol_position_mid_ccw_pos.grid(row=20, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_position_mid_ccw_neg = ttk.Label(scrollable_frame, text="Tol. Position Mittelanzapfung CCW Negativ")
lbl_tol_position_mid_ccw_neg.grid(row=21, column=0, pady=(5, 5), padx=(20,0))
txt_tol_position_mid_ccw_neg = ttk.Entry(scrollable_frame)
txt_tol_position_mid_ccw_neg.grid(row=21, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_total_mid_cw_pos = ttk.Label(scrollable_frame, text="Tol. Gesamtwinkel Mittelanzapfung Positiv")
lbl_tol_total_mid_cw_pos.grid(row=22, column=0, pady=(5, 5), padx=(20,0))
txt_tol_total_mid_cw_pos = ttk.Entry(scrollable_frame)
txt_tol_total_mid_cw_pos.grid(row=22, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_total_mid_cw_neg = ttk.Label(scrollable_frame, text="Tol. Gesamtwinkel Mittelanzapfung Negativ")
lbl_tol_total_mid_cw_neg.grid(row=23, column=0, pady=(5, 5), padx=(20,0))
txt_tol_total_mid_cw_neg = ttk.Entry(scrollable_frame)
txt_tol_total_mid_cw_neg.grid(row=23, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_activeCW_pos = ttk.Label(scrollable_frame, text="Tol. Gesamtwinkel AktivCW Positiv")
lbl_tol_activeCW_pos.grid(row=24, column=0, pady=(5, 5), padx=(20,0))
txt_tol_activeCW_pos = ttk.Entry(scrollable_frame)
txt_tol_activeCW_pos.grid(row=24, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_activeCW_neg = ttk.Label(scrollable_frame, text="Tol. Gesamtwinkel AktivCW Negativ")
lbl_tol_activeCW_neg.grid(row=25, column=0, pady=(5, 5), padx=(20,0))
txt_tol_activeCW_neg = ttk.Entry(scrollable_frame)
txt_tol_activeCW_neg.grid(row=25, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_activeCCW_pos = ttk.Label(scrollable_frame, text="Tol. Gesamtwinkel AktivCCW Positiv")
lbl_tol_activeCCW_pos.grid(row=26, column=0, pady=(5, 5), padx=(20,0))
txt_tol_activeCCW_pos = ttk.Entry(scrollable_frame)
txt_tol_activeCCW_pos.grid(row=26, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_activeCCW_neg = ttk.Label(scrollable_frame, text="Tol. Gesamtwinkel AktivCCW Negativ")
lbl_tol_activeCCW_neg.grid(row=27, column=0, pady=(5, 5), padx=(20,0))
txt_tol_activeCCW_neg = ttk.Entry(scrollable_frame)
txt_tol_activeCCW_neg.grid(row=27, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_lin_pos = ttk.Label(scrollable_frame, text="Tol. Linearität Positiv")
lbl_tol_lin_pos.grid(row=28, column=0, pady=(5, 5), padx=(20,0))
txt_tol_lin_pos = ttk.Entry(scrollable_frame)
txt_tol_lin_pos.grid(row=28, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_lin_neg = ttk.Label(scrollable_frame, text="Tol. Linearität Negativ")
lbl_tol_lin_neg.grid(row=29, column=0, pady=(5, 5), padx=(20,0))
txt_tol_lin_neg = ttk.Entry(scrollable_frame)
txt_tol_lin_neg.grid(row=29, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_resist_pos = ttk.Label(scrollable_frame, text="Tol. Widerstand Positiv")
lbl_tol_resist_pos.grid(row=30, column=0, pady=(5, 5), padx=(20,0))
txt_tol_resist_pos = ttk.Entry(scrollable_frame)
txt_tol_resist_pos.grid(row=30, column=1, pady=(5, 5), padx=(20,0))

lbl_tol_resist_neg = ttk.Label(scrollable_frame, text="Tol. Widerstand Negativ")
lbl_tol_resist_neg.grid(row=31, column=0, pady=(5, 5), padx=(20,0))
txt_tol_resist_neg = ttk.Entry(scrollable_frame)
txt_tol_resist_neg.grid(row=31, column=1, pady=(5, 5), padx=(20,0))

lbl_switch_polarity = ttk.Label(scrollable_frame, text="Polarität wechsel?")
lbl_switch_polarity.grid(row=32, column=0, pady=(5, 5), padx=(20,0))
txt_switch_polarity = ttk.Entry(scrollable_frame)
txt_switch_polarity.grid(row=32, column=1, pady=(5, 5), padx=(20,0))

lbl_comment = ttk.Label(scrollable_frame, text="Kommentar")
lbl_comment.grid(row=33, column=0, pady=(5, 5), padx=(20,0))
# txt_comment = tk.Text(scrollable_frame, height= 7, width= 20, font="Arial 12")
# txt_comment.grid(row=33, column=1, pady=(5, 5), padx=(20,0))
txt_comment = ttk.Entry(scrollable_frame)
txt_comment.grid(row=33, column=1, pady=(5, 5), padx=(20,0))

entries["soll_spannung_rauschen"] = txt_soll_V_noise
entries["soll_spannung_linear"] = txt_soll_V_linear
entries["soll_spannung_widerstand"] = txt_soll_V_resist
entries["soll_winkel"] = txt_soll_mech_angle
entries["soll_geschwindigkeit"] = txt_soll_speed

entries["d11"] = txt_d11
entries["d12"] = txt_d12
entries["d21"] = txt_d21
entries["d22"] = txt_d22
entries["d31"] = txt_d31
entries["d32"] = txt_d32

entries["tol_drehwinkel_mech_pos"] = txt_tol_mech_pos
entries["tol_drehwinkel_mech_neg"] = txt_tol_mech_neg
entries["tol_drehwinkel_elec_pos"] = txt_tol_elec_pos
entries["tol_drehwinkel_elec_neg"] = txt_tol_elec_neg

entries["tol_position_mittelanzapfung_cw_pos"] = txt_tol_position_mid_cw_pos
entries["tol_position_mittelanzapfung_cw_neg"] = txt_tol_position_mid_cw_neg
entries["tol_position_mittelanzapfung_ccw_pos"] = txt_tol_position_mid_ccw_pos
entries["tol_position_mittelanzapfung_ccw_neg"] = txt_tol_position_mid_ccw_neg

entries["tol_gesamt_mittelanzapfung_pos"] = txt_tol_total_mid_cw_pos
entries["tol_gesamt_mittelanzapfung_neg"] = txt_tol_total_mid_cw_neg

entries["tol_active_cw_pos"] = txt_tol_activeCW_pos
entries["tol_active_cw_neg"] = txt_tol_activeCW_neg
entries["tol_active_ccw_pos"] = txt_tol_activeCCW_pos
entries["tol_active_ccw_neg"] = txt_tol_activeCCW_neg

entries["tol_linear_pos"] = txt_tol_lin_pos
entries["tol_linear_neg"] = txt_tol_lin_neg
entries["tol_widerstand_pos"] = txt_tol_resist_pos
entries["tol_widerstand_neg"] = txt_tol_resist_neg

entries["relay_polarity_switch"] = txt_switch_polarity
entries["comment"] = txt_comment

# ------------------ MAIN
root.mainloop()


# if __name__ == "__main__":
#     main()