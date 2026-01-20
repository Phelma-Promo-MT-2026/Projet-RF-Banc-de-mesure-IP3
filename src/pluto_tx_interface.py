import adi
from src.param import *

class PlutoTxInterface:
    def __init__(self, ip_addr):
        self.ip = ip_addr  # IP du Pluto TX.
        try: 
            self.sdr = adi.Pluto(self.ip)
            self.connected =  True
        except:
            self.connected =  False
        pass 
    
    def configure_tx(self, params: TxParams):
        self.sdr.sample_rate = params.fs
        self.sdr.tx_rf_bandwidth = params.fs
        self.sdr.tx_lo = params.f_rf
        self.sdr.tx_hardwaregain_chan0 = params.pe_dbm
        
    def load_waveform(self,signal_codes):
        self.sdr.tx_destroy_buffer()
        self.sdr.tx_cyclic_buffer = True
        self.sdr.tx(signal_codes)
    
    def stop_tx(self):
        self.sdr.tx_destroy_buffer()    

    def is_connected(self):
        return self.connected