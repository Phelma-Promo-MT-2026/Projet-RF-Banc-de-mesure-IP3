import os
import json
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from src_old.pluto_interface import *
from src_old.utils import *
from src_old.error_manager import *

SETTINGS_FILE = "src/settings.json"


def load_settings():
    """ Load default settings from a JSON file if available. """
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None
    return None


class parameter(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Advanced parameters")
        self.geometry("340x280")

        self.protocol("WM_DELETE_WINDOW", self.on_close)
         
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        # --- delta_f ---
        ttk.Label(main_frame, text="delta_f (Hz) :").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_delta_f = ttk.Entry(main_frame)
        self.entry_delta_f.grid(row=0, column=1, sticky="ew", pady=5)
        self.entry_delta_f.insert(0, f"{self.parent.delta_f:.1e}")

        # --- n_sample ---
        ttk.Label(main_frame, text="n_sample :").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_n_sample = ttk.Entry(main_frame)
        self.entry_n_sample.grid(row=1, column=1, sticky="ew", pady=5)
        self.entry_n_sample.insert(0, f"{float(self.parent.n_sample)}")

        # --- f_sample ---
        ttk.Label(main_frame, text="f_sample (Hz) :").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_f_sample = ttk.Entry(main_frame)
        self.entry_f_sample.grid(row=2, column=1, sticky="ew", pady=5)
        self.entry_f_sample.insert(0, f"{self.parent.fs_pluto:.1e}")

        # --- f_rf ---
        ttk.Label(main_frame, text="f_rf (Hz) :").grid(row=3, column=0, sticky="w", pady=5)
        self.entry_f_rf = ttk.Entry(main_frame)
        self.entry_f_rf.grid(row=3, column=1, sticky="ew", pady=5)
        self.entry_f_rf.insert(0, f"{self.parent.f_rf:.1e}")

        # --- pe ---
        ttk.Label(main_frame, text="Power Tx (dBm) :").grid(row=4, column=0, sticky="w", pady=5)
        self.entry_pe = ttk.Entry(main_frame)
        self.entry_pe.grid(row=4, column=1, sticky="ew", pady=5)
        self.entry_pe.insert(0, f"{float(self.parent.pe):}")
        
        # --- g_rx ---
        ttk.Label(main_frame, text="Gain Rx (dBm) :").grid(row=4, column=0, sticky="w", pady=5)
        self.entry_g_rx = ttk.Entry(main_frame)
        self.entry_g_rx.grid(row=4, column=1, sticky="ew", pady=5)
        self.entry_g_rx.insert(0, f"{float(self.parent.pe):}")

        # --- boutons ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=15, sticky="e")

        ttk.Button(btn_frame, text="Save setting by default", command=self.save_defaults).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Apply", command=self.apply_and_close).pack(
            side="right", padx=5
        )

        main_frame.columnconfigure(1, weight=1)
        
    def on_close(self):
        """ close via the cross: we also apply the values before closing."""
        self.apply_and_close()
        
    def _read_fields(self):
        """ read fields and return a dict with typed values."""
        delta_f = float(self.entry_delta_f.get())
        n_sample = int(float(self.entry_n_sample.get()))
        f_sample = float(self.entry_f_sample.get())
        f_rf = float(self.entry_f_rf.get())
        pe = float(self.entry_pe.get())
        return {
            "delta_f": delta_f,
            "n_sample": n_sample,
            "f_sample": f_sample,
            "f_rf": f_rf,
            "pe": pe,
        }

    def apply_and_close(self):
        try:
            vals = self._read_fields()
        except ValueError:
            return

        self.parent.delta_f = vals["delta_f"]
        self.parent.n_sample = vals["n_sample"]
        self.parent.fs_pluto = vals["f_sample"]
        self.parent.f_rf = vals["f_rf"]
        self.parent.pe = vals["pe"]
        
        self.parent.update_entries_from_params()
        
        self.destroy()

    def save_defaults(self):
        """ save the values as default parameters in a JSON file. """
        try:
            vals = self._read_fields()
        except ValueError:
            return

        settings = {
            "delta_f": vals["delta_f"],
            "n_sample": vals["n_sample"],
            "f_sample": vals["f_sample"],
            "f_rf": vals["f_rf"],
            "pe": vals["pe"],
        }

        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
        self.apply_and_close()
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

    def clear(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")



class main_window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.err_mgr = error_manager()
        
        defaults = load_settings() or {}
        self.delta_f = defaults.get("delta_f", 1e6)
        self.fs_pluto = defaults.get("f_sample", self.delta_f * 4)
        self.n_sample = int(defaults.get("n_sample", 1024))
        self.f_rf = defaults.get("f_rf", 2.4e9)
        self.pe = defaults.get("pe", -20)
        self.g_rx = defaults.get("g_rx",0)
        self.k = 0
        self.test_pluto = pluto_interface()
        self.test_utils = utils()

        self.title("PlutoSDR Signal Generator GUI")
        self.geometry("1000x900")

        # === Layout principal ===
        frame_left = ttk.Frame(self, padding=10)
        frame_left.pack(side="left", fill="y")

        # frame principal droite (plots + log)
        frame_right = ttk.Frame(self, padding=10)
        frame_right.pack(side="right", expand=True, fill="both")

        # --- Top bar + bouton engrenage ---
        top_bar = ttk.Frame(frame_left)
        top_bar.pack(fill="x", pady=(0, 10))

        ttk.Label(top_bar, text="All Parameters").pack(side="left")

        self.btn_param = ttk.Button(
            top_bar,
            text="⚙",
            width=3,
            command=self.open_parameter_window,
        )
        self.btn_param.pack(side="right")

        # === User fields ===
        ttk.Label(frame_left, text="Power Tx (dBm):").pack(anchor="w")
        self.entry_power = ttk.Entry(frame_left)
        self.entry_power.insert(0, str(self.pe))
        self.entry_power.pack(fill="x")

        ttk.Label(frame_left, text="Frequency RF (Hz):").pack(anchor="w")
        self.entry_rf = ttk.Entry(frame_left)
        self.entry_rf.insert(0, f"{self.f_rf:.1e}")
        self.entry_rf.pack(fill="x")
        
        ttk.Label(frame_left, text="Gain Rx (dB):").pack(anchor="w")
        self.entry_g_rx = ttk.Entry(frame_left)
        self.entry_g_rx.insert(0, f"{self.g_rx}")
        self.entry_g_rx.pack(fill="x")

        # === Channel selection ===
        channels_frame = ttk.LabelFrame(frame_left, text="Channels")
        channels_frame.pack(fill="x", pady=10)

        self.I_var = tk.BooleanVar(value=True)
        self.Q_var = tk.BooleanVar(value=False)

        self.chk_I = ttk.Checkbutton(
            channels_frame,
            text="Channel I",
            variable=self.I_var
        )
        self.chk_I.pack(anchor="w")

        self.chk_Q = ttk.Checkbutton(
            channels_frame,
            text="Channel Q",
            variable=self.Q_var
        )
        self.chk_Q.pack(anchor="w")

        # === Buttons ===
        ttk.Button(frame_left, text="Send tx", command=self.send).pack(pady=20)
        ttk.Button(frame_left, text="Receive rx", command=self.receive).pack(pady=20)
        ttk.Button(frame_left, text="Send tx / Receive rx", command=self.send_receive).pack(pady=20)
        ttk.Button(frame_left, text="Generate fft", command=self.generate_fft).pack(pady=20)

        # === Partie droite : plots + log ===
        frame_plots = ttk.Frame(frame_right)
        frame_plots.pack(side="top", fill="both", expand=True)

        frame_top = ttk.Frame(frame_plots)
        frame_top.pack(side="top", fill="both", expand=True)

        frame_bottom = ttk.Frame(frame_plots)
        frame_bottom.pack(side="top", fill="both", expand=True)

        # ---------- Spectrum TX attendu ----------
        label_tx = ttk.Label(frame_top, text="Expected on tx")
        label_tx.pack(anchor="w")

        self.fig_tx, self.ax_tx = plt.subplots(figsize=(4, 2))
        self.canvas_tx = FigureCanvasTkAgg(self.fig_tx, master=frame_top)
        self.canvas_tx.get_tk_widget().pack(fill="both", expand=True)

        # ---------- Spectrum RX reçu ----------
        label_rx = ttk.Label(frame_bottom, text="Received on rx")
        label_rx.pack(anchor="w")

        self.fig_rx, self.ax_rx = plt.subplots(figsize=(4, 2))
        self.canvas_rx = FigureCanvasTkAgg(self.fig_rx, master=frame_bottom)
        self.canvas_rx.get_tk_widget().pack(fill="both", expand=True)

        # --- partie basse : log utilisateur ---
        frame_log = ttk.Frame(frame_right)
        frame_log.pack(side="bottom", fill="x")

        # ligne titre + bouton clear
        top_log_bar = ttk.Frame(frame_log)
        top_log_bar.pack(fill="x")

        ttk.Label(top_log_bar, text="Messages :").pack(side="left", anchor="w")

        btn_clear_log = ttk.Button(
            top_log_bar,
            text="Clear",
            command=self.clear_log_messages
        )
        btn_clear_log.pack(side="right")

        # zone texte
        self.text_log = tk.Text(frame_log, height=4, state="disabled")
        self.text_log.pack(fill="x", expand=False)

        self.log = Log(self.text_log)

        self.param_window = None

        # optionnel : initialiser les entrées avec les params
        self.update_entries_from_params()
    
    def clear_log_messages(self):
        """Efface les messages de log affichés."""
        self.log.clear()
        
    def update_entries_from_params(self):
        """Met à jour les champs utilisateur à partir des attributs internes."""
        # RF
        self.entry_rf.delete(0, tk.END)
        self.entry_rf.insert(0, f"{self.f_rf:.1e}")

        # Power
        self.entry_power.delete(0, tk.END)
        self.entry_power.insert(0, str(self.pe))
    def on_close(self):
        plt.close("all")
        self.destroy()
        self.quit()

    def open_parameter_window(self):
        if self.param_window is None or not self.param_window.winfo_exists():
            self.param_window = parameter(self)
        else:
            self.param_window.lift()
            self.param_window.focus_force()

    def send(self):
        f_rf = float(self.entry_rf.get())
        pe = float(self.entry_power.get())
        I_enable = self.I_var.get()  
        Q_enable = self.Q_var.get()
        self.f_rf = f_rf
        self.pe = pe
        return_code = self.test_pluto.send_waveform(int(f_rf), self.delta_f, self.fs_pluto, self.n_sample, float(pe), I_enable, Q_enable)
        if(return_code == 1):
            self.log.write(f"[OK] Send TX: f_rf={f_rf:.3e} Hz, P={pe:.1f} dBm, I={I_enable}, Q={Q_enable}")
        elif (return_code==0):
            self.log.write("Impossible to send Waveform on tx : Pluto not connected")
            self.ax_tx.clear()
            return
        elif (return_code==2):
            self.log.write("Impossible to send Waveform on tx : No channel (I or Q) selected")
            self.ax_tx.clear()
            return
        signal_v, signal_code = self.test_utils.generate_waveform_base_band(int(pe), self.delta_f, self.n_sample, I_enable,Q_enable)
        signal_modulated = self.test_utils.modulate_waveform(signal_v, int(f_rf), self.n_sample,self.delta_f)
        f, spectrum = self.test_utils.compute_fft(signal_modulated, self.f_rf)
        spectrum_db = self.test_utils.spectrum_to_dbm(spectrum)
        self.display_spectrum_tx(signal_modulated, f_rf)
        
        
    def receive(self):
        f_rf = float(self.entry_rf.get())
        g_rx = float(self.entry_g_rx.get())
        pe = float(self.entry_power.get())
        self.f_rf = f_rf
        
        rx_sample = self.test_pluto.receive_waveform(
            int(f_rf),
            self.delta_f,
            self.fs_pluto,
            self.n_sample,
            0,
        )
        # Spectre à partir des codes ADC complexes
        freq_abs, P_bin, P_dBm,A_sample = self.test_pluto.spectrum_to_dBm(
            rx_sample, self.fs_pluto, int(f_rf)
        )
        iip3_dbm = self.test_utils.compute_ip3(pe,freq_abs-f_rf,A_sample)
        self.log.write(f"[INFO] Computed IIP3: {iip3_dbm:.2f} dBm")

        # Affichage linéaire (P_bin) autour de f_rf
        self.display_spectrum_rx(
            (freq_abs - f_rf) / 1e6,   # offset en MHz
            A_sample,
            "Received on rx",
            "Frequency offset [MHz]",
            "P_bin [ADC^2]"
        )

    def send_receive(self):
        f_rf = float(self.entry_rf.get())
        pe = float(self.entry_power.get())
        g_rx = float(self.entry_g_rx.get())
        self.f_rf = f_rf
        self.pe = pe
        I_enable = self.I_var.get()
        Q_enable = self.Q_var.get()

        return_code = self.test_pluto.send_waveform(
            int(f_rf),
            self.delta_f,
            self.fs_pluto,
            self.n_sample,
            int(pe),
            I_enable,
            Q_enable,
        )
        #signal_v, signal_code = self.test_utils.generate_waveform_base_band(int(pe), self.delta_f, self.n_sample, I_enable,Q_enable)
        #signal_modulated = self.test_utils.modulate_waveform(signal_v, int(f_rf), self.n_sample,self.delta_f)
        #self.display_spectrum_tx(signal_modulated, f_rf)
        if return_code == 1:
            self.log.write(
                f"[OK] Send TX: f_rf={f_rf:.3e} Hz, P={pe:.1f} dBm, I={I_enable}, Q={Q_enable}"
            )
        elif return_code == 0:
            self.log.write("Impossible to send Waveform on tx : Pluto not connected")
            self.ax_tx.clear()
            return
        elif return_code == 2:
            self.log.write("Impossible to send Waveform on tx : No channel (I or Q) selected")
            self.ax_tx.clear()
            return

        # --- Réception ---
        rx_sample = self.test_pluto.receive_waveform(
            int(f_rf),
            self.delta_f,
            self.fs_pluto,
            self.n_sample,
            0,
        )
        # Spectre à partir des codes ADC complexes
        freq_abs, P_bin, P_dBm,A_sample = self.test_pluto.spectrum_to_dBm(
            rx_sample, self.fs_pluto, int(f_rf)
        )
        iip3_dbm = self.test_utils.compute_ip3(pe,freq_abs-f_rf,A_sample)
        self.log.write(f"[INFO] Computed IIP3: {iip3_dbm:.2f} dBm")

        # Affichage linéaire (P_bin) autour de f_rf
        self.display_spectrum_rx(
            (freq_abs) / 1e6,   # offset en MHz
            A_sample,
            "Received on rx",
            "Frequency offset [MHz]",
            "P_bin [ADC^2]"
        )
        
    def generate_fft(self):
        f_rf = float(self.entry_rf.get())
        pe = float(self.entry_power.get())
        I_enable = self.I_var.get()
        Q_enable = self.Q_var.get()
        self.pe = pe
        signal_v, signal_code = self.test_utils.generate_waveform_base_band(int(pe), self.delta_f, self.n_sample,I_enable, Q_enable)
        if(signal_v is None):
            self.log.write("[ERROR] No channel selected for waveform generation")
            return
        signal_modulated = self.test_utils.modulate_waveform(signal_v, int(f_rf), self.n_sample,self.delta_f)
        
        f, spectrum = self.test_utils.compute_fft(signal_modulated, int(f_rf))
        spectrum_db = self.test_utils.spectrum_to_dbm(spectrum)
        
        self.log.write(f"[OK] Generated FFT: f_rf={f_rf:.3e} Hz, P={pe:.1f} dBm, I={I_enable}, Q={Q_enable}")
        self.display_spectrum_tx(signal_modulated, f_rf)
        
    def display_spectrum_rx(self, x, y, title="Received on rx", x_axis="", y_axix=""):
        self.ax_rx.clear()
        self.ax_rx.plot(x, y)
        self.ax_rx.set_title(title)
        # par exemple +/- fs_pluto/2 en MHz
        #span_MHz = (self.fs_pluto / 2) / 1e6
        #self.ax_rx.set_xlim(-span_MHz, span_MHz)
        self.ax_rx.set_xlabel(x_axis)
        self.ax_rx.set_ylabel(y_axix)
        self.ax_rx.grid(True)
        self.canvas_rx.draw()
        
    def debug_plot_time(self,rx_samples):
        plt.figure()
        plt.plot(np.real(rx_samples), label="I")
        plt.plot(np.imag(rx_samples), label="Q")
        plt.axhline(2047, color="r", linestyle="--")
        plt.axhline(-2048, color="r", linestyle="--")
        plt.legend()
        plt.title("ADC codes vs échantillons")
        plt.grid(True)
        plt.show()

    
    def display_spectrum_tx(self,signal_v, f_rf):
        f, spectrum = self.test_utils.compute_fft(signal_v, int(f_rf))
        spectrum_db = self.test_utils.spectrum_to_dbm(spectrum)
        self.ax_tx.clear()
        self.ax_tx.plot(f, spectrum_db)
        self.ax_tx.set_title("Expected on tx")
        self.ax_tx.set_xlabel("Frequency (Hz)")
        self.ax_tx.set_ylabel("Amplitude (dBm)")
        self.ax_tx.grid(True)
        self.canvas_tx.draw()
