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