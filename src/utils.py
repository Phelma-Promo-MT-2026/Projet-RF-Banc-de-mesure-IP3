import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk


class tools_box:
    def __init__(self):
        pass

    def generate_waveform_base_band(self, g, delta_f, fs, n_sample):
        # -------------------------------------#
        # --       Signal Configuration      --#
        # -------------------------------------#
        t = np.arange(n_sample) / fs
        signal = g * np.cos(2 * np.pi * (delta_f / 2) * t)
        signal = signal * (2**14)
        return signal

    def generate_2tons_waveform(self, f_rf, g, delta_f, fs, n_sample):
        # -------------------------------------#
        # --       Signal Configuration      --#
        # -------------------------------------#
        t = np.arange(n_sample) / fs
        signal = g * (
              np.cos(2 * np.pi * (f_rf - delta_f / 2) * t)
            + np.cos(2 * np.pi * (f_rf + delta_f / 2) * t)
        )
        signal = signal * (2**14)
        return signal

    def perform_fft(self, signal, fs, n_sample=None):
        # ---------------------------------
        # ---       FFT Calculation      ---
        # ---------------------------------
        if n_sample is None:
            n_sample = len(signal)

        sig = np.asarray(signal)
        if len(sig) > n_sample:
            sig = sig[:n_sample]
        elif len(sig) < n_sample:
            pad = np.zeros(n_sample - len(sig))
            sig = np.concatenate((sig, pad))

        # FFT
        spectrum_complex = np.fft.fft(sig, n=n_sample)
        spectrum = np.abs(spectrum_complex) * (2.0 / n_sample)

        # On ne garde que la moitié positive
        freq = np.fft.fftfreq(n_sample, d=1.0 / fs)
        half = n_sample // 2
        freq = freq[:half]
        spectrum = spectrum[:half]

        return freq, spectrum

    def display_fft(self, frequency, spectrum, ax=None):
        # ---------------------------------
        # ---        FFT Display         ---
        # ---------------------------------
        if ax is None:
            plt.figure()
            ax = plt.gca()

        ax.plot(frequency, spectrum)
        ax.set_title("FFT of the signal")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Amplitude")
        ax.grid(True)

        if not isinstance(ax.figure.canvas, FigureCanvasTkAgg):
            plt.show()
