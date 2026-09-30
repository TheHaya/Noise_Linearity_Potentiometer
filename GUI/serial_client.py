import serial, time, sys, re
import serial.tools.list_ports
import json, os
# --------------- SERIAL VARIABLES
ser_Arduino = None
# ------ PRÜFVORRICHTUNG FIRMA
# ARDUINO_PORT = "COM3"
# MULTI_PORT = "COM4"
# PSU_PORT = "COM5"

# ------ ALWIN LAPTOP
# ARDUINO_PORT = "COM18"
# MULTI_PORT = "COM6"
# PSU_PORT = "COM7"

# --------------- COM PORTS MIT JSON
def resource_path(rel_path):
    base = getattr(
        sys,
        "_MEIPASS",
        os.path.dirname(os.path.abspath(__file__))
    )
    return os.path.join(base, rel_path)


def load_com_ports():
    path = resource_path("COM_PORTS.json")

    with open(path, "r", encoding="utf-8") as file:
        config = json.load(file)

    required = ("arduino", "multimeter", "psu")

    for name in required:
        if not config.get(name):
            raise ValueError(f"COM-Port für {name} fehlt.")

    ports = [config[name] for name in required]

    if len(ports) != len(set(ports)):
        raise ValueError("Ein COM-Port wurde mehrfach zugewiesen.")

    return config

COM_PORTS = load_com_ports()

# --------------- SERIAL MIT SERVO
def connect_ard(port, baud=115200, timeout=0.1):
    serial_ports()
    err_time = time.monotonic() + 10
    while time.monotonic() < err_time:
        try:
            ser_ard = serial.Serial(port, baudrate=baud, timeout=timeout)
            print(f"[SERIAL] Mikrocontroller verbunden: {port}")
            time.sleep(0.5)
            return ser_ard
        except Exception as e:
            print("Mikrocontroller kein Port")

def connect_multi(port, baud=19200, timeout=3):
    try:
        ser_multi = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )

        print("[DMM] Einstellungen:", ser_multi.get_settings())
        time.sleep(0.2)

        ser_multi.reset_input_buffer()
        ser_multi.write(b"*IDN?\r")
        ser_multi.flush()
        time.sleep(0.2)
        response = ser_multi.read_all()
        print(f"[DMM] IDN RAW: {response!r}")
        return ser_multi

    except Exception as e:
        print("Multimeter kein Port:", e)
        return None

# def connect_multi(baud=19200, timeout=2, port=MULTI_PORT):
#     try:
#         ser_multi = serial.Serial(port, baudrate=baud, timeout=timeout)
#         print(f"[SERIAL] Multimeter verbunden: {MULTI_PORT}")
#         time.sleep(0.5)

#         return ser_multi
#     except Exception as e:
#         print("Multimeter kein Port")

def connect_psu(port, baud=115200, timeout=2):
    try:
        ser_psu = serial.Serial(port, baudrate=baud, timeout=timeout)
        print(f"[SERIAL] Netzteil verbunden: {port}")
        time.sleep(0.5)
        return ser_psu
    except Exception as e:
        print("Netzteil kein Port")

def set_psu_parameters(ser_PSU, v_lim, c_lim, v_set, c_set):
    try:
        ser_PSU.write(b"OUTP OFF\n")
        time.sleep(0.2)
        ser_PSU.write(f"VOLT:LIM {v_lim}\n".encode())
        print(f"[PSU] Spannung Limit: {v_lim}")
        time.sleep(0.2)
        ser_PSU.write(f"CURR:LIM {c_lim}\n".encode())
        print(f"[PSU] Strom Limit: {c_lim}")
        time.sleep(0.2)
        ser_PSU.write(f"VOLT {v_set}\n".encode())
        print(f"[PSU] Spannung Ausgang: {v_set}")
        time.sleep(0.2)
        ser_PSU.write(f"CURR {c_set}\n".encode())
        print(f"[PSU] Strom Ausgang: {c_set}")
        time.sleep(0.2)
        ser_PSU.write(b"OUTP ON\n")
        time.sleep(0.2)
    except Exception as e:
        print("Netzteil Problem bei Parameter Settings")
    return


