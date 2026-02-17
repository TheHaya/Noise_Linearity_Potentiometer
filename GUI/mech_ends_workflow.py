import time, serial
from serial_client import open_first_available
import pico_runner
from ring import mark_ends, mark_noise_segments, set_circle_text
from elec_deg_workflow import RegexMultimeter

# --------------- MECH ENDS VARIABLES
root = None
txt_speed = None
MULTI_PORT = "COM17"
PSU_PORT = "COM15"
delay_time1 = 0.0
delay_time2 = 0.0
delay_time3 = 0.0
total_ticks = 0

# --------------- MECH ENDS FUNCTIONS

def config(app_root, txt_speed_entry, ser_arduino_app=None):
    global root, txt_speed, ser_arduino
    root = app_root
    txt_speed = txt_speed_entry
    #ser_arduino = ser_arduino_app
    
def measurement(ges_v=None, ges_w=None, ges_s=None, stop_event=None, on_finish=None):
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

        ser_PSU.write(b"VOLT 10\n")
        time.sleep(0.2)
        ser_PSU.write(b"CURR 0.004\n")
        time.sleep(0.2)
        ser_PSU.write(b"VOLT:LIM 12\n")
        time.sleep(0.2)
        ser_PSU.write(b"CURR:LIM 0.120\n")
        time.sleep(0.2)
        ser_arduino.write(f"SETW:{ges_w}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"SETS:{ges_s}\n".encode())
        time.sleep(0.2)
        print("speed ist", ges_s)
        print("Sende: GO") #debug
        ser_arduino.write(b"INIT_GO\n")

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
            if line.startswith("ANGLE"):
                global total_mech
                total_mech = float(line[5::])
                global total_ticks
                total_ticks = round(total_mech*(4096/360))
                print("Gesamtwinkel ist: ")
                print(total_mech)
                break
            
            elif line.startswith("DELAY1"):
                global delay_time1
                delay_time1 = float(line[6::])
                print(f"{delay_time1}")
                
            elif line.startswith("DELAY2"):
                global delay_time2
                delay_time2 = float(line[6::])
                print(f"{delay_time2}")
                
            elif line.startswith("DELAY3"):
                global delay_time3
                delay_time3 = float(line[6::])
                print(f"{delay_time3}")

            #elif line == 'ENDS_FINISH':
            #    break
            elif line == 'CANCEL':
                break

        ser_arduino.close()

    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()
