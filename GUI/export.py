from itertools import cycle
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xlsxwriter
import xlwings as xw

# --------------- EXCEL EXPORT VARIABLES
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


# --------------- PDF EXPORT FUNCTIONS
def save_to_pdf(txt, pico_plot_time, pico_pdf_time, pico_plot_volt, pico_volt, rework_nr=None):
    try:
        pdf_time = np.concatenate([pico_plot_time, pico_pdf_time])
        pdf_volt = np.concatenate([pico_plot_volt, pico_volt])
        i = np.argsort(pdf_time, kind="stable")
        pdf_time = pdf_time[i]
        pdf_volt = pdf_volt[i]

        title = txt.get().strip()
        if title == "":
            title = "-"

        file = "Rauschkurve-RMTest-" + title

        fig = plt.figure(figsize=(11, 6.5), dpi=550)
        plt.plot(pdf_time, pdf_volt, linewidth=0.1)
        if len(pico_pdf_time) == len(pico_volt) and len(pico_pdf_time) > 0:
            plt.scatter(
                pico_pdf_time,
                pico_volt,
                color="red",
                marker="o",
                s=4,
                zorder=5,

            )

        plt.title(("Rauschkurve "+ file))
        plt.xlabel("Zeit")
        plt.ylabel("Spannung")
        plt.grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
        plt.tight_layout()
        dupe = 0
        rework_dupe = 0
        if os.path.exists('{}.pdf'.format(file)) and rework_nr is not None:
            rework_dupe += 1
            while os.path.exists('{} ({:d}).pdf'.format(file, rework_dupe)):
                fig.savefig('{} ({:d}).pdf'.format(file, rework_dupe))
        elif os.path.exists('{}.pdf'.format(file)):
            dupe += 1
            while os.path.exists('{} ({:d}).pdf'.format(file, dupe)):
                dupe += 1
            fig.savefig('{} ({:d}).pdf'.format(file, dupe))
        else:
            fig.savefig('{}.pdf'.format(file))
            
        plt.close(fig)
        print(f"{file}.pdf gespeichert.")

    except Exception as e:
        print("Fehler bei Rauschkurve-Export: ", e)

def _find_next_normal_sheet_name(sheets):
    max_sheet_nr = 0
    for sheet in sheets:
        name = str(sheet.name).strip()
        if name.isdigit():
            max_sheet_nr = max(max_sheet_nr, int(name))
    return str(max_sheet_nr + 1)


def _find_next_rework_sheet_name(sheets, base_sheet_nr):
    prefix = f"{base_sheet_nr}-"
    max_suffix = 0

    for sheet in sheets:
        name = str(sheet.name).strip()
        if not name.startswith(prefix):
            continue

        suffix = name[len(prefix):]
        if suffix.isdigit():
            max_suffix = max(max_suffix, int(suffix))

    return f"{base_sheet_nr}-{max_suffix + 1}"


def _sheet_exists(sheets, sheet_name):
    target = str(sheet_name).strip()
    return any(str(sheet.name).strip() == target for sheet in sheets)

