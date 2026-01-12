
# --------------- PICOSCOPE VARIABLES
picoEXE = r"C:\Users\wonga\Documents\PlatformIO\Projects\BA_Servo_Noise\Pico_Demo/pico_demo.exe"
delay_compensation = 0.15   # damit Pico und Servo position synchron sind ohne Blockierung



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


def run_pico(ser_Ard, time_arr, volt_arr, pdf_time_arr, plot_volt_arr, plot_arr):
    global start_time
    out_volt = False
    out_found = False
    plot_volt = False
    plot_time = False
    txt_geschw = float(txt_speed.get().strip().replace(',', '.'))
    pico_time = calc_duration(txt_geschw)
    print(f"Dauer ca. {pico_time}")
    print(f"Winkellänge {total_ticks*(360/4096)}")
    pico_timeStr = str(pico_time+delay_compensation)
    p = subprocess.Popen(
        [picoEXE, f"--time={pico_timeStr}"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    for line in p.stdout:
        line = line.strip()
        print(line)

        if line.startswith("PICO_START"):
            print("Sende: PICO_START") #debug
            ser_Ard.write(b"START\n")
            ser_Ard.flush()
            
            start_time = time.time()
            print("NACH: PICO_START")
        
        if out_volt is True:
            volt_arr.append(float(line))

        if line.startswith("OUTPUV"):
            out_volt = True
            out_found = False

        if out_found is True:
            time_arr.append(float(line)-delay_compensation)
            pdf_time_arr.append(float(line))

        if line.startswith("OUTPUT"):
            out_found = True
            plot_volt = False

        if plot_volt is True:
            plot_volt_arr.append(float(line))

        if line.startswith("PLOT_VOLT"):
            plot_volt = True 
            plot_time = False

        if plot_time is True:
            plot_arr.append(float(line))

        if line.startswith("PLOT_TIME"):
            plot_time = True

    end_time = time.time()
    print("Time Array:")
    print(time_arr)
    #print("Volt Array:")
    #print(plot_volt_arr)
    #print("Plot Array:")
    #print(plot_arr)
    finish_time = end_time - start_time
    print(f"Gemessene Zeit: {finish_time}")
    p.terminate()
