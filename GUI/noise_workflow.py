import time
import serial_client as sc
import pico_runner
from ring import mark_ends, mark_noise_segments, set_circle_text
import mech_ends_workflow as mech

# --------------- NOISE VARIABLES
root = None
txt_speed = None


# --------------- CALC FUNCTIONS
def calc_duration(ges_spd, ges_deg):
    total_delay = (mech.delay_time1 + mech.delay_time2 + mech.delay_time3) * 2
    user_rpm = float(ges_spd)
    duration = 0
    circle_tick = 4096
    for i in range(1, 4, 1):
        div_spd = user_rpm/2
        if ges_deg == 0:
            duration += 2 * (60/(div_spd*i))
        else:
            duration += 2 * (60/(div_spd*i)) * (mech.total_ticks/circle_tick)
       
    duration = (duration + total_delay) * 2  # wegen servo delay für jeden antrieb // *2 wegen 2 rounds pro geschwindigkeit
    return duration

def calc_individual_turns(ges_spd, turn_number, ges_deg):
    user_rpm = float(ges_spd)
    total_duration = 0
    turn_duration = 0
    circle_tick = 4096
    for i in range(1, 4, 1):
        div_spd = user_rpm/2
        if ges_deg == 0:
            turn_duration += 2 * (60/(div_spd*i))
        else:
            turn_duration += 2 * (60/(div_spd*i)) * (mech.total_ticks/circle_tick)
        total_duration += 4 * turn_duration
        # match i:
        #     case 1:
        #         time1 = total_duration + mech.delay_time1
        #         turn1 = turn_duration + (mech.delay_time1 / 2)
        #     case 2:
        #         time2 = total_duration + mech.delay_time1 + mech.delay_time2
        #         turn2 = turn_duration + (mech.delay_time2 / 2)
        #     case 3:
        #         time3 = total_duration + mech.delay_time1 + mech.delay_time2 + mech.delay_time3
        #         turn3 = turn_duration + (mech.delay_time3 / 2)
        match i:
            case 1:
                time1 = total_duration + mech.delay_time1
                turn1 = turn_duration + (mech.delay_time1 / 2)
            case 2:
                time2 = total_duration + mech.delay_time1 + mech.delay_time2
                turn2 = turn_duration + (mech.delay_time2 / 2)
            case 3:
                time3 = total_duration + mech.delay_time1 + mech.delay_time2 + mech.delay_time3
                turn3 = turn_duration + (mech.delay_time3 / 2)

    match turn_number:
        case 1: return time1
        case 2: return time2
        case 3: return time3
        case 4: return turn1
        case 5: return turn2
        case 6: return turn3

def calc_rel_angle(time_arr, turn_arr, angle_arr, ges_deg):
    user_rpm = float(txt_speed.get().strip().replace(',', '.'))
    time1 = calc_individual_turns(user_rpm, 1, ges_deg)
    time2 = calc_individual_turns(user_rpm, 2, ges_deg)
    time3 = calc_individual_turns(user_rpm, 3, ges_deg)

    turn1 = calc_individual_turns(user_rpm, 4, ges_deg)
    turn2 = calc_individual_turns(user_rpm, 5, ges_deg)
    turn3 = calc_individual_turns(user_rpm, 6, ges_deg)
    
    if not time_arr:
        return 
    
    # Wenn Zeit evtl. schöner machen?
    for i in range(len(time_arr)):
        if time_arr[i] < turn1:
            turn_arr.append(1)
            angle_arr.append((time_arr[i])/(turn1)*360)
        elif time_arr[i] < time1:
            turn_arr.append(2)
            angle_arr.append(360-((time_arr[i]-turn1)/(turn1)*360))
        elif time_arr[i] < time2-turn2:
            turn_arr.append(3)
            angle_arr.append((time_arr[i]-time1)/(turn2)*360)
        elif time_arr[i] < time2:
            turn_arr.append(4)
            angle_arr.append(360-((time_arr[i]-time1-turn2)/(turn2)*360))
        elif time_arr[i] < time3-turn3:
            turn_arr.append(5)
            angle_arr.append((time_arr[i]-time2)/(turn3)*360)
        elif time_arr[i] < time3:
            turn_arr.append(6)
            angle_arr.append(360-((time_arr[i]-time2-turn3)/(turn3)*360))

    print(turn1)
    print(time1)
    print(time2-turn2)
    print(time2)
    print(time3-turn3)
    print(time3)
    # print(turn_arr)
    # print(angle_arr)
    return 


