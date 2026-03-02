import serial, time, sys, re
import serial.tools.list_ports

# --------------- SERIAL VARIABLES
ser_Arduino = None
ARDUINO_PORT = "COM18"
MULTI_PORT = "COM17"
PSU_PORT = "COM15"

# --------------- SERIAL MIT SERVO
def connect_ard(baud=115200, timeout=2, port=ARDUINO_PORT):
    serial_ports()
    err_time = time.monotonic() + 15
    while time.monotonic() < err_time:
        try:
            ser_ard = serial.Serial(port, baudrate=baud, timeout=timeout)
            print(f"[SERIAL] Mikrocontroller verbunden: {port}")
            time.sleep(0.5)
            return ser_ard
        except Exception as e:
            print("Mikrocontroller kein Port")

def connect_multi(baud=9600, timeout=2, port=MULTI_PORT):
    try:
        ser_multi = serial.Serial(port, baudrate=baud, timeout=timeout)
        print(f"[SERIAL] Multimeter verbunden: {MULTI_PORT}")
        time.sleep(0.5)
        return ser_multi
    except Exception as e:
        print("Multimeter kein Port")

def connect_psu(baud=115200, timeout=2, port=PSU_PORT):
    try:
        ser_psu = serial.Serial(port, baudrate=baud, timeout=timeout)
        print(f"[SERIAL] Netzteil verbunden: {PSU_PORT}")
        time.sleep(0.5)
        return ser_psu
    except Exception as e:
        print("Netzteil kein Port")

def set_psu_parameters(ser_PSU, v_lim, c_lim, v_set, c_set):
    ser_PSU.write(b"OUTP OFF\n")
    time.sleep(0.2)
    ser_PSU.write(f"VOLT:LIM {v_lim}\n".encode())
    print(f"[PSU] Spannung Limit: {v_lim}")
    time.sleep(0.2)
    ser_PSU.write(f"CURR:LIM {c_lim}\n".encode())
    print(f"[PSU] Strom Limit: {c_lim}")
    time.sleep(0.2)
    ser_PSU.write(f"VOLT {v_set}\n".encode())
    print(f"[PSU] Spannung Ausgang: {v_set}")
    time.sleep(0.2)
    ser_PSU.write(f"CURR {c_set}\n".encode())
    print(f"[PSU] Strom Ausgang: {c_set}")
    time.sleep(0.2)
    ser_PSU.write(b"OUTP ON\n")
    time.sleep(0.2)
    return


def set_part_parameters(ser_arduino, part_voltage, part_angle, part_speed):
    ser_arduino.write(f"SETV:{part_voltage}\n".encode())
    print("[MCU] Spannung: ", part_voltage)
    time.sleep(0.2)
    ser_arduino.write(f"SETW:{part_angle}\n".encode())
    print("[MCU] Gesamtwinkel: ", part_angle)
    time.sleep(0.2)
    ser_arduino.write(f"SETS:{part_speed}\n".encode())
    print("[MCU] Speed: ", part_speed)
    time.sleep(0.2)
    

def RegexMultimeter(output):
    match = re.search(r"[-+]?\d\.\d+(?:[Ee][-+]\d+)", output)
    #match = re.search("[+\-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?", output)
    if match:
        return match.group(0)
    return None


def get_multi_voltage(ser_arduino, ser_Multi):
    ser_Multi.reset_input_buffer()
    ser_Multi.reset_output_buffer()
    ser_Multi.write(b':MEAS:VOLT:DC?\n')
    #print("geschrieben")
    time.sleep(0.05)
    #print("sleep 0.2 sek")
    response = ser_Multi.readline().decode('utf-8', errors='ignore').strip()
    #print("geantwortet")
    if(RegexMultimeter(response)):
        #print("check1")
        voltage = float(RegexMultimeter(response))
        #print("check2")
        print(f"Erfasste Spannung: {voltage}")
        ser_arduino.write(f"ISTV:{voltage}\n".encode())
        #print("check3")
    else:
        print("Problem bei DMM Response")
        None

def serial_ports():
    if sys.platform.startswith('win'):
        ports = list(serial.tools.list_ports.comports())
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for p in ports:
        try:
            print(p)
            
        except (OSError, serial.SerialException):
            pass
    return result

