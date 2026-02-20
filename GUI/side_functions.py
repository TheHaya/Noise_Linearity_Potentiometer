import time
from serial_client import open_first_available


# --------------- GO_ZERO VARIABLES
root = None
txt_speed = None


# --------------- GO_ZERO FUNCTION
def go_zero(stop_event, on_finish):
    try:
        ser_arduino = open_first_available(baud=115200, timeout=5)
        ser_arduino.reset_input_buffer() 
        ser_arduino.reset_output_buffer()
        time.sleep(1)
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
            print("Empfangen:", line) #debug
            if line == 'ZERO_READY':
                break
            if line == 'CANCEL':
                break
        ser_arduino.close()
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()

def goto(txt_goto, stop_event,  on_finish):
    try:
        ser_arduino = open_first_available(baud=115200, timeout=5)
        ser_arduino.reset_input_buffer() 
        ser_arduino.reset_output_buffer()
        time.sleep(1)
        print("GOTO geschrieben")
        ser_arduino.write(f"goto:{txt_goto}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(b"GOTO\n")
        ser_arduino.timeout = 0.1
        while True:
            if stop_event.is_set():
                ser_arduino.write(b"STOP\n")
                ser_arduino.flush()
                time.sleep(0.2)
                break
            line = ser_arduino.readline().decode('utf-8').strip()
            print("Empfangen:", line) #debug
            if line == 'GOTO_READY':
                break
            if line == 'CANCEL':
                break
        ser_arduino.close()
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()