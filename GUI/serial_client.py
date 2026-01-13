import serial, time
import pico_runner


# --------------- SERIAL VARIABLES
ser_Arduino = None
ARDUINO_PORT1 = "COM3"
ARDUINO_PORT2 = "COM5"
ARDUINO_PORT3 = "COM9"


# --------------- SERIAL MIT SERVO
def open_first_available(baud=115200, timeout=2, ports=(ARDUINO_PORT1, ARDUINO_PORT2, ARDUINO_PORT3)):
    last = None
    for p in ports:
        try:
            ser = serial.Serial(p, baudrate=baud, timeout=timeout)
            print(f"[SERIAL] Verbunden: {p}")
            time.sleep(1)
            return ser
        except Exception as e:
            last = e
    raise RuntimeError(f"Kein Port aus {ports} verfügbar: {last}")

