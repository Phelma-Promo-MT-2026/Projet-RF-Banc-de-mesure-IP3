import numpy as np


class SignalUtils:
    def _dbm_to_vpeak(self, pe_dbm, r_ohm=50):
        # Convert power level in dBm into peak voltage for a given load resistance
        p_w = 10.0 ** ((pe_dbm - 30.0) / 10.0)      # Power in watts from dBm
        v_rms = np.sqrt(p_w * r_ohm)                # RMS voltage from P=V^2/R
        v_peak = v_rms * np.sqrt(2.0)               # Peak voltage from RMS
        return v_peak

    def generate_two_tone_baseband(self, pe_dbm, delta_f, n_sample, r_ohm=50):
        # Generate a baseband test signal and corresponding DAC codes
        # Sampling frequency chosen as 4 × tone spacing
        fs = delta_f * 4
        t = np.arange(n_sample) / fs

        # Convert desired power to peak voltage
        v_peak = self._dbm_to_vpeak(pe_dbm, r_ohm=r_ohm)
        signal_v = v_peak * np.cos(2.0 * np.pi * (delta_f / 2) * t)

        # Quantize to signed 16‑bit integer codes for DAC
        max_code = (2 ** 15) - 1  # Max code for signed 16-bit DAC [-2^15; 2^15-1]
        scale = max_code / v_peak
        signal_codes = (signal_v * scale).astype(np.int16)

        # Return analog-domain waveform and corresponding integer DAC codes
        return signal_v, signal_codes

    def modulate_to_rf(self, delta_f, n_sample, signal_baseband, f_rf):
        # Perform real RF modulation of a baseband signal (theoretical model)
        fs = delta_f * 4.0
        t = np.arange(n_sample) / fs
        carrier = np.cos(2.0 * np.pi * f_rf * t)
        signal_rf_v = signal_baseband * carrier
        return signal_rf_v

    def compute_fft(self, signal_v, fs, f_rf):
        # Compute centered FFT, power per bin and absolute frequency axis
        """
        Spectrum in dBm per bin with centered FFT.
        Frequency axis is given as absolute frequencies around f_rf.
        signal_v: time-domain samples (int16 or float).
        """
        N = len(signal_v)
        # Centered and normalized FFT on raw ADC codes
        X = np.fft.fftshift(np.fft.fft(signal_v)) / N

        A_sample = np.abs(X)
        # Power per bin in arbitrary units (ADC^2 scaled to ohmic load)
        P_bin = (np.abs(X) ** 2) / 2 * 50

        # Avoid log10(0) by enforcing a minimum power level
        P_bin_safe = P_bin.copy()
        P_bin_safe[P_bin_safe <= 0] = 1e-20

        P_dBm = 10 * np.log10(P_bin_safe)

        # Centered frequency axis, then shifted to absolute RF frequency
        freq_base = np.fft.fftshift(np.fft.fftfreq(N, d=1.0 / fs))  # [-fs/2; +fs/2]
        freq_abs = freq_base + f_rf

        # Return absolute frequency, raw power, dBm spectrum and magnitude
        return freq_abs, P_bin, P_dBm, A_sample

    def spectrum_to_dbm(self, spectrum, R=50):
        # Convert an amplitude spectrum into dBm assuming a resistive load
        eps = 1e-20                         # Small floor to avoid log(0)
        P_w = (np.abs(spectrum) ** 2) / R   # Power in watts from V^2/R
        P_mw = P_w * 1e3                    # Convert watts to milliwatts
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
        Compute Delta_dB for a two-tone test:
        Delta_dB = average of (P_fundamental - P_IM3) on both sides.

        Parameters
        ----------
        f : ndarray
            Frequency axis (Hz), aligned with spectrum_dbm.
        spectrum_dbm : ndarray
            Spectrum in dBm (single-sided or centered).
        f_fund : float
            Absolute frequency of the fundamentals (Hz), e.g., 500 kHz.
        f_im3 : float
            Absolute frequency of IM3 components (Hz), e.g., 1.5 MHz.
        search_bw : float
            Search bandwidth around each target frequency (Hz).

        Returns
        -------
        delta_db : float
            Average Delta_dB between fundamentals and IM3 (dB).
        P1_avg_dbm : float
            Average power of the two fundamental tones (dBm).
        """

        def local_max_in_band(f_center):
            # Find maximum amplitude and its frequency around a given center
            mask = (f >= (f_center - search_bw)) & (f <= (f_center + search_bw))
            if not np.any(mask):
                raise ValueError(f"No points in band around {f_center} Hz")
            idx_band = np.where(mask)[0]
            idx_local_max = idx_band[np.argmax(spectrum_dbm[idx_band])]
            return spectrum_dbm[idx_local_max], f[idx_local_max]

        # Fundamentals (positive and negative side)
        P1_pos_dbm, f1_pos = local_max_in_band(+f_fund)
        P1_neg_dbm, f1_neg = local_max_in_band(-f_fund)

        # IM3 components (positive and negative side)
        P3_pos_dbm, f3_pos = local_max_in_band(+f_im3)
        P3_neg_dbm, f3_neg = local_max_in_band(-f_im3)

        # Individual deltas between fundamentals and IM3
        delta_pos = P1_pos_dbm - P3_pos_dbm
        delta_neg = P1_neg_dbm - P3_neg_dbm
        print(f"Fundamental +: {P1_pos_dbm:.2f} dBm at {f1_pos/1e6:.3f} MHz")
        print(f"Fundamental -: {P1_neg_dbm:.2f} dBm at {f1_neg/1e6:.3f} MHz")
        print(f"IM3 -: {P3_neg_dbm:.2f} dBm at {f3_neg/1e6:.3f} MHz")
        print(f"IM3 +: {P3_pos_dbm:.2f} dBm at {f3_pos/1e6:.3f} MHz")

        # Average delta and fundamental power over both sides
        delta_db = 0.5 * (delta_pos + delta_neg)
        P1_avg_dbm = 0.5 * (P1_pos_dbm + P1_neg_dbm)

        return delta_db, P1_avg_dbm
    
    def search_peak_in_band(
        self,
        f,
        spectrum_dbm,
        f_rf,
        f_tone,
        f_im3,
        search_bw=100e3
    ):
        """
        Search for the 2 fundamental tones and the 2 IMD3 products around
        their expected frequencies.

        Parameters
        ----------
        f : ndarray
            Frequency axis (Hz), same length as spectrum_dbm.
        spectrum_dbm : ndarray
            Spectrum in dBm.
        f_tone : float
            Absolute frequency of the fundamental tones (Hz).
        f_im3 : float
            Absolute frequency of the IM3 products (Hz).
        search_bw : float
            Half-bandwidth of the search window around each target frequency (Hz).

        Returns
        -------
        p_tone_pos : float
            Power (dBm) of the positive fundamental tone (+f_tone).
        p_tone_neg : float
            Power (dBm) of the negative fundamental tone (-f_tone).
        p_im3_pos : float
            Power (dBm) of the positive IM3 product (+f_im3).
        p_im3_neg : float
            Power (dBm) of the negative IM3 product (-f_im3).
        """

        def local_max_in_band(f_center):
            # Find maximum in a small band around f_center
            mask = (f >= (f_center - search_bw)) & (f <= (f_center + search_bw))
            if not np.any(mask):
                raise ValueError(f"No points in band around {f_center} Hz")
            idx_band = np.where(mask)[0]
            idx_local_max = idx_band[np.argmax(spectrum_dbm[idx_band])]
            return spectrum_dbm[idx_local_max]

        # Fundamentals
        p_tone_pos = local_max_in_band(f_rf+f_tone)
        p_tone_neg = local_max_in_band(f_rf-f_tone)

        # IM3 products
        p_im3_pos = local_max_in_band(f_rf+f_im3)
        p_im3_neg = local_max_in_band(f_rf-f_im3)
        
        return p_tone_pos, p_tone_neg, p_im3_pos, p_im3_neg
