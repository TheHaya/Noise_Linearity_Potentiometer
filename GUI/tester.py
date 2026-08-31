import threading, time
from datetime import datetime
import pandas as pd
import os
import pandas as pd
import xlwings as xw
from itertools import cycle
from linear_workflow import daten
import serial_client as sc
import mech_ends_workflow

TEST_RUNS = 40
_tester_running = False

# NUR TESTER FÜR 
ALIGN_CENTER = -4108
ALIGN_LEFT = -4131
def save_to_excel2(title_txt, daten, linear_sollV, linear_lin, summary_vals, lin_max, lin_min,
                  tol_d_p, tol_d_n, tol_cw_p, tol_cw_n, tol_ccw_p, tol_ccw_n, tol_lin_p, tol_lin_n):
    try: 
        daten = []
        linear_sollV = []
        linear_lin = []

        totzone   = summary_vals.get("Totzone")
        activeCW  = summary_vals.get("AktivCW")
        activeCCW = summary_vals.get("AktivCCW")
        activeSum = summary_vals.get("AktivSumme")

        for i in range(13):
            sollwinkel = float(i)
            sollspannung = float(i)
            istspannung = float(i)
            istwinkel = float(i)
            realwinkelmitte = float(i)
            daten.append([sollwinkel, sollspannung, istspannung, istwinkel, 
                        realwinkelmitte])
            linear_sollV.append(i)
            linear_lin.append(i)
        labels = [  "Mittelposition",
            "Start aktiver Bereich CW (Drehrichtung-)",
            "50° CW (25% aktiver Bereich)(Drehrichtung-)",
            "75° CW (50% aktiver Bereich)(Drehrichtung-)",
            "100° CW (75% aktiver Bereich)(Drehrichtung-)",
            "Ende aktiver Bereich CW (Drehrichtung-)(11) 10V",
            "Mechanisches Ende CW (Drehrichtung-)",
            "Start aktiver Bereich CCW (Drehrichtung+)",
            "50° CCW (25% aktiver Bereich)(Drehrichtung+)",
            "75° CCW (50% aktiver Bereich)(Drehrichtung+)",
            "100° CCW (75% aktiver Bereich)(Drehrichtung+)",
            "Ende aktiver Bereich CCW (Drehrichtung+)(13) 0V",
            "Mechanisches Ende CCW (Drehrichtung+)"]
        labels_iter = cycle(labels)
        rows = []
        for(sollwinkel, sollspannung, istspannung, istwinkel, 
                                realwinkelmitte), label in zip(daten, labels_iter):
            rows.append({
                " ": label,
                "Soll-Winkel [°]": round(sollwinkel, 1),
                "Soll-Spannung [V]": round(sollspannung, 2),
                "Ist-Spannung [V]": round(istspannung, 3),
                "Ist-Winkel [°]": round(istwinkel, 1),
                "Realer Winkel zur\nMitte [°]": round(realwinkelmitte, 1),
                #"Soll-Spannung Real [V]": round(realsollspannung, 3),
                #"Linearität":  float(linear)
            })

        title = title_txt.get()
        file = "RMTest-"+title+".xlsx"
        sh_name = str(3)

        if os.path.exists(f"{file}.xlsx"):
            
            wb = xw.Book(f"{file}.xlsx")
            sheet = wb.sheets.add(name=sh_name,after=wb.sheets[-1])
        else:
            wb = xw.Book()
            wb.save(f"{file}.xlsx")
            sheet = wb.sheets[0]
            sheet.name = sh_name

        df = pd.DataFrame(rows)
        L = len(df)
        
        def round_sollReal(x): 
            return None if x is None else round(x, 3)

        def round_linear(x): 
            return None if x is None else float(x)

        df["Soll-Spannung Real [V]"] = [round_sollReal(v) for v in linear_sollV[:L]]
        df["Linearität"] = [round_linear(v) for v in linear_lin[:L]]
 
        sheet['A1'].options(index=False).value = df
        sheet['A1:H1'].api.WrapText = True
        sheet['A:A'].column_width = 45
        sheet['A1:H1'].row_height = 45
        sheet['B:H'].column_width = 17
        sheet['B:H'].api.HorizontalAlignment = ALIGN_CENTER
        sheet['A:H'].api.VerticalAlignment = ALIGN_CENTER
        sheet['A1:H1'].font.bold = True

        ###### Test Values
        lmin = 0.2
        lmax = 0.8
        tol_lin_p = 0.005
        tol_lin_n = -0.005
        tol_d_p = 51.5
        tol_d_n = 48.5
        tol_cw_p = 200
        tol_cw_n = 198
        tol_ccw_p = 200
        tol_ccw_n = 198

        sheet['B:B'].number_format = '0,0°'
        sheet['C:C'].number_format = '0,00'
        sheet['D:D'].number_format = '0,000'
        sheet['E:E'].number_format = '0,0°'
        sheet['F:F'].number_format = '0,0°'
        sheet['G:G'].number_format = '0,000'
        sheet['H1:H17'].number_format = '0,00%'
        
        sheet['A16'].value = "Totzone"
        sheet['B16'].value = totzone
        sheet['A17'].value = "Winkel Aktiver Bereich CW (Drehrichtung-)(11)"
        sheet['B17'].value = activeCW
        sheet['A18'].value = "Winkel Aktiver Bereich CCW (Drehrichtung+)(13)"
        sheet['B18'].value = activeCCW
        sheet['A20'].value = "Aktive Bereiche Gesamt"
        sheet['B20'].value = activeSum

        sheet['G16'].value = "Lin Max"
        sheet['H16'].value = lin_max / 100
        sheet['G17'].value = "Lin Min"
        sheet['H17'].value = lin_min / 100

        for i in range(2,18):
            if i == 15:
                continue
            if float(sheet[f'H{i}'].value) > tol_lin_p or float(sheet[f'H{i}'].value) < tol_lin_n:
                sheet[f'H{i}'].color = "#FF5454"

        if float(sheet['B16'].value) > tol_d_p or float(sheet['B16'].value) < tol_d_n:
             sheet['B16'].color = "#FF5454"

        if float(sheet['B17'].value) > tol_cw_p or float(sheet['B17'].value) < tol_cw_n:
             sheet['B17'].color = "#FF5454"

        if float(sheet['B18'].value) > tol_ccw_p or float(sheet['B18'].value) < tol_ccw_n:
             sheet['B18'].color = "#FF5454"

        wb.save(f"{file}.xlsx")
        #wb.close()

    except Exception as e:
        print("Fehler bei Linearitäts-Export: ", e)

