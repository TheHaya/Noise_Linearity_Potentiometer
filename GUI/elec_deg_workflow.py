import time, re, serial
from serial_client import open_first_available


# --------------- ELEC DEG VARIABLES
root = None
MULTI_PORT = "COM15"
daten = []


# --------------- ELEC DEG FUNCTIONS
def RegexMultimeter(output):
    match = re.search(r"[-+]?\d\.\d+(?:[Ee][-+]\d+)", output)
    #match = re.search("[+\-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?", output)
    if match:
        return match.group(0)
    return None

def config(app_root, txt_speed_entry):
    global root, txt_speed
    root = app_root
    txt_speed = txt_speed_entry

def measurement(ges_v=None, ges_w=None, ges_s=None, d12=None, 
                d21=None, d22=None, d31=None, stop_event=None, on_finish=None):
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

        time.sleep(0.2)
        ser_Arduino.write(f"SETV:{ges_v}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"SETW:{ges_w}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"SETS:{ges_s}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"dead12:{d12}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"dead21:{d21}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"dead22:{d22}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"dead31:{d31}\n".encode())
        time.sleep(0.2)
        print("Sende: ELEC_DEG_GO") #debug
        #print(d11, d12, d21, d22, d31, d32)
        ser_Arduino.write(b"ELEC_DEG_GO\n")

        ser_Arduino.timeout = 0.1
        while True:
            if stop_event.is_set():
                ser_Arduino.write(b"STOP\n")
                time.sleep(0.5)
                ser_Arduino.flush()
                time.sleep(0.2)
                break

            line = ser_Arduino.readline().decode('utf-8').strip()
            #print("Empfangen:", line) #debug
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
            elif line == 'ELEC_DEG_READY':
                print("ELEC_DEG_READY empfangen")
                ser_Arduino.write(b"ELEC_DEG_START\n")
                print("Sende: ELEC_DEG_START")
            elif line == 'ELEC_DEG_FINISH':
                break
            elif line == 'CANCEL':
                break
            
        ser_Arduino.close()
        ser_Multi.close()
                        
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()