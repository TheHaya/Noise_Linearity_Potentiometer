import threading, time
from datetime import datetime
import pandas as pd
import os, serial
import pandas as pd
import xlwings as xw
from itertools import cycle
from linear_workflow import daten
import serial_client as sc
import mech_ends_workflow

TEST_RUNS = 40
_tester_running = False

# NUR TESTER FÜR 
ALIGN_CENTER = -4108
ALIGN_LEFT = -4131


def test_relays(ser_ard):
    ser_ard.write(b"REL_TESTER\n")

def tester_func(port, baud=19200, timeout=3):
    try:
        ser_multi = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )

        print("[DMM] Einstellungen:", ser_multi.get_settings())
        for i in range(0, 100, 1):
            time.sleep(0.2)

            ser_multi.reset_input_buffer()
            ser_multi.write(b"*IDN?\r")
            ser_multi.flush()
            time.sleep(0.2)
            response = ser_multi.read_all()
            print(f"{i}: [DMM] IDN RAW: {response!r}")
        return ser_multi

    except Exception as e:
        print("Multimeter kein Port:", e)
        return None