def test_relays(ser_ard):
    ser_ard.write(b"REL_TESTER\n")

def start_mech_angle_repeat_test(ser_ard, meas_volt, meas_angle, meas_speed, relay_switch_pol, soll_volt_linear, stop_event=None, on_finish=None):
    global _tester_running

    if _tester_running:
        print("Tester läuft bereits.")
        return

    _tester_running = True

    thread = threading.Thread(
    target=_run_mech_angle_repeat_test,
    args=(ser_ard, meas_volt, meas_angle, meas_speed, relay_switch_pol, soll_volt_linear, stop_event, on_finish),
    daemon=True
)
    thread.start()
    return thread

def _run_mech_angle_repeat_test(ser_ard, meas_volt, meas_angle, meas_speed, relay_switch_pol, soll_volt_linear, stop_event=None, on_finish=None):
    global _tester_running

    rows = []
    ser_psu = None
    ser_multi = None

    file_name = "MechWinkel_100x_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".xlsx"

    if stop_event is None:
        stop_event = _DummyStopEvent()

    try:
        if ser_ard is None:
            ser_ard = sc.connect_ard()

        ser_psu = sc.connect_psu()
        ser_multi = sc.connect_multi()

        mech_ends_workflow.config(
            None,
            None,
            ser_ard,
            ser_psu,
            ser_multi
        )

        for i in range(TEST_RUNS):
            print(f"Tester Messung {i + 1}/{TEST_RUNS}")

            status = "OK"
            angle = None
            ticks = None
            delay1 = None
            delay2 = None
            delay3 = None

            try:
                mech_ends_workflow.measurement(
                    meas_volt,
                    meas_angle,
                    meas_speed,
                    relay_switch_pol,
                    soll_volt_linear,
                    stop_event,
                    lambda: None
                )

                angle = getattr(mech_ends_workflow, "total_mech", None)
                ticks = getattr(mech_ends_workflow, "total_ticks", None)
                delay1 = getattr(mech_ends_workflow, "delay_time1", None)
                delay2 = getattr(mech_ends_workflow, "delay_time2", None)
                delay3 = getattr(mech_ends_workflow, "delay_time3", None)

            except Exception as e:
                status = f"Fehler: {e}"
                print(status)

            rows.append({
                "Lauf": i + 1,
                "Zeit": datetime.now().strftime("%H:%M:%S"),
                "Mechanischer Winkel [deg]": angle,
                "Ticks": ticks,
                "Delay 0.5x [s]": delay1,
                "Delay 1.0x [s]": delay2,
                "Delay 1.5x [s]": delay3,
                "Status": status,
            })

            _save_mech_angle_excel(file_name, rows)

    finally:
        try:
            if ser_psu is not None:
                ser_psu.write(b"OUTP OFF\n")
                ser_psu.close()
        except Exception:
            pass

        try:
            if ser_multi is not None:
                ser_multi.close()
        except Exception:
            pass

        _tester_running = False
        print("Tester fertig.")
        if on_finish is not None:
            on_finish()

class _DummyStopEvent:
    def is_set(self):
        return False

    def set(self):
        pass


def _save_mech_angle_excel(file_name, rows):
    df = pd.DataFrame(rows)

    angles = pd.to_numeric(df["Mechanischer Winkel [deg]"], errors="coerce")

    stats = pd.DataFrame([
        {"Wert": "Anzahl", "Ergebnis": angles.count()},
        {"Wert": "Mittelwert", "Ergebnis": angles.mean()},
        {"Wert": "Minimum", "Ergebnis": angles.min()},
        {"Wert": "Maximum", "Ergebnis": angles.max()},
        {"Wert": "Spannweite", "Ergebnis": angles.max() - angles.min()},
        {"Wert": "Standardabweichung", "Ergebnis": angles.std()},
    ])

    with pd.ExcelWriter(file_name, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Messwerte", index=False)

        start_row = len(df) + 3
        stats.to_excel(
            writer,
            sheet_name="Messwerte",
            startrow=start_row,
            index=False
        )