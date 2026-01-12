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
    
    def compute_fft(self,signal_v, frequency) :# return f, spectrum.
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