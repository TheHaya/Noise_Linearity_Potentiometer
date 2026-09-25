import time
import serial_client as sc

# --------------- ELEC DEG VARIABLES
root = None


# --------------- ELEC DEG FUNCTIONS

def config(app_root, txt_speed_entry, ser_arduino_app=None, ser_psu_app=None, ser_multi_app=None):
    global root, txt_speed, ser_arduino, ser_PSU, ser_Multi
    root = app_root
    txt_speed = txt_speed_entry
    ser_arduino = ser_arduino_app
    ser_PSU = ser_psu_app
    ser_Multi = ser_multi_app

def measurement(ges_v=None, ges_w=None, ges_s=None, rel_sw = None, soll_v=None, d12=None, 
                d21=None, d22=None, d31=None, stop_event=None, on_finish=None, on_progress=None):
    try:
        PSU_ovp = soll_v+soll_v*0.2
        PSU_ocp = 0.15                 
        PSU_current = 0.05

        sc.set_psu_parameters(ser_PSU, PSU_ovp, PSU_ocp, soll_v, PSU_current)
        # sc.set_part_parameters(ser_arduino, ges_v, ges_w, ges_s, rel_sw)

        ser_arduino.write(f"dead12:{d12}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead21:{d21}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead22:{d22}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"dead31:{d31}\n".encode())
        time.sleep(0.2)
        ser_arduino.write(f"rel_sw:{rel_sw}\n".encode())
        time.sleep(0.2)
        print(f"Deadzones: {d12}, {d21}, {d22}, {d31}")
        print("ELEC_DEG Sende: GO") #debug

        sc.prepare_arduino_run(ser_arduino)
        ser_arduino.write(b"ELEC_DEG_GO\n")

        ser_arduino.timeout = 0.1
        while True:
            if stop_event.is_set():
                ser_arduino.write(b"STOP\n")
                print("STOP EMPFANGEN")
                time.sleep(0.2)
                ser_arduino.flush()
                ser_PSU.write(b"OUTP OFF\n")
                print("PSU: OUTPUT OFF")
                time.sleep(0.2)
                break

            line = ser_arduino.readline().decode('utf-8').strip()
            #print("Empfangen:", line) #debug
            if sc.handle_progress(line, "ELEC", on_progress):
                continue
            if line.startswith('VOLTR'):
                sc.get_multi_voltage(ser_arduino, ser_Multi)
                debug_pos = float(line[5::])
                print(f"Position für Debug: {debug_pos} // {debug_pos*0.087890625}")
                print("_____")
                continue
            elif line == 'ELEC_DEG_READY':
                print("Empfangen: ELEC_DEG READY")
                ser_arduino.write(b"ELEC_DEG_START\n")
                print("Sende: ELEC_DEG START")
            elif line.startswith('TOTAL_ELEC'):
                print("Empfangen: TOTAL_ELEC")
                global total_elec
                total_elec = float(line[10::])
                print("Gesamt Elektr. Winkel:")
                print(total_elec)
            elif line == 'ELEC_DEG_FINISH':
                print("Empfangen: ELEC_DEG_FINISH")
                break
            elif line == 'CANCEL':
                print("Empfangen: CANCEL")
                if stop_event is not None:
                    stop_event.set()
                ser_arduino.reset_input_buffer()
                break
            
        ser_PSU.write(b"OUTP OFF\n")
                        
    except Exception as e:
        print("Fehler bei Serial (elec_deg): ", e) #debug

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()