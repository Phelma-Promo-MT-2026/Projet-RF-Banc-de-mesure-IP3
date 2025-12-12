import numpy as np
import matplotlib.pyplot as plt

class utils:

    def __init__(self):
        pass

    def _dbm_to_vpeak(self, pe_dbm, r_ohm=50.0):
        """
        Convert power in dBm to peak voltage (V_peak) across a given resistance (R_ohm).

        Parameters:
        - pe_dbm (float): Power in dBm (total power delivered to R_ohm).
        - r_ohm (float): Load resistance in ohms.

        Returns:
        - v_peak (float): Peak voltage (V) across R_ohm corresponding to pe_dbm.
        """
        # Convert dBm to watts
        p_w = 10.0 ** ((pe_dbm - 30.0) / 10.0)

        # Vrms from power and resistance
        v_rms = np.sqrt(p_w * r_ohm)

        # Vpeak from Vrms
        v_peak = v_rms * np.sqrt(2.0)

        return v_peak

    def generate_waveform_base_band(
        self,
        pe_dbm,
        delta_f,
        n_sample,
        I_enable,
        Q_enable,
        r_ohm=50.0
    ):
        """
        Generate a baseband waveform with given parameters.

        Parameters:
        - pe_dbm (float): Power in dBm (total power delivered to R_ohm).
        - delta_f (float): Frequency of the baseband tone (Hz).
        - n_sample (int): Number of samples.
        - I_enable (bool): Enable I channel.
        - Q_enable (bool): Enable Q channel.
        - r_ohm (float): Load resistance in ohms.

        Returns:
        - signal_v (ndarray): Complex (or real) baseband signal in volts.
        - signal_codes (ndarray of ints): Baseband waveform in DAC digital codes.
        """
        # Sampling frequency
        fs = delta_f * 4
        t = np.arange(n_sample) / fs

        # Get V_peak from power in dBm
        v_peak = self._dbm_to_vpeak(pe_dbm, r_ohm=r_ohm)

        I_channel = np.zeros(n_sample)
        Q_channel = np.zeros(n_sample)

        if (I_enable is False and Q_enable is False):
            print("No channel selected for waveform generation")
            return None, None

        if (I_enable is True and Q_enable is False):
            signal_v = v_peak * np.cos(2.0 * np.pi * (delta_f / 2) * t)

        if (Q_enable is True and I_enable is False):
            signal_v = 1j * v_peak * np.sin(2.0 * np.pi * (delta_f / 2) * t)

        if (I_enable is True and Q_enable is True):
            I_channel = (
                v_peak / np.sqrt(2)
                * np.cos(2.0 * np.pi * (delta_f / 2) * t)
            )
            Q_channel = (
                1j * v_peak / np.sqrt(2)
                * np.sin(2.0 * np.pi * (delta_f / 2) * t)
            )
            signal_v = I_channel + Q_channel

        # Generate baseband signal (V_peak)
        max_code = (2 ** 15) - 1  # Max code for signed 16-bit DAC [-2^15; 2^15-1]
        scale = max_code / v_peak
        signal_codes = signal_v * scale

        return signal_v, signal_codes

    def modulate_waveform(
        self,
        signal_baseband,
        f_rf,
        n_sample,
        delta_f,
        r_ohm=50.0
    ):
        """
        Modulate a baseband waveform to RF with a cosine carrier.

        Parameters:
        - signal_baseband (ndarray): Baseband signal.
        - f_rf (float): RF carrier frequency (Hz).
        - n_sample (int): Number of samples.
        - delta_f (float): Baseband tone frequency (Hz).
        - r_ohm (float): Load resistance in ohms (unused, kept for compatibility).

        Returns:
        - signal_rf_v (ndarray): RF-modulated signal in volts.
        """
        fs = delta_f * 4.0
        t = np.arange(n_sample) / fs

        carrier = np.cos(2.0 * np.pi * f_rf * t)
        signal_rf_v = signal_baseband * carrier

        return signal_rf_v

    def compute_fft(self, signal_v, frequency):
        """
        Compute single-sided FFT amplitude spectrum of a (possibly complex) signal.

        Parameters:
        - signal_v (ndarray): Input time-domain signal.
        - frequency (float): Fundamental frequency used to define sampling rate.

        Returns:
        - f (ndarray): Frequency axis (Hz).
        - spectrum (ndarray): Amplitude spectrum.
        """
        fs = frequency * 4
        N = len(signal_v)  # Number of samples

        # Complex FFT (two-sided)
        spectrum_c = np.fft.fft(signal_v)

        # Take positive frequencies (single-sided)
        spectrum_reel = np.abs(spectrum_c[: N // 2 + 1])

        # Amplitude normalization
        spectrum = np.abs(spectrum_reel) * 2.0 / N

        # Frequency axis
        f = np.fft.rfftfreq(N, d=1.0 / fs)

        return f, spectrum

    def spectrum_to_dbm(self, spectrum, R=50.0):
        """
        Convert an amplitude spectrum (voltage-like) to dBm
        assuming a load R (ohms).

        Parameters:
        - spectrum (ndarray): Voltage amplitude spectrum.
        - R (float): Load resistance in ohms.

        Returns:
        - spectrum_dbm (ndarray): Power spectrum in dBm.
        """
        # Avoid log10(0)
        eps = 1e-20

        # Power in watts: P = V^2 / R
        P_w = (np.abs(spectrum) ** 2) / R

        # Power in mW
        P_mw = P_w * 1e3

        # dBm
        spectrum_dbm = 10.0 * np.log10(P_mw + eps)

        return spectrum_dbm

    def plot_spectrum(
        self,
        x,
        y,
        xlabel="Frequency (Hz)",
        ylabel="Amplitude",
        title="Spectrum"
    ):
        """
        Plot a spectrum using Matplotlib.

        Parameters:
        - x (ndarray): Frequency axis (Hz).
        - y (ndarray): Amplitude or power axis.
        - xlabel (str): Label for x-axis.
        - ylabel (str): Label for y-axis.
        - title (str): Plot title.
        """
        plt.figure()
        plt.plot(x, y)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.grid(True)
        plt.show()