def set_part_parameters(ser_arduino, part_voltage, part_angle, part_speed, rel_sw, hohlwelle):
    ser_arduino.write(f"SETV:{part_voltage}\n".encode())
    print("[MCU] Spannung: ", part_voltage)
    time.sleep(0.2)
    ser_arduino.write(f"SETW:{part_angle}\n".encode())
    print("[MCU] Sollwinkel: ", part_angle)
    time.sleep(0.2)
    ser_arduino.write(f"SETS:{part_speed}\n".encode())
    print("[MCU] Speed: ", part_speed)
    time.sleep(0.2)
    ser_arduino.write(f"REL_SW:{rel_sw}\n".encode())
    time.sleep(0.2)
    print("[PRESET] relay_switch_pol =", rel_sw)
    ser_arduino.write(f"hohlwelle:{hohlwelle}\n".encode())
    time.sleep(0.2)
    print("[PRESET] hohlwelle =", hohlwelle)

def set_res_parameters(ser_arduino, res_init, res_final, res_total):
    ser_arduino.write(f"RES_I:{res_init}\n".encode())
    if(res_init==1):
        print("[MCU] Anfangswiderstand: Ja")
    else:
        print("[MCU] Anfangswiderstand: Nein")
    time.sleep(0.2)
    ser_arduino.write(f"RES_F:{res_final}\n".encode())
    if(res_final==1):
            print("[MCU] Endwiderstand: Ja")
    else:
            print("[MCU] Endwiderstand: Nein")
    time.sleep(0.2)
    ser_arduino.write(f"RES_T:{res_total}\n".encode())
    if(res_total==1):
            print("[MCU] Gesamtwiderstand: Ja")
    else:
            print("[MCU] Gesamtwiderstand: Nein")
    
def prepare_arduino_run(ser_arduino):
    if ser_arduino is None:
        return
    ser_arduino.flush()
    ser_arduino.reset_input_buffer()

PROGRESS_TEXTS = {
    # Mechanischer Endwinkel
    ("MECH", "INIT_GO"):
        "Messsystem wird initialisiert",
    ("MECH", "CHECK_BEGINNING"):
        "Ausgangslage wird geprüft",
    ("MECH", "CALIBRATE_CURRENTS"):
        "Servostrom wird kalibriert",
    ("MECH", "CHECK_END_END"):
        "Erfassung von mechanischen Endanschlag CW",
    ("MECH", "CHECK_END_START"):
        "Erfassung von mechanischen Endanschlag CCW",
    ("MECH", "ZERO_CHECK_ENDS"):
        "Rückfahrt auf Nullposition",
    ("MECH", "FINISH_CHECK_ENDS"):
        "Endanschlagsmessung beendet",
    ("MECH", "ENDLESS_VOLT_CROSSOVER"):
        "Nullbereich wird ermittelt",
    ("MECH", "ENDLESS_START_TICK"):
        "Startpunkt wird gesucht",
    ("MECH", "ENDLESS_END_TICK"):
        "Endpunkt wird gesucht",
    ("MECH", "ZERO_ENDLESS"):
        "Rückfahrt auf Nullposition",

    # Rauschen
    ("NOISE", "NOISE_GO"):
        "Motor fährt auf Startposition",
    ("NOISE", "NOISE_WAIT"):
        "Rauschprüfung wird vorbereitet",
    ("NOISE", "NOISE_MOVEMENT"):
        "Rauschprüfung startet",
    ("NOISE", "NOISE_FINISH"):
        "Rauschprüfung abgeschlossen",

    # Elektrischer Winkel
    ("ELEC", "ELEC_GO"):
        "Elektrische Winkelprüfung wird vorbereitet",
    ("ELEC", "D12_CHECK"):
        "Erfassung von elektrischer Winkel CW",
    ("ELEC", "D31_CHECK"):
        "Erfassung von elektrischer Winkel CCW",
    ("ELEC", "ELEC_FINISH"):
        "Elektrische Winkelprüfung abgeschlossen",

    # Linearität
    ("LINEAR", "LINEAR_START"):
        "Linearitätsprüfung wird vorbereitet",
    ("LINEAR", "D21_CHECK"):
        "Erfassung von Mittelanzapfung CW",
    ("LINEAR", "D21_BETWEEN"):
        "Erfassung von CW Zwischenpunkte",
    ("LINEAR", "D12_CHECK"):
        "Erfassung von Kurzschlusstrecke CW",
    ("LINEAR", "D22_CHECK"):
        "Erfassung von Mittelanzapfung CCW",
    ("LINEAR", "D22_BETWEEN"):
        "Erfassung von CCW Zwischenpunkte",
    ("LINEAR", "D32_CHECK"):
        "Erfassung von Kurzschlusstrecke CCW",
    ("LINEAR", "CALC_SUMMARY"):
        "Linearität wird ausgewertet",
    ("LINEAR", "LINEAR_FINISH"):
        "Linearitätsprüfung abgeschlossen",
    }

