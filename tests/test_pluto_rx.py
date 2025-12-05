from src.pluto_interface import pluto_interface
from src.error_manager import error_manager

class test_rx():
    
    def __init__(self):       
        self.pluto = pluto_interface()
        
    def receive_signal_from_pluto(self,f_rf, g, delta_f, fs, n_sample):
        #----------------------------------------------#
        #---          receive from Pluto            ---#
        #----------------------------------------------#
        rx_signal = self.pluto.receive_waveform(f_rf, g, delta_f, fs, n_sample)
        if(rx_signal is None):
            return None
        return rx_signal
    
    
 