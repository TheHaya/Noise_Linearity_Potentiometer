import matplotlib.pyplot as plt
import numpy as np


# --------------- PDF EXPORT FUNCTIONS
def save_to_pdf(txt, pico_plot_time, pico_pdf_time, pico_plot_volt, pico_volt):
    pdf_time = np.concatenate([pico_plot_time, pico_pdf_time])
    pdf_volt = np.concatenate([pico_plot_volt + pico_volt])
    i = np.argsort(pdf_time)
    pdf_time = pdf_time[i]
    pdf_volt = pdf_volt[i]

    fig = plt.figure(figsize=(11, 6.5), dpi=550)  # Größe beliebig anpassen
    plt.plot(pdf_time, pdf_volt, linewidth=0.1)
    plt.title(("Rauschkurve "+ txt.get()))
    plt.xlabel("Zeit")
    plt.ylabel("Spannung")
    plt.grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
    plt.tight_layout()
    fig.savefig((txt.get()+".pdf"), format="pdf")  # Vektor-PDF
    plt.close(fig)


def save_to_excel():
    if not stop_event.is_set():
            rows = []
            for(sollwinkel, sollspannung, istspannung, istwinkel, 
                                  realwinkelmitte), label in zip(daten, labels_iter):
                rows.append({
                    " ": label,
                    "Soll-Winkel [°]": round(sollwinkel, 1),
                    "Soll-Spannung [V]": round(sollspannung, 2),
                    "Ist-Spannung [V]": round(istspannung, 3),
                    "Ist-Winkel [°]": round(istwinkel, 1),
                    "Realer Winkel zur Mitte [°]": round(realwinkelmitte, 1),
                    #"Soll-Spannung Real [V]": round(realsollspannung, 3),
                    #"Linearität":  float(linear)
                })
            df = pd.DataFrame(rows)
            
            L = len(df)  # zur Sicherheit auf gleiche Länge bringen

            def round_sollReal(x): 
                return None if x is None else round(x, 3)

            def round_linear(x): 
                return None if x is None else float(x)

            df["Soll-Spannung Real [V]"] = [round_sollReal(v) for v in linear_sollV[:L]]
            df["Linearität"] = [round_linear(v) for v in linear_lin[:L]]

            with pd.ExcelWriter("RMTest-"+txt9.get()+".xlsx", engine="xlsxwriter") as writer:
                sheet = "Messung"
                df.to_excel(writer, index=False, sheet_name=sheet)
                wb = writer.book
                ws = writer.sheets[sheet]

                format_percent = wb.add_format({'num_format': '0.00%','align': 'center'})
                format_degree = wb.add_format({'num_format': '0.0°','align': 'center'})
                format_volt2 = wb.add_format({'num_format': '0.00','align': 'center'})
                format_volt3 = wb.add_format({'num_format': '0.000','align': 'center'})
                format_header = wb.add_format({'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'bold': True})
                format_error_percent = wb.add_format({'num_format': '0.00%', 'align': 'center', 'bg_color': "#F86A5A"})

                ws.set_row(0, 35, format_header)
                ws.set_column('A:A', 44)
                ws.set_column('B:B', 20, format_degree)
                ws.set_column('C:C', 20, format_volt2)
                ws.set_column('D:D', 20, format_volt3)
                ws.set_column('E:E', 20, format_degree)
                ws.set_column('F:F', 20, format_degree)
                ws.set_column('G:G', 20, format_volt3)
                ws.set_column('H:H', 20, format_percent)

                ws.freeze_panes(1,0)

                start = len(df) + 2  # 1 für Header + 1 Leerzeile

                # Fallbacks, falls nichts kam
                totzone   = summary_vals.get("Totzone")
                activeCW  = summary_vals.get("AktivCW")
                activeCCW = summary_vals.get("AktivCCW")
                activeSum = summary_vals.get("AktivSumme")

                ws.write(start + 0, 0, "Totzone")
                if totzone is not None:
                    ws.write_number(start + 0, 1, totzone, format_degree)

                ws.write(start + 1, 0, "Winkel Aktiver Bereich CW (Drehrichtung-)(11)")
                if activeCW is not None:
                    ws.write_number(start + 1, 1, activeCW, format_degree)

                ws.write(start + 2, 0, "Winkel Aktiver Bereich CCW (Drehrichtung+)(13)")
                if activeCCW is not None:
                    ws.write_number(start + 2, 1, activeCCW, format_degree)

                ws.write_blank(start + 3, 0, None)
                ws.write_blank(start + 3, 1, None)

                ws.write(start + 4, 0, "Aktive Bereiche Gesamt")
                if activeSum is not None:
                    ws.write_number(start + 4, 1, activeSum, format_degree)

                ws.write(start + 0, 6, "Lin Max")
                if lin_max is not None:
                    if error_lin_idx:
                        ws.write_number(start + 0, 7, lin_max, format_error_percent)
                    else:
                        ws.write_number(start + 0, 7, lin_max, format_percent)

                ws.write(start + 1, 6, "Lin Min")
                if lin_min is not None:
                    if error_lin_idx:
                        ws.write_number(start + 1, 7, lin_min, format_error_percent)
                    else:
                        ws.write_number(start + 1, 7, lin_min, format_percent)