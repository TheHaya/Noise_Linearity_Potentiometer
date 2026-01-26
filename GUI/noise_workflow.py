import time
from serial_client import open_first_available
import pico_runner
from ring import mark_ends, mark_noise_segments, set_circle_text


# --------------- NOISE VARIABLES
root = None
txt_speed = None

# --------------- CALC FUNCTIONS
def calc_duration(ges_spd):
    total_delay = delay_time1 + delay_time2 + delay_time3
    user_rpm = float(ges_spd)
    duration = 0
    circle_tick = 4096
    for i in range(1, 4, 1):
        div_spd = user_rpm/2
        duration += 2 * (60/(div_spd*i)) * (total_ticks/circle_tick)
    duration = duration + total_delay # wegen servo delay für jeden antrieb
    return duration

def calc_individual_turns(ges_spd, turn_number):
    user_rpm = float(ges_spd)
    total_duration = 0
    circle_tick = 4096
    for i in range(1, 4, 1):
        div_spd = user_rpm/2
        turn_duration = (60/(div_spd*i)) * (total_ticks/circle_tick)
        total_duration += 2 * turn_duration
        match i:
            case 1:
                time1 = total_duration + delay_time1
                turn1 = turn_duration + (delay_time1 / 2)
            case 2:
                time2 = total_duration + delay_time1 + delay_time2
                turn2 = turn_duration + (delay_time2 / 2)
            case 3:
                time3 = total_duration + delay_time1 + delay_time2 + delay_time3
                turn3 = turn_duration + (delay_time3 / 2)

    match turn_number:
        case 1: return time1
        case 2: return time2
        case 3: return time3
        case 4: return turn1
        case 5: return turn2
        case 6: return turn3

def calc_rel_angle(time_arr, turn_arr, angle_arr):
    user_rpm = float(txt_speed.get().strip().replace(',', '.'))
    time1 = calc_individual_turns(user_rpm, 1)
    time2 = calc_individual_turns(user_rpm, 2)
    time3 = calc_individual_turns(user_rpm, 3)

    turn1 = calc_individual_turns(user_rpm, 4)
    turn2 = calc_individual_turns(user_rpm, 5)
    turn3 = calc_individual_turns(user_rpm, 6)
    
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
    print(turn_arr)
    print(angle_arr)
    return 


# --------------- NOISE FUNCTIONS
def config(app_root, txt_speed_entry):
    global root, txt_speed
    root = app_root
    txt_speed = txt_speed_entry

def measurement(ges_v = None, ges_w=None, ges_s=None, pico_plot_volt=None, pico_plot_time=None, stop_event=None, on_finish=None):
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

        ser_Arduino = open_first_available(baud=115200, timeout=5)
        time.sleep(0.2)
        ser_Arduino.write(f"SETW:{ges_w}\n".encode())
        time.sleep(0.2)
        ser_Arduino.write(f"SETS:{ges_s}\n".encode())
        time.sleep(0.2)
        print("speed ist", ges_s)
        print("Sende: GO") #debug
        ser_Arduino.write(b"NOISE_GO\n")

        ser_Arduino.timeout = 0.1
        while True:
            if stop_event.is_set():
                ser_Arduino.write(b"STOP\n")
                time.sleep(0.5)
                ser_Arduino.flush()
                time.sleep(0.2)
                break

            line = ser_Arduino.readline().decode('utf-8').strip()
            #print("Empfangen:", line) #debug
            if line.startswith("TICKS"):
                global total_ticks
                total_ticks = float(line[5::])

            if line == 'NOISE_READY':
                print("Config Pico")
                pico_runner.config_pico(
                    txt_s=lambda: txt_speed.get(),
                    calc_d=calc_duration,
                    total_t=lambda: total_ticks
                )
                print("start run_pico")
                pico_runner.run_pico(ser_Arduino, pico_time, pico_volt, pico_pdf_time, pico_plot_volt, pico_plot_time)

            elif line == 'FINISH':
                finish_time = time.time()
                total_duration = finish_time - pico_runner.start_time
                print(f"FINISH empfangen, total Dauer: {total_duration}")
                calc_rel_angle(pico_time, pico_turn, pico_angle)
                mark_ends(total_ticks)
                mark_noise_segments(pico_angle)
                set_circle_text(pico_angle)
                break

            elif line == 'NOISE_FINISH':
                break
            elif line == 'CANCEL':
                break

            elif line.startswith("DELAY1"):
                global delay_time1
                delay_time1 = float(line[6::])
                print(f"{delay_time1}")
                
            elif line.startswith("DELAY2"):
                global delay_time2
                delay_time2 = float(line[6::])
                print(f"{delay_time2}")
                
            elif line.startswith("DELAY3"):
                global delay_time3
                delay_time3 = float(line[6::])
                print(f"{delay_time3}")
           
        ser_Arduino.close()

    except Exception as e:
        print("Fehler bei Serial: ", e) #debug

    if root is not None:
        root.after(0, on_finish)
    else:
        on_finish()
