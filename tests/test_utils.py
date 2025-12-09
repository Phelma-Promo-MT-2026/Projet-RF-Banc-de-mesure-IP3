from src.utils import *  # adapter au vrai nom de ta classe


class test_utils:
    def __init__(self):
        self.tools = utils()

    def test_fft_calculation_base_band(self, g, delta_f, fs, n_sample):
        # ----------------------------------------------#
        # ---      Baseband signal generation        ---#
        # ----------------------------------------------#
        signal = self.tools.generate_waveform_base_band(g, delta_f, fs, n_sample)
        if signal is None:
            return None

        # ----------------------------------------------#
        # ---          FFT Calculation Test           ---#
        # ----------------------------------------------#
        frequency, spectrum = self.tools.perform_fft(signal, fs, n_sample)
        self.tools.display_fft(frequency, spectrum)

        return frequency, spectrum
