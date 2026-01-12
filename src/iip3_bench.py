from src.pluto_tx_interface import *
from src.pluto_rx_interface import *
from src.signal_utils import *
from dataclasses import dataclass

class IIP3Bench :
    def __init__(self, tx_iface, rx_iface, signal_utils):
        self.tx_iface =  tx_iface
        self.rx_iface =  rx_iface
        self.signal_utils =  signal_utils
        self.current_tx_params: TxParams
        self.current_rx_params: RxParams
        pass
    
    def configure(self, tx_params, rx_params) : #stocke les paramètres et configure les 2 Pluto.
        # Mémorise les paramètres courants
        self.current_tx_params = tx_params
        self.current_rx_params = rx_params

        # Configure TX si connecté
        if self.tx_iface.is_connected():
            self.tx_iface.configure_tx(tx_params)

        # Configure RX si connecté
        if self.rx_iface.is_connected():
            self.rx_iface.configure_rx(rx_params)
        pass

    def send_tx(self, tx_params=None) :
        #get tx_params or use current
        if tx_params is None:
            tx_params = self.current_tx_params

        # 1) generate baseband two-tone signal and DAC codes
            # convention : pe_dbm = power per ton, delta_f = width between the 2 tons
        signal_v, signal_codes = self.signal_utils.generate_two_tone_baseband(
            pe_dbm=tx_params.pe_dbm,
            delta_f=tx_params.delta_f,
            n_sample=tx_params.n_sample,
        )

        # 2) Send to Pluto TX
        if self.tx_iface.is_connected():
            self.tx_iface.configure_tx(tx_params) #ecurity : reconfigure if needed
            self.tx_iface.load_waveform(signal_codes)
        else:
            # bring back error code
            return None, None

        # 3) compute theoretical FFT for display
        f_base, spec_base = self.signal_utils.compute_fft(
            signal_v,
            frequency=tx_params.delta_f  # cohérent avec SignalUtils actuel
        )

        return f_base, spec_base

    def receive_rx(self,rx_params=None):
         #get rx_params or use current
        if rx_params is None:
            rx_params = self.current_rx_params
        if not self.rx_iface.is_connected():
            return None
        
        # Configure RX
        self.rx_iface.configure_rx(rx_params)
        
        # Clear buffers for avoiding leftovers
        self.rx_iface.flush_buffers(n=10)
        
        # Capture
        rx_samples = self.rx_iface.receive(n_samples=rx_params.n_sample)
        return rx_samples
    
    def run_two_tone_measure(self, tx_params=None, rx_params=None):
        # 1) Use current params if none provided
        if tx_params is None:
            tx_params = self.current_tx_params
        if rx_params is None:
            rx_params = self.current_rx_params

        # 2) Configure the two Pluto
        self.configure(tx_params, rx_params)

        # 3) Send Tx + compute theoretical FFT of Tx (for display)
        f_tx, spec_tx = self.send_tx(tx_params)
        if f_tx is None:
            # Pluto TX not connected → empty return
            return IIP3Result([], [], [], [], 0.0, 0.0, 0.0)

        # 4) Receive real RX
        rx_samples = self.receive_rx(rx_params)
        if rx_samples is None:
            # Pluto RX not connected → empty return
            return IIP3Result([], [], [], [], 0.0, 0.0, 0.0)

        # 5) FFT RX
        f_rx, spec_rx = self.signal_utils.compute_fft(
            rx_samples,
            frequency=rx_params.fs / 4.0  # cohérent avec fs = 4*delta_f aujourd’hui
        )
        spec_rx_dbm = self.signal_utils.spectrum_to_dbm(spec_rx)

        # 6) Placeholder pour IIP3
        iip3_dbm = 0.0
        delta_db = 0.0
        p1_avg_dbm = 0.0

        return IIP3Result(
            freq_tx=f_tx.tolist(),
            spec_tx=spec_tx.tolist(),
            freq_rx=f_rx.tolist(),
            spec_rx=spec_rx_dbm.tolist(),
            iip3_dbm=iip3_dbm,
            delta_db=delta_db,
            p1_avg_dbm=p1_avg_dbm,
        )
        return IIP3Result()
    
@dataclass
class TxParams:
    f_rf    : float
    delta_f : float
    fs      : float
    pe_dbm  : float
    n_sample: int
        

@dataclass
class RxParams:
    f_rf    : float
    fs      : float
    n_sample: int
    g_rx_db : float

@dataclass        
class IIP3Result:
    freq_tx     : list[float] # fréquences TX (Hz).
    spec_tx     : list[float] # spectre TX (dBm).
    freq_rx     : list[float] # fréquences RX (Hz).
    spec_rx     : list[float] # spectre RX (dBm).
    iip3_dbm    : float # IIP3 calculé (dBm).
    delta_db    : float # ΔIM3 mesuré (dB).
    p1_avg_dbm  : float # Puissance moyenne porteuse (dBm).