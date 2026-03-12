import time
import serial_client as sc


# --------------- GO_ZERO VARIABLES
root = None
txt_speed = None
cur_pos = 0

# --------------- GO_ZERO FUNCTION
def go_zero(ges_s=None, stop_event=None, on_finish=None):
    try:
        ser_arduino = sc.connect_ard()
        ser_arduino.reset_input_buffer() 
        ser_arduino.reset_output_buffer()
        time.sleep(1)
        ser_arduino.write(f"SETS:{ges_s}\n".encode())
        time.sleep(0.2)
        print("ZERO geschrieben")
        ser_arduino.write(b"ZERO\n")
        ser_arduino.timeout = 0.1
        while True:
            if stop_event.is_set():
                ser_arduino.write(b"STOP\n")
                ser_arduino.flush()
                time.sleep(0.2)
                break
            line = ser_arduino.readline().decode('utf-8').strip()
            if line == 'ZERO_READY':
                print("ZERO_READY empfangen.")
                break
            if line == 'CANCEL':
                print("CANCEL empfangen.")
                break
        ser_arduino.close()
    except Exception as e:
        print("Fehler bei Serial (GO ZERO): ", e) #debug

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()

def goto(txt_goto=None, ges_s=None):
    timeout = time.monotonic() + 5
    try:
        ser_arduino = sc.connect_ard()
        ser_arduino.reset_input_buffer() 
        ser_arduino.reset_output_buffer()
        time.sleep(1)
        ser_arduino.write(f"SETS:{ges_s}\n".encode())
        time.sleep(0.2)
        print("GOTO geschrieben")
        ser_arduino.write(f"goto:{txt_goto}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(b"GOTO\n")
        time.sleep(0.2)
        while time.monotonic() < timeout:
            line = ser_arduino.readline().decode('utf-8').strip()
            if line == 'GOTO_READY':
                print("GOTO_READY empfangen.")
                break
        ser_arduino.close()
    except Exception as e:
        print("Fehler bei Serial (GO TO): ", e) #debug

    # if root is not None:
    #     root.after(0, on_finish)
    # else:
    #     on_finish()

def show_pos():
    timeout = time.monotonic() + 5
    try:
        ser_arduino = sc.connect_ard()
        ser_arduino.reset_input_buffer() 
        ser_arduino.reset_output_buffer()
        time.sleep(1)
        ser_arduino.write(b"WHERE\n")
        time.sleep(0.2)
        print("WHERE geschrieben")
        while time.monotonic() < timeout:
            line = ser_arduino.readline().decode('utf-8').strip()
            if line.startswith("WHERE_POS"):
                global cur_pos
                cur_pos = float(line[9::])
                print(f"WHERE_POS empfangen. Position ist: {cur_pos}")
                break
        ser_arduino.close()
    except Exception as e:
        print("Fehler bei Serial (SHOW POS): ", e)

def reset_arduino():
    try:
        
        ser_arduino = sc.connect_ard()
        ser_arduino.reset_input_buffer() 
        ser_arduino.reset_output_buffer()
        time.sleep(0.1)
        ser_arduino.write(b"STOP\n")
        time.sleep(0.1)
        ser_arduino.dtr = False
        time.sleep(0.1)
        ser_arduino.dtr = True
        time.sleep(0.1)
        ser_arduino.rts = False
        time.sleep(0.1)
        ser_arduino.rts = True
        ser_arduino.close()
        print("Arduino reset ausgelöst.")
    except Exception as e:
        print("Fehler bei Serial (RESET_ARDUINO): ", e)
