
import tkinter as tk
from tkinter import ttk
from turtle import left
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from src.iip3_bench import IIP3Bench, TxParams, RxParams
from src.pluto_tx_interface import PlutoTxInterface
from src.pluto_rx_interface import PlutoRxInterface
from src.signal_utils import SignalUtils
from src.error_manager import ErrorManager
from src.Tx_calibration import TxCalibration
import subprocess
import re

class Log:
    def __init__(self, text_widget):
        self.text = text_widget

    def write(self, msg: str):
        if not msg.endswith("\n"):
            msg += "\n"
        self.text.config(state="normal")
        self.text.insert("end", msg)
        self.text.see("end")
        self.text.config(state="disabled")


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        style = ttk.Style(self)
        #style.theme_use('clam')  # un thème qui gère bien les bordures

        style.configure(
            "Section.TLabelframe",
            borderwidth=3,
            relief="groove"
        )
        style.configure(
            "Section.TLabelframe.Label",
            font=("TkDefaultFont", 10, "bold")
        )
        # --- backend ---
        self.log_text = None
        self.log = None
        
        self.err_mgr = ErrorManager()
        sig_utils = SignalUtils()
        self.tx_iface = PlutoTxInterface("ip:192.168.2.1")
        self.rx_iface = PlutoRxInterface("ip:192.168.2.1")
        calib = TxCalibration("plutot_characterization.csv")
        self.bench = IIP3Bench(self.tx_iface, self.rx_iface, sig_utils, self.err_mgr, calib)
        
              
        # --- fenetre ---
        self.title("IIP3 bench – Pluto")
        self.geometry("1000x800")
        
        # default parameter
        self.f_rf = 2.4e9
        self.delta_f = 1e6
        self.pe = -10.0
        self.g_rx = 0.0
        self.n_sample = 100000
        
        # --- left layout (parameter + buttons) ---
        left = ttk.Frame(self, padding=10)
        left.pack(side="left", fill="y")
        # === Section 1 : PERFORM MEASURE ===
        frame_measure = ttk.LabelFrame(left, text="PERFORM MEASURE")
        frame_measure.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_measure, text="f_rf (Hz)").pack(anchor="w")
        self.entry_f_rf = ttk.Entry(frame_measure)
        self.entry_f_rf.insert(0, f"{self.f_rf:.1e}")
        self.entry_f_rf.pack(fill="x")

        ttk.Label(frame_measure, text="P_tx (dBm)").pack(anchor="w")
        self.entry_pe = ttk.Entry(frame_measure)
        self.entry_pe.insert(0, str(self.pe))
        self.entry_pe.pack(fill="x")

        ttk.Button(frame_measure, text="Send TX",
                command=self.send_tx).pack(pady=10, fill="x")
        ttk.Button(frame_measure, text="Receive RX",
                command=self.receive_rx).pack(pady=10, fill="x")

        # === Section 2 : IP3 COMPUTE SECTION ===
        frame_ip3 = ttk.LabelFrame(left, text="IP3 COMPUTE SECTION")
        frame_ip3.pack(fill="x", pady=(10, 0))

        ttk.Label(frame_ip3, text="P_ton measured (dBm)").pack(anchor="w")
        self.entry_p_ton_meas = ttk.Entry(frame_ip3)
        self.entry_p_ton_meas.insert(0, "0")
        self.entry_p_ton_meas.pack(fill="x")

        ttk.Label(frame_ip3, text="P_imd3 measured (dBm)").pack(anchor="w")
        self.entry_p_imd3_meas = ttk.Entry(frame_ip3)
        self.entry_p_imd3_meas.insert(0, "0")
        self.entry_p_imd3_meas.pack(fill="x")

        ttk.Button(frame_ip3, text="Compute IP3",
                command=self.compute_iip3).pack(pady=10, fill="x")

        ttk.Label(frame_ip3, text="Result IP3 (dBm)").pack(anchor="w")
        self.entry_result_ip3 = ttk.Entry(frame_ip3)
        self.entry_result_ip3.insert(0, "N/A")
        self.entry_result_ip3.pack(fill="x")

        # --- right layout (plots + log) ---
        
        right = ttk.Frame(self, padding=10)
        right.pack(side="right", expand=True, fill="both")

        # plots
        frame_plots = ttk.Frame(right)
        frame_plots.pack(side="top", fill="both", expand=True)

        frame_tx = ttk.Frame(frame_plots)
        frame_tx.pack(side="top", fill="both", expand=True)
        frame_rx = ttk.Frame(frame_plots)
        frame_rx.pack(side="top", fill="both", expand=True)

        ttk.Label(frame_tx, text="TX (theorical)").pack(anchor="w")
        self.fig_tx, self.ax_tx = plt.subplots(figsize=(5, 2))
        self.canvas_tx = FigureCanvasTkAgg(self.fig_tx, master=frame_tx)
        self.canvas_tx.get_tk_widget().pack(fill="both", expand=True)

        ttk.Label(frame_rx, text="RX (measured)").pack(anchor="w")
        self.fig_rx, self.ax_rx = plt.subplots(figsize=(5, 2))
        self.canvas_rx = FigureCanvasTkAgg(self.fig_rx, master=frame_rx)
        self.canvas_rx.get_tk_widget().pack(fill="both", expand=True)

        # log
        frame_log = ttk.Frame(right)
        frame_log.pack(side="bottom", fill="x")

        ttk.Label(frame_log, text="Log :").pack(anchor="w")
        self.log_text = tk.Text(frame_log, height=12, state="disabled")
        self.log_text.pack(fill="x")
        self.log = Log(self.log_text)
        
        ttk.Button(frame_log, text="Clear log", command=self.clear_log_messages).pack(pady=10, fill="x")
        
        # maintenant que Log existe, on connecte ErrorManager
        self.err_mgr.set_log_callback(self.log.write)
        self._report_pluto_status()

    def _report_pluto_status(self):
        tx_connected = self.bench.tx_iface.is_connected()
        rx_connected = self.bench.rx_iface.is_connected()

        if tx_connected:
            self.err_mgr.info("Pluto TX détecté et connecté.")
        else:
            self.err_mgr.error("Pluto TX non détecté au démarrage.")

        if rx_connected:
            self.err_mgr.info("Pluto RX détecté et connecté.")
        else:
            self.err_mgr.error("Pluto RX non détecté au démarrage.")


    def _read_params(self):
        if not self.entry_f_rf.get() or not self.entry_pe.get() or not self.entry_p_ton_meas.get() or not self.entry_p_imd3_meas.get():
            self.err_mgr.error("Please fill in all required fields.")
            return None, None, None, None
        f_rf     = int(float(self.entry_f_rf.get()))
        delta_f  = int(1e6) 
        pe       = int(float(self.entry_pe.get()))
        g_rx     = int(0) 
        n_sample = int(100000)
        fs       = int (4e6)  # fixe à 4 MHz pour l'instant
        p_ton_meas = float(self.entry_p_ton_meas.get())
        p_imd3_meas =float(self.entry_p_imd3_meas.get())

        tx = TxParams(
            f_rf    =f_rf,
            delta_f =delta_f,
            fs      =fs,
            pe_dbm  =pe,
            n_sample=n_sample,
        )
        rx = RxParams(
            f_rf    =f_rf,
            fs      =fs,
            n_sample=n_sample,
            g_rx_db =g_rx,
        )
        return tx, rx, p_ton_meas, p_imd3_meas
    
    def send_tx(self):
        if self.bench is None or not self.tx_iface or not self.tx_iface.is_connected():
            self.err_mgr.error("Pluto TX not connected. Connect Pluto to computer and restart Applications.")
            return
        tx, rx, p_ton_meas, p_imd3_meas = self._read_params()
        self.bench.configure(tx, rx)
        freq_abs, P_bin, P_dBm, A_sample = self.bench.send_tx(tx)
        if freq_abs is None:
            return
        self.ax_tx.clear()
        self.ax_tx.plot(freq_abs, P_dBm)
        self.ax_tx.set_xlabel("Hz")
        self.ax_tx.set_ylabel("Amplitude")
        self.ax_tx.grid(True)
        self.canvas_tx.draw()

    def receive_rx(self):
        if self.bench is None or not self.tx_iface or not self.tx_iface.is_connected():
            self.err_mgr.error("Pluto RX not connected. Click first on 'Connect Plutos'.")
            return

        tx, rx, p_ton_meas, p_imd3_meas = self._read_params()
        self.bench.configure(tx, rx)
        rx_samples = self.bench.receive_rx(rx)
        if rx_samples is None:
            return

        freq_abs, P_bin, P_dBm, A_sample = self.bench.signal_utils.compute_fft(rx_samples,rx.fs,rx.f_rf)
        
        self.ax_rx.clear()
        self.ax_rx.plot(freq_abs, A_sample)
        self.ax_rx.set_xlabel("Hz")
        self.ax_rx.set_ylabel("dBm")
        self.ax_rx.grid(True)
        self.canvas_rx.draw()
        
    def compute_iip3(self):
        tx, rx, p_ton_meas, p_imd3_meas = self._read_params()

        delta_db = p_ton_meas - p_imd3_meas
        ip3_dbm = p_ton_meas + (delta_db / 2.0)
        
        self.entry_result_ip3.delete(0, tk.END)
        self.entry_result_ip3.insert(0, f"{ip3_dbm:.2f}")
        pass
    
    def clear_log_messages(self): # efface le log.
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")
    
class ParameterWindow:

    def __init__(self,parent) :# construit les champs.
        self.parent: MainWindow # fenêtre principale.
        #Widgets: entry_delta_f, entry_n_sample, entry_f_sample, entry_f_rf, entry_pe, entry_g_rx
        pass
        
    def _read_fields() :# lit les entrées, renvoie un dict typé.
        pass
    def apply_and_close(): # applique dans parent puis détruit la fenêtre.
        pass
    def save_defaults(): # écrit dans settings.json.
        pass
    def on_close(): # applique puis ferme (croix).
        pass