import time, re, serial
from serial_client import open_first_available


# --------------- ELEC DEG VARIABLES
root = None
MULTI_PORT = "COM17"
PSU_PORT = "COM15"


# --------------- ELEC DEG FUNCTIONS
def RegexMultimeter(output):
    match = re.search(r"[-+]?\d\.\d+(?:[Ee][-+]\d+)", output)
    #match = re.search("[+\-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?", output)
    if match:
        return match.group(0)
    return None

def config(app_root, txt_speed_entry, ser_arduino_app=None):
    global root, txt_speed, ser_arduino
    root = app_root
    txt_speed = txt_speed_entry
    #ser_arduino = ser_arduino_app

def measurement(ges_v=None, ges_w=None, ges_s=None, d12=None, 
                d21=None, d22=None, d31=None, stop_event=None, on_finish=None):
    try:
        ser_arduino = open_first_available(baud=115200, timeout=5)
        try:
            ser_Multi = serial.Serial(MULTI_PORT, baudrate=9600, timeout = 0.5)
            print(f"[SERIAL] Verbunden: {MULTI_PORT}")
        except Exception as e:
            print("Multimeter kein Port")

        try:
            ser_PSU = serial.Serial(PSU_PORT, baudrate=115200, timeout = 0.5)
            print(f"[SERIAL] Verbunden: {PSU_PORT}")
        except Exception as e:
            print("Netzteil kein Port")
        ser_PSU.write(b"OUTP OFF\n")
        time.sleep(0.2)
        ser_PSU.write(b"VOLT 10\n")
        time.sleep(0.2)
        ser_PSU.write(b"CURR 0.004\n")
        time.sleep(0.2)
        ser_PSU.write(b"VOLT:LIM 12\n")
        time.sleep(0.2)
        ser_PSU.write(b"CURR:LIM 0.120\n")
        time.sleep(0.2)
        ser_PSU.write(b"OUTP ON\n")
        time.sleep(0.2)
        N = 13 #Anz Messpunkte wegen leere Zellen

        time.sleep(0.2)
        ser_arduino.write(f"SETV:{ges_v}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"SETW:{ges_w}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"SETS:{ges_s}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead12:{d12}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead21:{d21}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead22:{d22}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead31:{d31}\n".encode())
        time.sleep(0.2)
        print("Sende: GO") #debug
        #print(d11, d12, d21, d22, d31, d32)
        ser_arduino.write(b"ELEC_DEG_GO\n")

        ser_arduino.timeout = 0.1
        while True:
            if stop_event.is_set():
                ser_arduino.write(b"STOP\n")
                time.sleep(0.5)
                ser_arduino.flush()
                time.sleep(0.2)
                break

            line = ser_arduino.readline().decode('utf-8').strip()
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
                    ser_arduino.write(f"ISTV:{voltage}\n".encode())
                    #print("check3")
                else:
                    print("Problem bei Response")
                    None
                continue
            elif line == 'ELEC_DEG_READY':
                print("ELEC_DEG READY empfangen")
                ser_arduino.write(b"ELEC_DEG_START\n")
                print("Sende: ELEC_DEG START")
            elif line.startswith('TOTAL_ELEC'):
                global total_elec
                total_elec = float(line[10::])
                print("Gesamt Elektr. Winkel:")
                print(total_elec)

            elif line == 'ELEC_DEG_FINISH':
                break
            elif line == 'CANCEL':
                break
            
        ser_arduino.close()
        ser_Multi.close()
        ser_PSU.close()
                        
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()