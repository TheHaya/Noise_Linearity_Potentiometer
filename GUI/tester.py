import time, serial
from elec_deg_workflow import RegexMultimeter


PSU_PORT = "COM15"



def tests():
    with serial.Serial(PSU_PORT, baudrate=115200, timeout=5) as psu:

        time.sleep(0.2)
        psu.reset_input_buffer()
        psu.reset_output_buffer()

        psu.write(b"VOLT 10\n")
        time.sleep(0.2)
        psu.write(b"OUTP?\n")
        print("OUT:", psu.readline().decode(errors="ignore").strip())
