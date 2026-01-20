import numpy as np

class SignalUtils : 
    def _dbm_to_vpeak(self,pe_dbm, r_ohm=50): # conversion dBm → V_peak.
        p_w = 10.0 ** ((pe_dbm - 30.0) / 10.0) # Convert dBm to watts
        v_rms = np.sqrt(p_w * r_ohm) # Vrms from power and resistance
        v_peak = v_rms * np.sqrt(2.0) # Vpeak from Vrms
        return v_peak

    def generate_two_tone_baseband(self,pe_dbm, delta_f, n_sample, r_ohm=50):
        # Sampling frequency
        fs = delta_f * 4
        t = np.arange(n_sample) / fs
        
        # Get V_peak from power in dBm
        v_peak = self._dbm_to_vpeak(pe_dbm, r_ohm=r_ohm)
        signal_v = v_peak * np.cos(2.0 * np.pi * (delta_f / 2) * t)
        
        # Generate baseband signal (V_peak)
        max_code = (2 ** 15) - 1  # Max code for signed 16-bit DAC [-2^15; 2^15-1]
        scale = max_code / v_peak
        signal_codes = (signal_v * scale).astype(np.int16)
        #Return  signal_v (complex) and signal_codes (int16).
        return signal_v, signal_codes

    def modulate_to_rf(self,delta_f, n_sample, signal_baseband, f_rf): # RF modulation - theoretical.
        fs = delta_f * 4.0
        t = np.arange(n_sample) / fs
        carrier = np.cos(2.0 * np.pi * f_rf * t)
        signal_rf_v = signal_baseband * carrier
        return signal_rf_v
    
    def compute_fft(self,signal_v, fs, f_rf) :# return f, spectrum.
        """
        Spectre en dBm par bin avec FFT centrée.
        Axe fréquence : absolu autour de f_rf.
        rx_samples : échantillons complexes issus de l'ADC (int16 ou float).
        """
        N = len(signal_v)
        # FFT centrée et normalisée (sur les codes ADC bruts)
        X = np.fft.fftshift(np.fft.fft(signal_v)) / N

        #X = np.fft.fft(rx_samples) / N
        
        A_sample = np.abs(X)
        # Puissance par bin en unités ADC^2
        P_bin = (np.abs(X) ** 2)/2*50       # réel

        # éviter log(0)
        P_bin_safe = P_bin.copy()
        P_bin_safe[P_bin_safe <= 0] = 1e-20

        P_dBm = 10 * np.log10(P_bin_safe)

        # Axe fréquence centré
        freq_base = np.fft.fftshift(np.fft.fftfreq(N, d=1.0 / fs))   # [-fs/2; +fs/2]
        #freq_base = np.fft.fftfreq(N, d=1.0 / fs)
        freq_abs  = freq_base + f_rf

        # On renvoie freq_abs (ou freq_base), P_bin réel et P_dBm
        return freq_abs, P_bin, P_dBm, A_sample
        
    
    def spectrum_to_dbm(self,spectrum, R=50) :# amplitude → dBm.
        # Avoid log10(0)
        eps = 1e-20
        # Power in watts: P = V^2 / R
        P_w = (np.abs(spectrum) ** 2) / R
        # Power in mW
        P_mw = P_w * 1e3
        # dBm
        spectrum_dbm = 10.0 * np.log10(P_mw + eps)
        return spectrum_dbm
    
    def compute_delta_db(
        self,
        f,
        spectrum_dbm,
        f_fund=500e3,
        f_im3=1.5e3,
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