def handle_progress(line, expected_mode, on_progress):
    if not line.startswith("PROGRESS;"):
        return False

    try:
        parts = line.split(";", 3)

        if len(parts) != 4:
            print("Ungültige Fortschrittsmeldung:", line)
            return True

        _, mode, percent_text, phase = parts

        if mode != expected_mode:
            print(
                f"Unerwarteter Fortschrittsmodus: "
                f"{mode}, erwartet: {expected_mode}"
            )
            return True

        percent = int(percent_text)
        percent = max(0, min(100, percent))

        text = PROGRESS_TEXTS.get(
            (mode, phase),
            phase.replace("_", " ").title()
        )

        if on_progress is not None:
            on_progress(percent / 100.0, text)

        return True

    except ValueError:
        print("Ungültiger Prozentwert:", line)
        return True

def RegexMultimeter(output):
    match = re.search(r"[-+]?\d\.\d+(?:[Ee][-+]\d+)", output)
    #match = re.search("[+\-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?", output)
    if match:
        return match.group(0)
    return None

def get_multi_voltage(ser_arduino, ser_Multi):
    time.sleep(0.5)
    ser_Multi.reset_input_buffer()
    # ser_Multi.write(b"*IDN?\r")
    # ser_Multi.flush()

    # idn_raw = ser_Multi.read_until(b"\r")
    # print(f"[DMM] IDN während CALIB: {idn_raw!r}")

    # # Eventuelle Reste der IDN-Antwort entfernen
    # time.sleep(0.1)
    # ser_Multi.reset_input_buffer()

    ser_Multi.write(b":MEAS:VOLT:DC?\r")
    ser_Multi.flush()

    response_raw = ser_Multi.read_until(b"\r")
    # print(f"[DMM] Spannung RAW: {response_raw!r}")

    try:
        response = response_raw.decode("ascii").strip()
    except UnicodeDecodeError:
        print("[DMM] Beschädigte Nicht-ASCII-Antwort")
        ser_arduino.write(b"ISTV:ERR\n")
        return

    value = RegexMultimeter(response)

    if value is not None:
        voltage = float(value)
        print(f"Erfasste Spannung: {voltage}")
        ser_arduino.write(f"ISTV:{voltage}\n".encode())
    else:
        print("Problem bei DMM Response:", repr(response))
        ser_arduino.write(b"ISTV:ERR\n")


