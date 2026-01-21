import pyvisa
import sys
import time
import csv
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox

from src import signal_utils
from src.param import TxParams
from src.pluto_tx_interface import PlutoTxInterface


STABILIZATION_DELAY = 0.1  # s
SPAN = 2e6
RBW = 25e3


def open_ms2840a():
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource("TCPIP0::Anritsu-MS2840A::inst0::INSTR")
    inst.timeout = 5000
    inst.write("SYST:LANG SCPI")
    print(inst.query("*IDN?"))
    return inst


def measure_peak(inst, f_center, span, rbw):
    inst.write(f"SENSE:FREQUENCY:CENTER {f_center}")
    inst.write(f"SENSE:FREQUENCY:SPAN {span}")
    inst.write(f"SENSE:BANDWIDTH:RESOLUTION {rbw}")
    inst.write("INIT:CONT OFF")
    inst.write("INIT:IMM")
    inst.query("*OPC?")
    inst.write("CALC:MARK1:STATE ON")
    inst.write("CALC:MARK1:MAX")
    p = float(inst.query("CALC:MARK1:Y?"))
    f_peak = float(inst.query("CALC:MARK1:X?"))
    print(f"Peak at {f_peak/1e6:.3f} MHz: {p:.2f} dBm")
    return p


class CalibrationApp:
    """
    Simple GUI wrapper to configure and run the TX power calibration sweep.
    The GUI gathers user inputs, then calls the measurement routine.
    """

    def __init__(self, master):
        self.master = master
        master.title("Pluto TX Calibration Tool")

        # Main frame
        main_frame = ttk.Frame(master, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid
        for i in range(6):
            main_frame.rowconfigure(i, weight=0)
        for j in range(2):
            main_frame.columnconfigure(j, weight=1)

        # Filename
        ttk.Label(main_frame, text="Output CSV filename:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.filename_var = tk.StringVar(value="pluto_characterization.csv")
        ttk.Entry(main_frame, textvariable=self.filename_var, width=30).grid(row=0, column=1, sticky="w", padx=5, pady=2)

        # Frequency range (MHz)
        ttk.Label(main_frame, text="Start frequency (MHz):").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.f_start_var = tk.StringVar(value="400")
        ttk.Entry(main_frame, textvariable=self.f_start_var, width=10).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(main_frame, text="End frequency (MHz):").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.f_end_var = tk.StringVar(value="3400")
        ttk.Entry(main_frame, textvariable=self.f_end_var, width=10).grid(row=2, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(main_frame, text="Frequency step (MHz):").grid(row=3, column=0, sticky="e", padx=5, pady=2)
        self.f_step_var = tk.StringVar(value="100")
        ttk.Entry(main_frame, textvariable=self.f_step_var, width=10).grid(row=3, column=1, sticky="w", padx=5, pady=2)

        # Power range (dBm)
        ttk.Label(main_frame, text="Start power (dBm):").grid(row=4, column=0, sticky="e", padx=5, pady=2)
        self.p_start_var = tk.StringVar(value="-30")
        ttk.Entry(main_frame, textvariable=self.p_start_var, width=10).grid(row=4, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(main_frame, text="End power (dBm):").grid(row=5, column=0, sticky="e", padx=5, pady=2)
        self.p_end_var = tk.StringVar(value="0")
        ttk.Entry(main_frame, textvariable=self.p_end_var, width=10).grid(row=5, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(main_frame, text="Power step (dB):").grid(row=6, column=0, sticky="e", padx=5, pady=2)
        self.p_step_var = tk.StringVar(value="1")
        ttk.Entry(main_frame, textvariable=self.p_step_var, width=10).grid(row=6, column=1, sticky="w", padx=5, pady=2)

        # Status label
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(main_frame, textvariable=self.status_var, foreground="blue").grid(
            row=7, column=0, columnspan=2, sticky="w", padx=5, pady=5
        )

        # Start button
        self.start_button = ttk.Button(main_frame, text="Start calibration", command=self.on_start)
        self.start_button.grid(row=8, column=0, columnspan=2, pady=10)

    def on_start(self):
        """
        Callback for the 'Start calibration' button.
        Validates inputs and runs the sweep.
        """
        try:
            filename = self.filename_var.get().strip()
            if not filename:
                raise ValueError("Output filename must not be empty.")

            f_start_mhz = float(self.f_start_var.get())
            f_end_mhz = float(self.f_end_var.get())
            f_step_mhz = float(self.f_step_var.get())

            p_start = float(self.p_start_var.get())
            p_end = float(self.p_end_var.get())
            p_step = float(self.p_step_var.get())

            if f_start_mhz <= 0 or f_end_mhz <= 0 or f_step_mhz <= 0:
                raise ValueError("Frequencies must be positive and step > 0.")
            if f_end_mhz < f_start_mhz:
                raise ValueError("End frequency must be >= start frequency.")
            if p_step <= 0:
                raise ValueError("Power step must be > 0.")
            if p_end < p_start:
                raise ValueError("End power must be >= start power.")

            f_start = f_start_mhz * 1e6
            f_end = f_end_mhz * 1e6
            f_step = f_step_mhz * 1e6

        except ValueError as e:
            messagebox.showerror("Input error", str(e))
            return

        self.start_button.config(state="disabled")
        self.status_var.set("Running calibration...")
        self.master.update_idletasks()

        try:
            run_calibration(
                filename=filename,
                f_start=f_start,
                f_end=f_end,
                f_step=f_step,
                p_start=p_start,
                p_end=p_end,
                p_step=p_step,
                status_callback=self.set_status,
            )
            messagebox.showinfo("Done", f"Calibration finished and saved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error during calibration", str(e))
        finally:
            self.start_button.config(state="normal")
            self.status_var.set("Ready.")

    def set_status(self, text):
        """
        Update the status label in the GUI.
        """
        self.status_var.set(text)
        self.master.update_idletasks()


def run_calibration(
    filename,
    f_start,
    f_end,
    f_step,
    p_start,
    p_end,
    p_step,
    status_callback=None,
):
    """
    Run the full frequency/power sweep and save results to CSV.

    Parameters are all in SI units (Hz, dBm).
    The status_callback, if provided, is a function taking a single string
    to update the GUI status.
    """
    def update_status(msg):
        if status_callback is not None:
            status_callback(msg)
        print(msg)

    # Build frequency and power arrays
    frequencies = np.arange(f_start, f_end + f_step / 2, f_step)
    powers = np.arange(p_start, p_end + p_step / 2, p_step)

    update_status(
        f"Frequencies: {len(frequencies)} points from {frequencies[0]/1e9:.1f} to {frequencies[-1]/1e9:.1f} GHz"
    )
    update_status(
        f"Powers: {len(powers)} levels from {powers[0]:.1f} to {powers[-1]:.1f} dBm"
    )

    # Initialize CSV header
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        header = ["Frequency (Hz)"] + [str(int(p)) for p in powers]
        writer.writerow(header)

    results = {f: {p: None for p in powers} for f in frequencies}

    # Initialize instruments
    inst = open_ms2840a()
    tx_iface = PlutoTxInterface("ip:192.168.2.1")
    utils = signal_utils.SignalUtils()

    try:
        for p_tx in powers:
            update_status(f"TX Power: {p_tx:.1f} dBm")
            for f_center in frequencies:
                update_status(f"Measuring at {f_center/1e9:.3f} GHz, {p_tx:.1f} dBm")

                tx_params = TxParams(
                    f_rf=int(f_center),
                    delta_f=int(1e6),
                    fs=int(4e6),
                    pe_dbm=int(p_tx),
                    n_sample=int(4096),
                )

                signal_v, signal_codes = utils.generate_two_tone_baseband(
                    pe_dbm=tx_params.pe_dbm,
                    delta_f=tx_params.delta_f,
                    n_sample=tx_params.n_sample,
                )

                tx_iface.configure_tx(tx_params)
                tx_iface.load_waveform(signal_codes)

                time.sleep(STABILIZATION_DELAY)
                p_meas = measure_peak(inst, f_center, SPAN, RBW)
                results[f_center][p_tx] = p_meas

        # Final CSV write
        with open(filename, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for f_center in frequencies:
                row = [f_center] + [results[f_center][p] for p in powers]
                writer.writerow(row)

    finally:
        inst.close()

    update_status("Calibration completed.")


if __name__ == "__main__":
    root = tk.Tk()
    app = CalibrationApp(root)
    root.mainloop()