# --------------- NOISE FUNCTIONS
def config(app_root, txt_speed_entry, ser_arduino_app=None, ser_psu_app=None, ser_multi_app=None):
    global root, txt_speed, ser_arduino, ser_PSU, ser_Multi
    root = app_root
    txt_speed = txt_speed_entry
    ser_arduino = ser_arduino_app
    ser_PSU = ser_psu_app
    ser_Multi = ser_multi_app

def measurement(ges_v = None, ges_w=None, ges_s=None, rel_sw = None, soll_v=None, 
                pico_plot_volt=None, pico_plot_time=None, stop_event=None, on_finish=None):
    try:
        global pico_pdf_time
        pico_pdf_time = []
        global pico_time
        pico_time = []
        pico_turn = []
        global pico_angle
        pico_angle = []
        global pico_volt
        pico_volt = []
        global noise_found
        noise_found = False
        
        PSU_ovp = soll_v+soll_v*0.2
        PSU_ocp = 0.15
        PSU_current = 0.05
        #ser_arduino = sc.connect_ard()
        # ser_PSU = sc.connect_psu()
        sc.set_psu_parameters(ser_PSU, PSU_ovp, PSU_ocp, soll_v, PSU_current) # für dp37
        # sc.set_psu_parameters(ser_PSU, 2.5, 0.12, 2, 0.008) # für t18
        sc.set_part_parameters(ser_arduino, ges_v, ges_w, ges_s, rel_sw)
        # ser_arduino.reset_input_buffer()
        # ser_arduino.reset_output_buffer()
        sc.prepare_arduino_run(ser_arduino)
        ser_arduino.write(b"NOISE_GO\n")
        print("NOISE Sende: GO")

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

            if line == 'NOISE_READY':
                print("Empfangen: NOISE_READY")
                print("Config Pico")
                if ges_w == 0:
                    pico_runner.config_pico(
                    txt_s=lambda: txt_speed.get(),
                    calc_d=lambda speed: calc_duration(speed, ges_w),
                    total_t=lambda: 4096
                )
                else:
                    pico_runner.config_pico(
                        txt_s=lambda: txt_speed.get(),
                        calc_d=lambda speed: calc_duration(speed, ges_w),
                        total_t=lambda: mech.total_ticks
                    )
                print("Run_Pico starten")
                pico_runner.run_pico(ser_arduino, pico_time, pico_volt, pico_pdf_time, pico_plot_volt, pico_plot_time, stop_event)

            elif line == 'NOISE_MOVE_FINISH':
                finish_time = time.time()
                total_duration = finish_time - pico_runner.start_time
                print(f"Empfangen: NOISE_MOVE_FINISH, total Dauer: {total_duration}")
                calc_rel_angle(pico_time, pico_turn, pico_angle, ges_w)
                if ges_w == 0:
                    mark_ends(4096)
                else:
                    mark_ends(mech.total_ticks)
                mark_noise_segments(pico_angle)
                
            elif line == 'NOISE_FINISH':
                print("Empfangen: NOISE_FINISH")
                break

            elif line == 'CANCEL':
                print("Empfangen: CANCEL")
                if stop_event is not None:
                    stop_event.set()
                ser_arduino.reset_input_buffer()
                break
        
        time.sleep(1)
        ser_PSU.write(b"OUTP OFF\n")
        #ser_arduino.close()
        #ser_PSU.close()

    except Exception as e:
        print("Fehler bei Serial (noise): ", e) #debug

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()