def get_multi_resistance(ser_arduino, ser_Multi, variation):
    ser_Multi.reset_input_buffer()
    ser_Multi.reset_output_buffer()

    ser_Multi.write(b":MEAS:RES?\r")
    # ser_Multi.write(b"*IDN?\n")
    # ser_Multi.write(b':READ?\n')
    #print("geschrieben")
    time.sleep(0.05)
    #print("sleep 0.2 sek")
    response = ser_Multi.readline().decode('utf-8', errors='ignore').strip()
    # print("DMM Antwort:", response)
    if response == "":
        print("DMM leere Antwort")
    #print("geantwortet")
    if(RegexMultimeter(response)):
        #print("check1")
        resistance = float(RegexMultimeter(response))
        #print("check2")
        print("---------------")
        if variation == 1:
            print(f"Erfasster Anfangswiderstand: {resistance}")
        elif variation == 2:
            print(f"Erfasster Endwiderstand: {resistance}")
        elif variation == 3:
            print(f"Erfasster Gesamtwiderstand: {resistance}")
        # elif variation == 4:
        #     print(f"Erfasster Anfangswiderstand: {resistance}")
        # elif variation == 5:
        #     print(f"Erfasster Endwiderstand: {resistance}")
        # elif variation == 6:
        #     print(f"Erfasster Gesamtwiderstand: {resistance}")
        else:
            print(f"Erfasster Widerstand: {resistance}")
        ser_arduino.write(f"ISTR:{resistance}\n".encode())
        #print("check3")
        return resistance
    else:
        print("Problem bei DMM Response")
        ser_arduino.write(f"ISTR:ERR\n".encode())
        None


def serial_ports():
    if sys.platform.startswith('win'):
        ports = list(serial.tools.list_ports.comports())
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for p in ports:
        try:
            print(p)
            
        except (OSError, serial.SerialException):
            pass
    return result

CANCEL_REASONS = {
    "USER_STOP": "Abbruch durch Benutzer oder GUI",
    "POSITION_READ_FAILED": "Servoposition konnte nicht gelesen werden",
    "MOVE_DISTANCE_EXCEEDED": "Zielposition liegt außerhalb des sicheren Fahrbereichs",
    "CURRENT_LIMIT_RPM1": "Stromgrenze bei Geschwindigkeitsstufe 1 überschritten",
    "CURRENT_LIMIT_RPM2": "Stromgrenze bei Geschwindigkeitsstufe 2 überschritten",
    "CURRENT_LIMIT_RPM3": "Stromgrenze bei Geschwindigkeitsstufe 3 überschritten",
    "CALIBRATION_CURRENT_LIMIT": "Maximalstrom während Stromkalibrierung überschritten",
    "CURRENT_CALIBRATION_FAILED": "Stromkalibrierung fehlgeschlagen",
    "TARGET_NOT_REACHED_LINEARITY": "Zielposition bei Linearitätsmessung nicht erreicht",
    "TARGET_NOT_REACHED_ENDLESS_LINEARITY": "Zielposition bei Endlos-Linearität nicht erreicht",
    "TARGET_NOT_REACHED_ELEC_DEG": "Zielposition beim elektrischen Winkel nicht erreicht",
    "TARGET_NOT_REACHED_ENDLESS_ELEC_DEG": "Zielposition beim Endlos-Winkel nicht erreicht",
    "INIT_STATE_INVALID": "Initialzustand der Messvariablen ist ungültig",
    "POSITION_NOT_NORMALIZED": "Startposition liegt nicht zwischen 0 und 4095 Ticks",
    "SAFETY_START_EXCEEDED": "Linke Sicherheitsgrenze wurde überschritten",
    "SAFETY_END_EXCEEDED": "Rechte Sicherheitsgrenze wurde überschritten",
}


def handle_cancel(line, workflow, stop_event=None):
    if line == "CANCEL":
        code = "UNKNOWN_LEGACY"
        details = ""
        reason = "Firmware hat keinen Abbruchgrund übermittelt"
    elif line.startswith("CANCEL:"):
        payload = line[len("CANCEL:"):]
        code, separator, details = payload.partition(";")
        reason = CANCEL_REASONS.get(code, "Unbekannter Abbruchgrund")
    else:
        return False

    message = f"[ABBRUCH][{workflow}] {reason} | Code: {code}"
    if details:
        message += f" | {details}"

    print(message)

    if stop_event is not None:
        stop_event.set()

    return True