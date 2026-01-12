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
    
    def compute_delta_db(
        self,
        f,
        spectrum_dbm,
        f_fund=500e3,
        f_im3=1.5e6,
        search_bw=100e3
    ):
        """
        Calcule Delta_dB pour un test deux-tons :
        Delta_dB = moyenne de (P_fondamental - P_IM3) sur les deux côtés.

        Paramètres
        ----------
        f : ndarray
            Axe fréquentiel (Hz), cohérent avec spectrum_dbm.
        spectrum_dbm : ndarray
            Spectre en dBm (monolatéral).
        f_fund : float
            Fréquence absolue des fondamentaux (Hz), p.ex. 500 kHz.
        f_im3 : float
            Fréquence absolue des IM3 (Hz), p.ex. 1.5 MHz.
        search_bw : float
            Largeur de bande de recherche autour de chaque fréquence (Hz).

        Retour
        ------
        delta_db : float
            Delta_dB moyen entre fondamentaux et IM3 (en dB).
        P1_avg_dbm : float
            Puissance moyenne des deux fondamentaux (en dBm).
        """

        def local_max_in_band(f_center):
            """Retourne l'amplitude max et la fréquence correspondante dans une bande autour de f_center."""
            mask = (f >= (f_center - search_bw)) & (f <= (f_center + search_bw))
            if not np.any(mask):
                raise ValueError(f"Aucun point dans la bande autour de {f_center} Hz")
            idx_band = np.where(mask)[0]
            idx_local_max = idx_band[np.argmax(spectrum_dbm[idx_band])]
            return spectrum_dbm[idx_local_max], f[idx_local_max]

        # Fondamentaux (côté + et côté -)
        P1_pos_dbm, f1_pos = local_max_in_band(+f_fund)
        P1_neg_dbm, f1_neg = local_max_in_band(-f_fund)

        # IM3 (côté + et côté -)
        P3_pos_dbm, f3_pos = local_max_in_band(+f_im3)
        P3_neg_dbm, f3_neg = local_max_in_band(-f_im3)

        # Deltas individuels
        delta_pos = P1_pos_dbm - P3_pos_dbm
        delta_neg = P1_neg_dbm - P3_neg_dbm
        print(f"Fundamental +: {P1_pos_dbm:.2f} dBm at {f1_pos/1e6:.3f} MHz")
        print(f"Fundamental -: {P1_neg_dbm:.2f} dBm at {f1_neg/1e6:.3f} MHz")
        print(f"IM3 -: {P3_neg_dbm:.2f} dBm at {f3_neg/1e6:.3f} MHz")
        print(f"IM3 +: {P3_pos_dbm:.2f} dBm at {f3_pos/1e6:.3f} MHz")

        # Moyennes
        delta_db = 0.5 * (delta_pos + delta_neg)
        P1_avg_dbm = 0.5 * (P1_pos_dbm + P1_neg_dbm)

        return delta_db, P1_avg_dbm
    
    def compute_ip3(self, power_dbm,f,spectrum_dbm):
        """
        Compute the output power at the third-order intermodulation point (IP3).

        Parameters:
        - power_dbm (float): Input power in dBm.
        - delta_db (float): Delta in dB.

        Returns:
        - ip3_dbm (float): Output IP3 power in dBm.
        """
        delta_db,peak_idx = self.compute_delta_db(f,spectrum_dbm)
        print(f"Delta dB between fundamental and IM3: {delta_db} dB")
        print(f"Peaks at indices: {peak_idx}")
        ip3_dbm = power_dbm + (delta_db / 2.0)
        return ip3_dbm