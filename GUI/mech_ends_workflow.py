import time
from serial_client import open_first_available
import pico_runner
from ring import mark_ends, mark_noise_segments, set_circle_text


# --------------- MECH ENDS VARIABLES
root = None
txt_speed = None

  
# --------------- MECH ENDS FUNCTIONS

def measurement(ges_v=None, ges_w=None, ges_s=None, stop_event=None, on_finish=None):
    try:
        ser_Arduino = open_first_available(baud=115200, timeout=5)
        time.sleep(0.2)
        ser_Arduino.write(f"SETW:{ges_w}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"SETS:{ges_s}\n".encode())
        time.sleep(0.2)
        print("speed ist", ges_s)
        print("Sende: GO") #debug
        ser_Arduino.write(b"INIT_GO\n")

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

            if line.startswith("ANGLE"):
                global total_angle
                total_angle = float(line[5::])
                print("Gesamtwinkel ist: ")
                print(total_angle)
                break
            #elif line == 'ENDS_FINISH':
            #    break
            elif line == 'CANCEL':
                break

        ser_Arduino.close()

    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()
