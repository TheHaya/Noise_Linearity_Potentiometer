import time, re, serial
from serial_client import open_first_available


# --------------- LINEAR VARIABLES
root = None
MULTI_PORT = "COM15"
daten = []

# --------------- LINEAR FUNCTIONS
def RegexMultimeter(output):
    match = re.search(r"[-+]?\d\.\d+(?:[Ee][-+]\d+)", output)
    #match = re.search("[+\-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?", output)
    if match:
        return match.group(0)
    return None

def config_linear(app_root, txt_speed_entry):
    global root, txt_speed
    root = app_root
    txt_speed = txt_speed_entry

def linear_measurement(ges_v, ges_w, ges_s, d11, d12, d21, d22, d31, d32, stop_event, on_finish):
    try:
        ser_Arduino = open_first_available(baud=115200, timeout=5)
        try:
            ser_Multi = serial.Serial(MULTI_PORT, baudrate=9600, timeout = 0.5)
            print(f"[SERIAL] Verbunden: {MULTI_PORT}")
        except Exception as e:
            print("Multimeter kein Port")
        N = 13 #Anz Messpunkte wegen leere Zellen
        global daten
        daten = []
        linear_sollV = [None] * N
        linear_lin = [None] * N
        error_lin_idx = set()
        lin_max = None
        lin_min = None
        summary_vals = {}
        time.sleep(0.2)
        ser_Arduino.write(f"SETV:{ges_v}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"SETW:{ges_w}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"SETS:{ges_s}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"dead11:{d11}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"dead12:{d12}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"dead21:{d21}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"dead22:{d22}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"dead31:{d31}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"dead32:{d32}\n".encode())
        time.sleep(0.2)
        print("Sende: GO") #debug
        #print(d11, d12, d21, d22, d31, d32)
        ser_Arduino.write(b"LINEAR_GO\n")

        ser_Arduino.timeout = 0.1
        while True:
            if stop_event.is_set():
                ser_Arduino.write(b"STOP\n")
                time.sleep(0.5)
                ser_Arduino.flush()
                time.sleep(0.2)
                break

            line = ser_Arduino.readline().decode('utf-8').strip()
            print("Empfangen:", line) #debug
            if line == 'VOLTR':
                ser_Multi.reset_input_buffer()
                ser_Multi.reset_output_buffer()
                ser_Multi.write(b':MEAS:VOLT:DC?\n')
                #print("geschrieben")
                time.sleep(0.05)
                #print("sleep 0.2 sek")
                response = ser_Multi.readline().decode('utf-8', errors='ignore').strip()
                #print("geantwortet")
                if(RegexMultimeter(response)):
                    #print("check1")
                    voltage  = float(RegexMultimeter(response))
                    #print("check2")
                    print(voltage)
                    ser_Arduino.write(f"ISTV:{voltage}\n".encode())
                    #print("check3")
                else:
                    print("Problem bei Response")
                    None
                continue
            elif line.startswith("SUMMARY;"):
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
                ser_Arduino.write(b"LINEAR_START\n")
            elif line == 'CANCEL':
                break
            
        ser_Arduino.close()
        ser_Multi.close()
                        
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
        root.after(0, lambda: on_finish(result))

    else:
        on_finish(result)