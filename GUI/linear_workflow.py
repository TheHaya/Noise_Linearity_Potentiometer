import time, re
import serial_client as sc


# --------------- LINEAR VARIABLES
root = None
daten = []
result = {}
lin_error = False
summary_vals = {}
# --------------- LINEAR FUNCTIONS
def RegexMultimeter(output):
    match = re.search(r"[-+]?\d\.\d+(?:[Ee][-+]\d+)", output)
    #match = re.search("[+\-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?", output)
    if match:
        return match.group(0)
    return None

def config(app_root, txt_speed_entry, ser_arduino_app=None, ser_psu_app=None, ser_multi_app=None):
    global root, txt_speed, ser_arduino, ser_PSU, ser_Multi
    root = app_root
    txt_speed = txt_speed_entry
    ser_arduino = ser_arduino_app
    ser_PSU = ser_psu_app
    ser_Multi = ser_multi_app

def measurement(ges_v=None, ges_w=None, ges_s=None, rel_sw = None, d11=None, d12=None, 
                d21=None, d22=None, d31=None, d32=None, stop_event=None, on_finish=None):
    try:
        global lin_error
        lin_error = False
        N = 13 #Anz Messpunkte wegen leere Zellen
        global daten, result
        result = {
            "daten": [],
            "linear_sollV": [None] * N,
            "linear_lin": [None] * N,
            "summary_vals": {},
            "lin_max": None,
            "lin_min": None,
            "error_lin_idx": set(),}
        daten = []
        linear_sollV = [None] * N
        linear_lin = [None] * N
        error_lin_idx = set()
        global lin_max, lin_min
        lin_max = None
        lin_min = None
        global summary_vals
        summary_vals = {}

        #ser_arduino = sc.connect_ard()
        # ser_Multi = sc.connect_multi()
        # ser_PSU = sc.connect_psu()
        sc.set_psu_parameters(ser_PSU, 12, 0.12, 10, 0.004)
        sc.set_part_parameters(ser_arduino, ges_v, ges_w, ges_s, rel_sw)

        ser_arduino.write(f"dead11:{d11}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead12:{d12}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead21:{d21}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead22:{d22}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead31:{d31}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead32:{d32}\n".encode())
        time.sleep(0.2)
        print("LINEAR Sende: GO") #debug
        #print(d11, d12, d21, d22, d31, d32)
        # ser_arduino.reset_input_buffer()
        # ser_arduino.reset_output_buffer()

        sc.prepare_arduino_run(ser_arduino)
        ser_arduino.write(b"LINEAR_GO\n")

        #ser_arduino.timeout = 0.1
        while True:
            if stop_event.is_set():
                ser_arduino.write(b"STOP\n")
                print("STOP EMPFANGEN")
                time.sleep(0.2)
                ser_arduino.flush()
                ser_PSU.write(b"OUTP OFF\n")
                print("PSU: OUTPUT OFF")
                time.sleep(0.2)
                break

            line = ser_arduino.readline().decode('utf-8').strip()
            #print("Empfangen:", line) #debug
            if line == 'VOLTR':
                sc.get_multi_voltage(ser_arduino, ser_Multi)
                continue
            elif line.startswith('DEBUG_POS'):
                debug_pos = float(line[9::])
                print(f"Position für Debug: {debug_pos} // {debug_pos*0.087890625}")
                print("_____")
            elif line.startswith('DEAD_CCW1'):
                dead_ccw1 = float(line[9::])
                print(f"--Deadzone CCW links: {dead_ccw1}")
            elif line.startswith('DEAD_CCW2'):
                dead_ccw2 = float(line[9::])
                print(f"--Deadzone CCW rechts: {dead_ccw2}")
            elif line.startswith('DEAD_CW1'):
                dead_cw1 = float(line[8::])
                print(f"--Deadzone CW links: {dead_cw1}")
            elif line.startswith('DEAD_CW2'):
                dead_cw2 = float(line[8::])
                print(f"--Deadzone CW rechts: {dead_cw2}")
            elif line.startswith('TOTAL_ELEC'):
                print("Empfangen: TOTAL_ELEC")
                global total_elec
                total_elec = float(line[10::])
                print("Gesamt Elektr. Winkel:")
                print(total_elec)
            elif line.startswith("SUMMARY;"):
                print("Empfangen: SUMMARY;")
                try:
                    parts = line.split(";")[1:]
                    for p in parts:
                        if ":" in p:
                            i, val = p.split(":", 1)
                            summary_vals[i] = float(val)
                except Exception as e:
                    print("Fehler SUMMARY-Parse:", e)
                continue
            elif line.startswith("RESULT;"):
                print("Empfangen: RESULT;")
                try:
                    parts = dict(p.split(":", 1) for p in line.split(";")[1:])
                    i = int(parts["idx"])
                    if "Soll-Spannung Real" in parts:
                        linear_sollV[i] = float(parts["Soll-Spannung Real"])
                        print(linear_sollV[i])
                    if "Linearität" in parts:
                        linear_lin[i] = float(parts["Linearität"])
                        print(linear_lin[i])
                except Exception as e:
                    print("Fehler LINEAR-Parse:", e)
                continue
            elif line.startswith("ERROR_LIN;"):
                try:
                    parts = dict(p.split(":", 1) for p in line.split(";")[1:])
                    
                    idx_str = parts.get("IDX", "")
                    if idx_str:
                        error_lin_idx = {int(s) for s in idx_str.split(",") if s.strip().isdigit()}
                    
                    if "LIN_MAX" in parts:
                        lin_max = float(parts["LIN_MAX"])
                    if "LIN_MIN" in parts:
                        lin_min = float(parts["LIN_MIN"])
                except Exception as e:
                    print("Fehler ERROR_LIN-Parse:", e)
                continue
            elif line.startswith("Soll-Winkel:"):
                try:
                    parts = line.split(";")
                    sollwinkel = float(parts[0].split(":")[1])
                    sollspannung = float(parts[1].split(":")[1])
                    istspannung = float(parts[2].split(":")[1])
                    istwinkel = float(parts[3].split(":")[1])
                    realwinkelmitte = float(parts[4].split(":")[1])
                    daten.append([sollwinkel, sollspannung, istspannung, istwinkel, 
                                  realwinkelmitte])
                except Exception as e:
                    print("Fehler beim Parsen:", e) #debug
                    continue
            elif line == 'LINEAR_READY':
                print("Empfangen: LINEAR_READY")
                ser_arduino.write(b"LINEAR_START\n")
            elif line == 'LINEAR_FINISH':
                print("Empfangen: LINEAR_FINISH")
                break
            elif line == 'CANCEL':
                print("Empfangen: CANCEL")
                if stop_event is not None:
                    stop_event.set()
                ser_arduino.reset_input_buffer()
                break
            
        ser_PSU.write(b"OUTP OFF\n")
        #ser_arduino.close()
        # ser_Multi.close()
        # print("[SERIAL] Multimeter close")
        # ser_PSU.close()
        # print("[SERIAL] Netzteil close")
                        
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

    
    result = {
    "daten": daten,
    "linear_sollV": linear_sollV,
    "linear_lin": linear_lin,
    "summary_vals": summary_vals,
    "lin_max": lin_max,
    "lin_min": lin_min,
    "error_lin_idx": error_lin_idx}

    if root is not None:
        root.after(0, on_finish)

    else:
        on_finish()