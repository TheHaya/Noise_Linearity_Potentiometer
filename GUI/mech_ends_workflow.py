import time
import serial_client as sc


# --------------- MECH ENDS VARIABLES
root = None
txt_speed = None
MULTI_PORT = "COM17"
PSU_PORT = "COM15"
delay_time1 = 0.0
delay_time2 = 0.0
delay_time3 = 0.0
total_ticks = 0

# --------------- MECH ENDS FUNCTIONS

def config(app_root, txt_speed_entry, ser_arduino_app=None, ser_psu_app=None, ser_multi_app=None):
    global root, txt_speed, ser_arduino, ser_PSU, ser_Multi
    root = app_root
    txt_speed = txt_speed_entry
    ser_arduino = ser_arduino_app
    ser_PSU = ser_psu_app
    ser_Multi = ser_multi_app
    
def measurement(ges_v=None, ges_w=None, ges_s=None, stop_event=None, on_finish=None):
    try:
        #ser_arduino = sc.connect_ard()
        # ser_Multi = sc.connect_multi()
        # ser_PSU = sc.connect_psu()
        sc.set_psu_parameters(ser_PSU, 12, 0.12, 10, 0.004)
        sc.set_part_parameters(ser_arduino, ges_v, ges_w, ges_s)
        global safety_cancel
        safety_cancel = False

        print("MECH_ENDS Sende: INIT_GO")
        ser_arduino.write(b"INIT_GO\n")

        ser_arduino.timeout = 0.1
        while True:
            if stop_event.is_set():
                ser_arduino.write(b"STOP\n")
                print("STOP EMPFANGEN")
                time.sleep(0.2)
                ser_arduino.flush()
                ser_PSU.write(b"OUTP OFF\n")
                print("PSU: OUTPUT OFF")
                ser_arduino.close()
                print("SERIAL: Arduino close")
                ser_Multi.close()
                print("SERIAL: Multimeter close")
                ser_PSU.close()
                print("SERIAL: Netzteil close")
                time.sleep(0.2)
                break

            line = ser_arduino.readline().decode('utf-8').strip()
            #print("Empfangen:", line) #debug
    
            if line == 'VOLTR':
                sc.get_multi_voltage(ser_arduino, ser_Multi)
                continue

            if line.startswith("ANGLE"):
                global total_mech
                total_mech = float(line[5::])
                global total_ticks
                total_ticks = round(total_mech*(4096/360))
                print(f"Gesamtwinkel ist: {total_mech}")
            
            elif line.startswith("DELAY1"):
                global delay_time1
                delay_time1 = float(line[6::])
                print(f"Delay 0.5x: {delay_time1}")
                
            elif line.startswith("DELAY2"):
                global delay_time2
                delay_time2 = float(line[6::])
                print(f"Delay 1.0x: {delay_time2}")
                
            elif line.startswith("DELAY3"):
                global delay_time3
                delay_time3 = float(line[6::])
                print(f"Delay 1.5x: {delay_time3}")

            elif line == 'INIT_FINISH':
                print("Empfangen: INIT_FINISH")
                break

            elif line == 'SAFETY':
                print("Empfangen: SAFETY")
                safety_cancel = True
                ser_PSU.write(b"OUTP OFF\n")
                print("Schleifer zu nah an mechanischem Anschlag")
                break
            elif line == 'CANCEL':
                print("Empfangen: CANCEL")
                break

        ser_PSU.write(b"OUTP OFF\n")

        #ser_arduino.close()
        # ser_Multi.close()
        # ser_PSU.close()
    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()
