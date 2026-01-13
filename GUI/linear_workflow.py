import time
from serial_client import open_first_available


# --------------- LINEAR VARIABLES
root = None

# --------------- LINEAR FUNCTIONS
def linear_measurement(ges_w, ges_s, stop_event, on_finish):
    try:
        global pico_pdf_time
        pico_pdf_time = []
        global pico_time
        pico_time = []
        pico_turn = []
        global pico_angle
        pico_angle = []
        global pico_volt
        pico_volt = []

        ser_Arduino = open_first_available(baud=115200, timeout=5)
        time.sleep(0.2)
        ser_Arduino.write(f"SETW:{ges_w}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"SETS:{ges_s}\n".encode())
        time.sleep(0.2)
        print("speed ist", ges_s)
        print("Sende: GO") #debug
        ser_Arduino.write(b"GO\n")

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
                global total_ticks
                total_ticks = float(line[5::])

            if line == 'READY':
                break

            elif line == 'FINISH':
                break

            elif line == 'CANCEL':
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
           
        ser_Arduino.close()

    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

    root.after(0, on_finish)
