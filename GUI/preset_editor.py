from tkinter import ttk
from tkinter import messagebox
import json, os, shutil, datetime, tempfile, sys
import sv_ttk
from PIL import ImageTk, Image

# def resource_path(rel_path: str) -> str:
#     base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
#     return os.path.join(base, rel_path)

# ------------------ BACKEND FUNCTIONS

def get_preset_file_path() -> str:
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_dir, "preset_Teile.json")

if __name__ == "__main__": pass

PRESET_PATH = get_preset_file_path()

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
        "key": "tol_mittelanzapfung_pos",
        "label": "Tol. Mittelanzapfung + [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #17
        "key": "tol_mittelanzapfung_neg",
        "label": "Tol. Mittelanzapfung - [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #18
        "key": "tol_active_cw_pos",
        "label": "Tol. AktivCW + [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #19
        "key": "tol_active_cw_neg",
        "label": "Tol. AktivCW - [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #20
        "key": "tol_active_ccw_pos",
        "label": "Tol. AktivCCW + [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #21
        "key": "tol_active_ccw_neg",
        "label": "Tol. AktivCCW - [deg]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #22
        "key": "tol_linear_pos",
        "label": "Tol. Linearität + [%]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #23
        "key": "tol_linear_neg",
        "label": "Tol. Linearität - [%]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #24
        "key": "tol_widerstand_pos",
        "label": "Tol. Widerstand + [%]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #25
        "key": "tol_widerstand_neg",
        "label": "Tol. Widerstand - [%]",
        "group": "Toleranzen",
        "type": float,
        "min": 0.0,
        "max": 9999999999.0,
        "required": True,
    },
    {   #26
        "key": "relay_polarity_switch",
        "label": "Relais Polaritätswechsler",
        "group": "Relais",
        "type": int,
        "min": 0,
        "max": 1,
        "required": True,
    },
    {   #27
        "key": "comment",
        "label": "Kommentar",
        "group": "Kommentar",
        "type": str,
        "required": False,
    },
]

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

def save_presets(path: str, data: dict) -> bool:
    directory = os.path.dirname(path)
    filename = os.path.basename(path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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



# ------------------ FRONTEND FUNCTIONS

