import time
import serial_client as sc


# --------------- MECH ENDS VARIABLES
root = None
txt_speed = None
delay_time1 = 0.0
delay_time2 = 0.0
delay_time3 = 0.0
total_ticks = 0
endless_noise_init = False

# --------------- MECH ENDS FUNCTIONS

def config(app_root, txt_speed_entry, ser_arduino_app=None, ser_psu_app=None, ser_multi_app=None):
    global root, txt_speed, ser_arduino, ser_PSU, ser_Multi
    root = app_root
    txt_speed = txt_speed_entry
    ser_arduino = ser_arduino_app
    ser_PSU = ser_psu_app
    ser_Multi = ser_multi_app
    
def measurement(ges_v=None, ges_w=None, ges_s=None, rel_sw=None, soll_v=None, 
                res_init_bool=None, res_final_bool=None, res_total_bool=None, stop_event=None, on_finish=None, on_progress=None):
    try:
        PSU_ovp = soll_v+soll_v*0.2
        PSU_ocp = 0.15
        PSU_current = 0.05
        sc.set_psu_parameters(ser_PSU, PSU_ovp, PSU_ocp, soll_v, PSU_current)
        sc.set_part_parameters(ser_arduino, ges_v, ges_w, ges_s, rel_sw)
        sc.set_res_parameters(ser_arduino, res_init_bool, res_final_bool, res_total_bool)
        global safety_cancel
        safety_cancel = False

        time.sleep(0.2)
        print("MECH_ENDS Sende: INIT_GO")
        sc.prepare_arduino_run(ser_arduino)
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
                time.sleep(0.2)
                break

            line = ser_arduino.readline().decode('utf-8').strip()

            if sc.handle_progress(line, "MECH", on_progress):
                continue
            if line.startswith('VOLTR_START'):
                sc.get_multi_voltage(ser_arduino, ser_Multi)
                debug_pos = float(line[11::])
                print(f"Ist_Start Position: {debug_pos} // {debug_pos*0.087890625}")
                print("_____")
                continue
            elif line.startswith('VOLTR_END'):
                sc.get_multi_voltage(ser_arduino, ser_Multi)
                debug_pos = float(line[9::])
                print(f"Ist_End Position: {debug_pos} // {debug_pos*0.087890625}")
                print("_____")
                continue
            elif line.startswith('VOLTR'):
                sc.get_multi_voltage(ser_arduino, ser_Multi)
                debug_pos = float(line[5::])
                print(f"Position für Debug: {debug_pos} // {debug_pos*0.087890625}")
                print("_____")
                continue
            elif line.startswith('RESR_INIT'):
                global res_init_val
                res_init_val = sc.get_multi_resistance(ser_arduino, ser_Multi, 1)
                print("_____")
                continue
            elif line.startswith('RESR_FINAL'):
                global res_final_val
                res_final_val = sc.get_multi_resistance(ser_arduino, ser_Multi, 2)
                print("_____")
                continue
            elif line.startswith('RESR_TOTAL'):
                global res_total_val
                res_total_val = sc.get_multi_resistance(ser_arduino, ser_Multi, 3)
                print("_____")
                continue
            elif line.startswith('RESR_INIT_SWITCHED'):
                res_init_val = sc.get_multi_resistance(ser_arduino, ser_Multi, 1)
                print("_____")
                continue
            elif line.startswith('RESR_FINAL_SWITCHED'):
                res_final_val = sc.get_multi_resistance(ser_arduino, ser_Multi, 2)
                print("_____")
                continue
            elif line.startswith('RESR_TOTAL_SWITCHED'):
                res_total_val = sc.get_multi_resistance(ser_arduino, ser_Multi, 3)
                print("_____")
                continue
            elif line.startswith("ANGLE"):
                global total_mech
                total_mech = float(line[5::])
                global total_ticks
                total_ticks = round(total_mech*(4096/360))
                print(f"Gesamtwinkel ist: {total_mech}")
            elif line.startswith("CUR0"):
                cal_cur0 = float(line[4::])
                print(f"Max. Strom RPM0: {cal_cur0}")
                
            elif line.startswith("CUR1"):
                cal_cur1 = float(line[4::])
                print(f"Max. Strom RPM1: {cal_cur1}")
                
            elif line.startswith("CUR2"):
                cal_cur2 = float(line[4::])
                print(f"Max. Strom RPM2: {cal_cur2}")

            elif line.startswith("CUR3"):
                cal_cur3 = float(line[4::])
                print(f"Max. Strom RPM3: {cal_cur3}")

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

            elif line.startswith('SAFETY_L'):
                global safety_V_low
                safety_V_low = float(line[8::])
                print("Empfangen: SAFETY_L")
                print(f"An Start-Voltage: {safety_V_low} V")

            elif line.startswith('SAFETY_H'):
                global safety_V_high
                safety_V_high = float(line[8::])
                print("Empfangen: SAFETY_H")
                print(f"An End-Voltage: {safety_V_high} V")

            elif line == 'INIT_FINISH':
                print("Empfangen: INIT_FINISH")
                if(endless_noise_init):
                    total_mech = 360
                    total_ticks = round(total_mech*(4096/360))
                    print(f"Gesamtwinkel ist: {total_mech}")
                    print("endless_noise_init is True")
                    break
                else:
                    ser_arduino.write(b"CALIB_GO\n")
                    print("MECH_ENDS Sende: CALIB_GO")
                
            elif line == 'CALIB_FINISH':
                print("Empfangen: CALIB_FINISH")
                break

            elif line == 'INIT_CHECK_FAILED':
                print("INIT Check fehlgeschlagen.")

            elif line == 'CANCEL':
                print("Empfangen: CANCEL")
                if stop_event is not None:
                    stop_event.set()
                ser_arduino.reset_input_buffer()
                break

        ser_PSU.write(b"OUTP OFF\n")

    except Exception as e:
        print("Fehler bei Serial (mech_ends): ", e) #debug
        raise

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()
