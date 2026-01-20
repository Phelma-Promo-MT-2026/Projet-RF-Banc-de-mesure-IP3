from src.pluto_tx_interface import *
from src.pluto_rx_interface import *
from src.signal_utils import *
from src.param import *
from dataclasses import dataclass
from src.error_manager import ErrorManager
from src.Tx_calibration import TxCalibration

class IIP3Bench :
    def __init__(self, tx_iface, rx_iface, signal_utils,err_mgr: ErrorManager, calib: TxCalibration):
        self.tx_iface =  tx_iface
        self.rx_iface =  rx_iface
        self.signal_utils =  signal_utils
        self.err_mgr = err_mgr
        self.calib = calib
        self.current_tx_params: TxParams
        self.current_rx_params: RxParams
        pass
    
    def set_calibration(self, calib: TxCalibration):
        self.calib = calib

    def _apply_tx_calibration(self, tx_params: TxParams) -> TxParams:
        """Retourne une copie de tx_params avec puissance corrigée."""
        if self.calib is None:
            return tx_params  # pas de calibration

        try:
            corr_db, f_ref, p_ref = self.calib.get_correction(
                f_rf_user=tx_params.f_rf,
                p_tx_user=tx_params.pe_dbm,
            )
        except ValueError as e:
            # hors abaque -> message d’erreur et on garde la valeur brute
            self.err_mgr.error(str(e))
            return tx_params

        pe_corr = tx_params.pe_dbm + corr_db
        self.err_mgr.info(
            f"Calibration TX: f={f_ref/1e6:.1f} MHz, P_cmd={tx_params.pe_dbm:.1f} dBm, "
            f"corr={corr_db:+.1f} dB → P_tx={pe_corr:.1f} dBm"
        )

        # crée un nouveau TxParams avec la puissance corrigée
        return TxParams(
            f_rf=tx_params.f_rf,
            delta_f=tx_params.delta_f,
            fs=tx_params.fs,
            pe_dbm=pe_corr,
            n_sample=tx_params.n_sample,
        )
        
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
        if tx_params is None:
            self.err_mgr.error("TX params not configured before send_tx()")

        if not self.tx_iface.is_connected():
            self.err_mgr.error("Pluto TX not connected")
            return None, None
        
        # applique la calibration
        tx_corr = self._apply_tx_calibration(tx_params)
        if tx_corr.pe_dbm > 0:
            self.err_mgr.warning("Calibration correction is positive, which may indicate an issue.")
            return None, None, None, None
        
        # 1) generate baseband two-tone signal and DAC codes
            # convention : pe_dbm = power per ton, delta_f = width between the 2 tons
        # génération du signal avec pe_dbm corrigé
        self.err_mgr.info(
            f"Generating two-tone baseband signal: f_rf={tx_corr.f_rf:.3e} Hz, "
            f"pe_dbm={tx_corr.pe_dbm:.1f} dBm, delta_f={tx_corr.delta_f:.1e} Hz, "
            f"n_sample={tx_corr.n_sample}"
        )
        signal_v, signal_codes = self.signal_utils.generate_two_tone_baseband(
            pe_dbm=tx_corr.pe_dbm,
            delta_f=tx_corr.delta_f,
            n_sample=tx_corr.n_sample,
        )

        
        # 2) Send to Pluto TX
        if self.tx_iface.is_connected():
            self.tx_iface.configure_tx(tx_corr) #ecurity : reconfigure if needed
            self.tx_iface.load_waveform(signal_codes)
            self.err_mgr.info(
                f"TX started: f_rf={tx_params.f_rf:.3e} Hz, P={tx_params.pe_dbm:.1f} dBm"
            )

        # 3) compute theoretical FFT for display
        freq_abs, P_bin, P_dBm, A_sample = self.signal_utils.compute_fft(
            signal_v,
            tx_corr.fs,
            tx_corr.f_rf  # cohérent avec SignalUtils actuel
        )

        return freq_abs, P_bin, P_dBm, A_sample

    def receive_rx(self,rx_params=None):
         #get rx_params or use current
        if rx_params is None:
            rx_params = self.current_rx_params
        if not self.rx_iface.is_connected():
            self.err_mgr.error("Pluto RX not connected")
            return None
        
        if rx_params is None:
            self.err_mgr.error("RX params not configured before receive_rx()")
            return None
        
        # Configure RX
        self.rx_iface.configure_rx(rx_params)
        
        # Clear buffers for avoiding leftovers
        self.rx_iface.flush_buffers(n=10)
        
        acc_spec = None
        acc_freq = None
        
        # Capture
        rx_samples = self.rx_iface.receive(n_samples=rx_params.n_sample)
        self.err_mgr.info(
            f"RX captured: f_rf={rx_params.f_rf:.3e} Hz, fs={rx_params.fs:.3e} Hz"
        )
        return rx_samples
    
@dataclass        
class IIP3Result:
    freq_tx     : list[float] # fréquences TX (Hz).
    spec_tx     : list[float] # spectre TX (dBm).
    freq_rx     : list[float] # fréquences RX (Hz).
    spec_rx     : list[float] # spectre RX (dBm).
    iip3_dbm    : float # IIP3 calculé (dBm).
    delta_db    : float # ΔIM3 mesuré (dB).
    p1_avg_dbm  : float # Puissance moyenne porteuse (dBm).