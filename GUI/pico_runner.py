import time, subprocess, sys, os

# --------------- PYINSTALLER
def resource_path(rel_path: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel_path)

picoEXE = resource_path("pico_demo.exe")

# --------------- PICOSCOPE VARIABLES
delay_compensation = 0.15   # damit Pico und Servo position synchron sind ohne Blockierung
# start_time = 0.0
start_time = None

txt_speed_getter = None
calc_duration_f = None
total_ticks_getter = None
out_volt = False
noise_error = False
active_process = None

# --------------- PICO FUNCTIONS
def config_pico(txt_s, calc_d, total_t):
    global txt_speed_getter, calc_duration_f, total_ticks_getter
    txt_speed_getter = txt_s
    calc_duration_f = calc_d
    total_ticks_getter = total_t


def stop_active_run():
    global active_process
    if active_process is None:
        return
    try:
        active_process.kill()
        active_process.wait(timeout=2)
    except Exception:
        pass
    finally:
        active_process = None

def run_pico(ser_Ard, time_arr, volt_arr, pdf_time_arr, plot_volt_arr, plot_arr, stop_event=None):
    global start_time, picoEXE, delay_compensation, out_volt, active_process, noise_error

    out_volt = False
    out_found = False
    plot_volt = False
    plot_time = False
    pico_started = False

    txt_geschw = float(txt_speed_getter().strip().replace(',', '.'))
    pico_time = calc_duration_f(txt_geschw)
    print(f"Pico Dauer ca. {pico_time}")
    print(f"Winkellänge: {total_ticks_getter()*(360/4096)}")
    pico_timeStr = str(pico_time+delay_compensation)
    p = subprocess.Popen(
        [picoEXE, f"--time={pico_timeStr}"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    active_process = p
    try:
        for line in p.stdout:
            if stop_event.is_set():
                    ser_Ard.write(b"STOP\n")
                    time.sleep(0.5)
                    ser_Ard.flush()
                    time.sleep(0.2)
                    break
            
            line = line.strip()
            # print(f"[PICO RAW] {line!r}")

            if line.startswith("PICO_START") and not pico_started:
                pico_started = True
                print("Sende: PICO_START") #debug
                ser_Ard.write(b"NOISE_START\n")
                ser_Ard.flush()
                
                # start_time = time.time()
                start_time = time.monotonic()
                print("NACH: PICO_START")
            
            if out_volt is True:
                noise_error = True
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

        if not pico_started and not stop_event.is_set():
            raise RuntimeError(
                f"pico_demo ohne PICO_START beendet, Returncode: {p.returncode}"
            )
    finally:
        if start_time is None:
            print("Pico-Messung wurde nicht gestartet")
        else:
            print(
                "Gemessene Zeit:",
                time.monotonic() - start_time
            )
        # end_time = time.time()
        print("Time Array:")
        print(time_arr)
        print("Volt Array:")
        print(volt_arr)
        # finish_time = end_time - start_time
        # print(f"Gemessene Zeit: {finish_time}")
        
        stop_active_run()
