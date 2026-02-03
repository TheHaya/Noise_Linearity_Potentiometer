import serial, time, sys, threading
import serial.tools.list_ports

# --------------- SERIAL VARIABLES
ser_Arduino = None
ARDUINO_PORT1 = "COM3"
ARDUINO_PORT2 = "COM5"
ARDUINO_PORT3 = "COM9"


# --------------- SERIAL MIT SERVO
def open_first_available(baud=115200, timeout=2, ports=(ARDUINO_PORT1, ARDUINO_PORT2, ARDUINO_PORT3)):
    last = None
    print(serial_ports())
    for p in ports:
        try:
            ser = serial.Serial(p, baudrate=baud, timeout=timeout)
            print(f"[SERIAL] Verbunden: {p}")
            time.sleep(1)
            return ser
        except Exception as e:
            last = e
    raise RuntimeError(f"Kein Port aus {ports} verfügbar: {last}")

def serial_ports():
    if sys.platform.startswith('win'):
        ports = list(serial.tools.list_ports.comports())
        #ports = ['COM%s' % (i + 1) for i in range(256)]
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for p in ports:
        try:
            print(p)
            #s = serial.Serial(port)
            #s.close()
            #result.append(port)
            
        except (OSError, serial.SerialException):
            pass
    return result

class serial_manager:
    def __init__(self, root, on_button = None):
        self.root = root
        self.ser = None
        self.alive = False
        self.busy = False
        self.on_button = on_button

    def connect(self, ports=(ARDUINO_PORT1, ARDUINO_PORT2, ARDUINO_PORT3), baud=115200):
        for p in ports:
            try:
                self.ser = serial.Serial(p, baudrate=baud, timeout=0.1, write_timeout=1)
                self.alive = True
                threading.Thread(target=self.reader, daemon=True).start()
                print(f"[SERIAL] Verbunden: {p}")
                time.sleep(0.5)
                return self.ser
            except Exception as e:
                last = e
        raise RuntimeError(f"Kein Port aus {ports} verfügbar: {last}")

    def reader(self):
        while self.alive:
            try:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                if line == "BUTTON":
                    if not self.busy:
                        self.root.after(0, self.on_button)

            except Exception:
                time.sleep(0.2)

    def write(self, s: str):
        if self.ser and self.ser.is_open:
            self.ser.write((s + "\n").encode())