# --------------- EXCEL EXPORT FUNCTIONS
def save_to_excel2(title_txt, daten, linear_sollV, linear_lin, summary_vals, lin_max, lin_min,
                  tol_d_p, tol_d_n, tol_pos_d_cw_p, tol_pos_d_cw_n, tol_pos_d_ccw_p, tol_pos_d_ccw_n, tol_cw_p, tol_cw_n, 
                  tol_ccw_p, tol_ccw_n, tol_lin_p, tol_lin_n, rework_nr=None):
    ALIGN_CENTER = -4108
    ALIGN_LEFT = -4131
    
    try: 
        totzone   = summary_vals.get("Totzone")
        activeCW  = summary_vals.get("AktivCW")
        activeCCW = summary_vals.get("AktivCCW")
        activeSum = summary_vals.get("AktivSumme")

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
                "Soll-Winkel [°]": round(sollwinkel, 4),
                "Soll-Spannung [V]": round(sollspannung, 8),
                "Ist-Spannung [V]": round(istspannung, 8),
                "Ist-Winkel [°]": round(istwinkel, 4),
                "Realer Winkel zur\nMitte [°]": round(realwinkelmitte, 4),
            })

        title = title_txt.get().strip()
        if title == "":
            title = "-"

        file = "RMTest-" + title + ".xlsx"

        if os.path.exists(file):
            wb = xw.Book(file)
            wb.app.display_alerts = False
            wb.app.screen_updating = True

            if rework_nr is not None:
                if rework_nr < 1:
                    print("Fehler bei Linearitäts-Export: Ungültige Nacharbeits-Tabellennummer.")
                    return

                if not _sheet_exists(wb.sheets, str(rework_nr)):
                    print(f"Fehler bei Linearitäts-Export: Tabelle {rework_nr} existiert nicht.")
                    return

                sh_name = _find_next_rework_sheet_name(wb.sheets, rework_nr)
            else:
                sh_name = _find_next_normal_sheet_name(wb.sheets)

            sheet = wb.sheets.add(name=sh_name, after=wb.sheets[-1])
            print("Excel Sheet gespeichert: ", sh_name)
        else:
            if rework_nr is not None:
                print(f"Fehler bei Linearitäts-Export: Datei {file} für Nacharbeit nicht gefunden.")
                return

            wb = xw.Book()
            wb.app.display_alerts = False
            wb.app.screen_updating = False
            wb.save(file)
            sheet = wb.sheets[0]
            sh_name = "1"
            sheet.name = sh_name

        df = pd.DataFrame(rows)
        L = len(df)
        
        def round_sollReal(x): 
            return None if x is None else round(x, 8)

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


        # TEMPORÄR
        sheet['B:B'].number_format = '0,000°'
        sheet['C:C'].number_format = '0,00000000'
        sheet['D:D'].number_format = '0,00000000'
        sheet['E:E'].number_format = '0,000°'
        sheet['F:F'].number_format = '0,000°'
        sheet['G:G'].number_format = '0,00000000'
        sheet['H1:H17'].number_format = '0,0000000%'
        
        sheet['A16'].value = "Totzone"
        sheet['B16'].value = totzone
        sheet['A17'].value = "Winkel Aktiver Bereich CW (Drehrichtung-)(11)"
        sheet['B17'].value = activeCW
        sheet['A18'].value = "Winkel Aktiver Bereich CCW (Drehrichtung+)(13)"
        sheet['B18'].value = activeCCW
        sheet['A20'].value = "Aktive Bereiche Gesamt"
        sheet['B20'].value = activeSum

        sheet['G16'].value = "Lin Max"
        sheet['H16'].value = lin_max 
        sheet['G17'].value = "Lin Min"
        sheet['H17'].value = lin_min

        for i in range(2,18):
            if sheet[f'H{i}'].value is None:
                continue
            if float(sheet[f'H{i}'].value) > tol_lin_p or float(sheet[f'H{i}'].value) < tol_lin_n:
                sheet[f'H{i}'].color = "#FF5454"
        
        if float(sheet['E3'].value) > tol_pos_d_cw_p or float(sheet['E3'].value) < tol_pos_d_cw_n:
            sheet['E3'].color = "#FF5454"
        else:
            sheet['E3'].color = "#5AFF54"

        if float(sheet['E9'].value) > tol_pos_d_ccw_p or float(sheet['E9'].value) < tol_pos_d_ccw_n:
            sheet['E9'].color = "#FF5454"
        else:
            sheet['E9'].color = "#5AFF54"

        if float(sheet['B16'].value) > tol_d_p or float(sheet['B16'].value) < tol_d_n:
            sheet['B16'].color = "#FF5454"

        if float(sheet['B17'].value) > tol_cw_p or float(sheet['B17'].value) < tol_cw_n:
            sheet['B17'].color = "#FF5454"

        if float(sheet['B18'].value) > tol_ccw_p or float(sheet['B18'].value) < tol_ccw_n:
            sheet['B18'].color = "#FF5454"

        wb.save(file)
        #wb.close()

    except Exception as e:
        print("Fehler bei Linearitäts-Export: ", e)

