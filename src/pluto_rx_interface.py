import adi
from iip3_bench import RxParams

class PlutoRxInterface:
    def __init__(self,ip_addr):
        self.ip = ip_addr  # IP du Pluto TX.
        try: 
            self.sdr = adi.Pluto(self.ip)
            self.connected =  True
        except:
            self.connected =  False
        self.current_fs: float
        self.current_lo: float
        self.current_pe: float
        pass 
    
    def configure_rx(self, params: RxParams):
        self.sdr.rx_lo = params.f_rf
        self.sdr.rx_rf_bandwidth = params.fs
        self.sdr.rx_buffer_size = params.n_sample
        self.sdr.gain_control_mode_chan0 = "manual"
        self.sdr.rx_hardwaregain_chan0 = params.g_rx_db

    def flush_buffers(self, n=10):  # boucle rx() pour vider.
        for _ in range(n):
            self.sdr.rx()   

    def receive(self, n_samples=None):
        if n_samples is not None:
            self.sdr.rx_buffer_size = n_samples
        return self.sdr.rx()

    def is_connected(self):
        return self.connected