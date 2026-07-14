import serial, time, sys, re
import serial.tools.list_ports

# --------------- SERIAL VARIABLES
ser_Arduino = None
# ------ PRÜFVORRICHTUNG FIRMA
# ARDUINO_PORT = "COM7"
# MULTI_PORT = "COM4"
# PSU_PORT = "COM5"

# ------ ALWIN LAPTOP
ARDUINO_PORT = "COM20"
MULTI_PORT = "COM6"
PSU_PORT = "COM7"


# --------------- SERIAL MIT SERVO
def connect_ard(baud=115200, timeout=0.1, port=ARDUINO_PORT):
    serial_ports()
    err_time = time.monotonic() + 15
    while time.monotonic() < err_time:
        try:
            ser_ard = serial.Serial(port, baudrate=baud, timeout=timeout)
            print(f"[SERIAL] Mikrocontroller verbunden: {port}")
            time.sleep(0.5)
            return ser_ard
        except Exception as e:
            print("Mikrocontroller kein Port")

def connect_multi(baud=19200, timeout=2, port=MULTI_PORT):
    try:
        ser_multi = serial.Serial(port, baudrate=baud, timeout=timeout)
        print(f"[SERIAL] Multimeter verbunden: {MULTI_PORT}")
        time.sleep(0.5)

        return ser_multi
    except Exception as e:
        print("Multimeter kein Port")

def connect_psu(baud=115200, timeout=2, port=PSU_PORT):
    try:
        ser_psu = serial.Serial(port, baudrate=baud, timeout=timeout)
        print(f"[SERIAL] Netzteil verbunden: {PSU_PORT}")
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


def set_part_parameters(ser_arduino, part_voltage, part_angle, part_speed, rel_sw):
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
    ser_Multi.reset_input_buffer()
    ser_Multi.reset_output_buffer()

    ser_Multi.write(b':MEAS:VOLT:DC?\n')
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
        voltage = float(RegexMultimeter(response))
        #print("check2")
        print(f"Erfasste Spannung: {voltage}")
        ser_arduino.write(f"ISTV:{voltage}\n".encode())
        #print("check3")
    else:
        print("Problem bei DMM Response")
        ser_arduino.write(f"ISTV:ERR\n".encode())
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
