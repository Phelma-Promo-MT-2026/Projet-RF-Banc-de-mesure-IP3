import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk

from src.pluto_interface import pluto_interface
from src.error_manager import error_manager

class test_tx_rx():
    
    def __init__(self):       
        self.pluto = pluto_interface()

    def send_signal_to_pluto(self,f_rf, g, delta_f, fs, n_sample, pe):
        #----------------------------------------------#
        #---             Send to Pluto              ---#
        #----------------------------------------------#
        print("send waveform to pluto")
        self.pluto.send_waveform(f_rf, g, delta_f, fs, n_sample, pe)
        #self.pluto.sdr.send_waveform(2.35e9,1,10e6,1e6,4096,-10)
        
    def receive_signal_from_pluto(self,f_rf, g, delta_f, fs, n_sample):
        #----------------------------------------------#
        #---          receive from Pluto            ---#
        #----------------------------------------------#
        print("receive waveform from pluto")
        rx_signal = self.pluto.receive_waveform(f_rf, g, delta_f, fs, n_sample)
        if(rx_signal is None):
            return None
        return rx_signal
    
    def send_and_receive(self,f_rf, g, delta_f, fs, n_sample, pe):
        #----------------------------------------------#
        #---          receive from Pluto            ---#
        #----------------------------------------------#
        rx_signal = self.pluto.send_and_receive(f_rf, g, delta_f, fs, n_sample, pe)
        if(rx_signal is None):
            return None
        #Complex fft
        psd = np.abs(np.fft.fftshift(np.fft.fft(rx_signal)))**2
        psd_dB = 10*np.log10(psd)
        f = np.linspace(fs/-2, fs/2, len(psd))
        freq = np.fft.fftshift(np.fft.fftfreq(n_sample, 1/fs))
        freq_rf = freq + f_rf
        
        return rx_signal
    
    def display_fft(self,signal, fs, n_sample,f_rf,delta_f):
        # -------------------------------
        # FFT
        # -------------------------------
        t = np.arange(n_sample) / fs
        S = np.fft.fftshift(np.fft.fft(signal))
        freqs = np.fft.fftshift(np.fft.fftfreq(n_sample, 1/fs))
        freqs_rf = freqs + f_rf
        S_db = 20*np.log10(np.abs(S))
        
        # -------------------------------
        # Research pic at target frequencies
        # -------------------------------
        target_freqs = [f_rf + delta_f, f_rf - delta_f]
        indices = [np.argmin(np.abs(freqs_rf - f)) for f in target_freqs]
        
        # -------------------------------
        # Display FFT
        # -------------------------------
        # Marqueurs
        for f, idx in zip(target_freqs, indices):
            plt.plot(f/1e6, S_db[idx], "ro")  # point rouge
            plt.text(
                f/1e6,
                S_db[idx],
                f"\n{f/1e6:.6f} MHz\n{S_db[idx]:.1f} dB",
                ha="center",
                va="bottom"
            )
            
        plt.figure(figsize=(8,4))
        plt.plot(freqs_rf/1e6, 20*np.log10(np.abs(S)), label="Spectre")
        plt.xlabel("Frequency (MHz)")
        plt.ylabel("Amplitude (dB)")
        plt.title("Spectrum ")
        plt.grid(True)
        plt.show()
        return