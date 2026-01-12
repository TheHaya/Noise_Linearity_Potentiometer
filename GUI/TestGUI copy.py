
import  serial, time, json, subprocess, math














# --------------- DEBUG FUNCTION
"""
def go_left():
    try:
        global ser_Arduino
        if ser_Arduino is None or not ser_Arduino.is_open:
            print("Nicht verbunden.")
            return
        
        ser_Arduino.reset_input_buffer() 
        ser_Arduino.reset_output_buffer()
        time.sleep(1)
        print("LEFT geschrieben")
        ser_Arduino.write(b"LEFT\n")
        ser_Arduino.timeout = 0.1
        while True:
            line = ser_Arduino.readline().decode('utf-8').strip()
            print("Empfangen:", line) #debug
            if line == 'READY':
                break
            if line == 'CANCEL':
                break
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

def go_Right():
    try:
        ser_Arduino.write(b"RIGHT\n")
        print("RIGHT geschrieben")
        ser_Arduino.timeout = 0.1
        while True:
            line = ser_Arduino.readline().decode('utf-8').strip()
            print("Empfangen:", line) #debug
            if line == 'READY':
                break
            if line == 'CANCEL':
                break
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

def ser_Connect():
    try:
        global ser_Arduino
        if ser_Arduino is not None:
            ser_Arduino.close()
            ser_Arduino = None
            print("Serial Disconnected")
        else:
            ser_Arduino = open_first_available((ARDUINO_PORT1, ARDUINO_PORT2), baud=115200, timeout=5)
            ser_Arduino.reset_input_buffer() 
            ser_Arduino.reset_output_buffer()
            time.sleep(1)
            print("Serial Connected")
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

def curr_Pos():
    try:
        ser_Arduino.write(b"POS\n")
        print("POS geschrieben")
        ser_Arduino.timeout = 0.1
        while True:
            line = ser_Arduino.readline().decode('utf-8').strip()
            print("Empfangen:", line) #debug
            time.sleep(0.1)
            if line == 'READY':
                break
            if line == 'CANCEL':
                break
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

def goto():
    try:
        txtgoto = float(txtgo.get().strip())
        ser_Arduino.write(f"goto:{txtgoto}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(b"GOTO\n")
        print("GOTO geschrieben")
        ser_Arduino.timeout = 0.1
        while True:
            line = ser_Arduino.readline().decode('utf-8').strip()
            print("Empfangen:", line) #debug
            time.sleep(0.1)
            if line == 'READY':
                break
            if line == 'CANCEL':
                break
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug
"""










"""
if __name__ == "__main__":
    x = [1, 2, 1, 3, 4, 3]
    y = [1, 2, 3, 4, 5, 6]
    save_xy_to_pdf(x, y, filename="xy_plot.pdf", title="x–y Plot")
    print("PDF geschrieben: xy_plot.pdf")
"""








