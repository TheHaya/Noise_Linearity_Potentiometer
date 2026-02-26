import time
import serial_client as sc

# --------------- ELEC DEG VARIABLES
root = None
MULTI_PORT = "COM17"
PSU_PORT = "COM15"


# --------------- ELEC DEG FUNCTIONS


def config(app_root, txt_speed_entry, ser_arduino_app=None):
    global root, txt_speed, ser_arduino
    root = app_root
    txt_speed = txt_speed_entry
    #ser_arduino = ser_arduino_app

def measurement(ges_v=None, ges_w=None, ges_s=None, d12=None, 
                d21=None, d22=None, d31=None, stop_event=None, on_finish=None):
    try:
        ser_arduino = sc.connect_ard()
        ser_Multi = sc.connect_multi()
        ser_PSU = sc.connect_psu()
        sc.set_psu_parameters(ser_PSU, 12, 0.12, 10, 0.004)
        sc.set_part_parameters(ser_arduino, ges_v, ges_w, ges_s)

        ser_arduino.write(f"dead12:{d12}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead21:{d21}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead22:{d22}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead31:{d31}\n".encode())
        time.sleep(0.2)
        print("ELEC_DEG Sende: GO") #debug
        #print(d11, d12, d21, d22, d31, d32)
        ser_arduino.write(b"ELEC_DEG_GO\n")

        ser_arduino.timeout = 0.1
        while True:
            if stop_event.is_set():
                ser_arduino.write(b"STOP\n")
                time.sleep(0.2)
                ser_arduino.flush()
                ser_PSU.write(b"OUTP OFF\n")
                ser_arduino.close()
                ser_Multi.close()
                ser_PSU.close()
                time.sleep(0.2)
                break

            line = ser_arduino.readline().decode('utf-8').strip()
            #print("Empfangen:", line) #debug
            if line == 'VOLTR':
                sc.get_multi_voltage(ser_arduino, ser_Multi)
                continue
            elif line == 'ELEC_DEG_READY':
                print("ELEC_DEG READY empfangen")
                ser_arduino.write(b"ELEC_DEG_START\n")
                print("Sende: ELEC_DEG START")
            elif line.startswith('TOTAL_ELEC'):
                global total_elec
                total_elec = float(line[10::])
                print("Gesamt Elektr. Winkel:")
                print(total_elec)

            elif line == 'ELEC_DEG_FINISH':
                break
            elif line == 'CANCEL':
                break
            
        ser_PSU.write(b"OUTP OFF\n")
        ser_arduino.close()
        ser_Multi.close()
        ser_PSU.close()
                        
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()