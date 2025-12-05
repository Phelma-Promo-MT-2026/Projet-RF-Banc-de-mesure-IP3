from src.pluto_interface import pluto_interface
from src.error_manager import error_manager

class test_tx():
    
    def __init__(self):       
        self.pluto = pluto_interface()

    def send_signal_to_pluto(self,f_rf, g, delta_f, fs, n_sample, pe):
        #----------------------------------------------#
        #---          Send signal to Pluto          ---#
        #----------------------------------------------#
        self.pluto.send_waveform(f_rf, g, delta_f, fs, n_sample, pe)
