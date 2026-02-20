import time, serial
from elec_deg_workflow import RegexMultimeter

ard_port = "COM18"

def tests():
    with serial.Serial(ard_port, baudrate=115200, timeout=5) as ser_ard:
        time.sleep(2.0)  # wichtig: Arduino booten lassen!
        ser_ard.reset_input_buffer()
        ser_ard.write(b"SWITCH\n")
        time.sleep(0.2)
        time.sleep(0.2)
        print(ser_ard.read_all().decode(errors="ignore"))