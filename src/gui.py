import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt

from pluto_interface import pluto_interface
from error_manager import  error_manager
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from tkinter import ttk


class main_window(tk.Tk):
    
    def __init__(self):
        super().__init__()
        
        # === Parameter declaration ===
        #self.pluto = pluto_interface()
        
        # === Main windows ===
        self.title("PlutoSDR Signal Generator GUI")
        self.geometry("1000x600")

        # === Set template ===
        frame_left = ttk.Frame(self, padding=10)
        frame_left.pack(side="left", fill="y")

        frame_right = ttk.Frame(self, padding=10)
        frame_right.pack(side="right", expand=True, fill="both")

        # === User fields ===
        ttk.Label(frame_left, text="Power Tx (dB):").pack(anchor="w")
        self.entry_power = ttk.Entry(frame_left)
        self.entry_power.insert(0, "0")
        self.entry_power.pack(fill="x")

        ttk.Label(frame_left, text="Delta f (Hz):").pack(anchor="w")
        self.entry_delta_f = ttk.Entry(frame_left)
        self.entry_delta_f.insert(0, "1e6")
        self.entry_delta_f.pack(fill="x")

        ttk.Label(frame_left, text="Frequency RF (Hz):").pack(anchor="w")
        self.entry_rf = ttk.Entry(frame_left)
        self.entry_rf.insert(0, "2.4e9")
        self.entry_rf.pack(fill="x")

        ttk.Label(frame_left, text="Sample Frequency (Hz):").pack(anchor="w")
        self.entry_fs = ttk.Entry(frame_left)
        self.entry_fs.insert(0, "10e6")
        self.entry_fs.pack(fill="x")

        ttk.Label(frame_left, text="Gain:").pack(anchor="w")
        self.entry_gain = ttk.Entry(frame_left)
        self.entry_gain.insert(0, "1")
        self.entry_gain.pack(fill="x")

        ttk.Label(frame_left, text="Sample number:").pack(anchor="w")
        self.entry_N = ttk.Entry(frame_left)
        self.entry_N.insert(0, "4096")
        self.entry_N.pack(fill="x")

        # === Buttons ===
        ttk.Button(frame_left, text="Generate signal", command=self.send_signal_to_pluto).pack(pady=20)

        # === Spectrum ===
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def send_signal_to_pluto(self):
        #----------------------------------------------#
        #---            Get all user field          ---#
        #----------------------------------------------#
        try:
            f_rf     = int(float(self.entry_rf.get()))
            g        = int(float(self.entry_gain.get()))
            delta_f  = int(float(self.entry_delta_f.get()))
            fs       = int(float(self.entry_fs.get()))
            n_sample = int(float(self.entry_N.get()))  
            pe       = int(float(self.entry_power.get()))
        except ValueError:
            print("Erreur : une des valeurs saisies est invalide.")
            return
        #----------------------------------------------#
        #---             Send to Pluto              ---#
        #----------------------------------------------#
        
        #self.pluto.send_waveform(f_rf, g, delta_f, fs, n_sample, pe)
        #self.pluto.send_waveform(2.35e9,1,10e6,1e6,4096,-10)
        
        #----------------------------------------------#
        #--- Simulate modulated signal on spectrum  ---#
        #----------------------------------------------#
        t = np.arange(n_sample) / fs
        mod = np.sin(2*np.pi*delta_f*t)

        # Amplitude from Power PE (dB)
        A = 10**(pe/20)

        # Modulation IQ (I*cos - Q*sin)
        i = mod
        q = mod 
        rf_signal = A * ( i*np.cos(2*np.pi*f_rf*t) - q*np.sin(2*np.pi*f_rf*t) )

        # === Spectrum computing ===
        spectrum = np.abs(np.fft.fftshift(np.fft.fft(rf_signal)))
        freq = np.fft.fftshift(np.fft.fftfreq(n_sample, 1/fs))
        freq_rf = freq + f_rf
        
        # Fréquences des pics
        f_plus  = f_rf + delta_f
        f_minus = f_rf - delta_f

        # Indices correspondants
        idx_plus  = (np.abs(freq_rf - f_plus)).argmin()
        idx_minus = (np.abs(freq_rf - f_minus)).argmin()

        amp_plus  = spectrum[idx_plus]
        amp_minus = spectrum[idx_minus]

        # === AFFICHAGE ===
        self.ax.clear()
        self.ax.plot(freq_rf, spectrum, label="Spectrum")

        # Marqueurs
        self.ax.scatter([f_plus], [amp_plus], color="red")
        self.ax.scatter([f_minus], [amp_minus], color="red")

        # Annotations
        self.ax.annotate(f"{f_plus/1e6:.3f} MHz",
                        xy=(f_plus, amp_plus),
                        xytext=(0, 15),
                        textcoords="offset points",
                        ha="center",
                        arrowprops=dict(arrowstyle="->"))

        self.ax.annotate(f"{f_minus/1e6:.3f} MHz",
                        xy=(f_minus, amp_minus),
                        xytext=(0, -25),
                        textcoords="offset points",
                        ha="center",
                        arrowprops=dict(arrowstyle="->"))

        self.ax.set_title("Spectre simulé centré sur f_rf")
        self.ax.set_xlabel("Fréquence (Hz)")
        self.ax.set_ylabel("Amplitude")
        self.canvas.draw()