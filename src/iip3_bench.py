from src.pluto_tx_interface import *
from src.pluto_rx_interface import *
from src.signal_utils import *
from src.param import *
from dataclasses import dataclass
from src.error_manager import ErrorManager
from src.Tx_calibration import TxCalibration


class IIP3Bench:
    def __init__(self, tx_iface, rx_iface, signal_utils, err_mgr: ErrorManager, calib: TxCalibration):
        # Core bench orchestrator: holds TX/RX interfaces, DSP utilities, logger and calibration
        self.tx_iface = tx_iface
        self.rx_iface = rx_iface
        self.signal_utils = signal_utils
        self.err_mgr = err_mgr
        self.calib = calib
        # Store last-used TX/RX parameters for subsequent operations
        self.current_tx_params: TxParams
        self.current_rx_params: RxParams
        pass

    def set_calibration(self, calib: TxCalibration):
        # Update the calibration table used for TX power correction
        self.calib = calib

    def _apply_tx_calibration(self, tx_params: TxParams) -> TxParams:
        """Return a copy of tx_params with TX power corrected using the calibration table."""
        if self.calib is None:
            # No calibration available, return original parameters
            return tx_params

        try:
            # Lookup correction based on user RF frequency and commanded power
            corr_db, f_ref, p_ref = self.calib.get_correction(
                f_rf_user=tx_params.f_rf,
                p_tx_user=tx_params.pe_dbm,
            )
        except ValueError as e:
            # Out of calibration table range: log error and keep original power
            self.err_mgr.error(str(e))
            return tx_params

        # Apply correction to commanded TX power
        pe_corr = tx_params.pe_dbm + corr_db
        self.err_mgr.info(
            f"Calibration TX: f={f_ref/1e6:.1f} MHz, P_cmd={tx_params.pe_dbm:.1f} dBm, "
        )
        self.err_mgr.info(
            f"correction={corr_db:+.1f} dBm → P_tx={pe_corr:.1f} dBm"
        )

        # Build a new TxParams instance with corrected power while preserving other fields
        return TxParams(
            f_rf=tx_params.f_rf,
            delta_f=tx_params.delta_f,
            fs=tx_params.fs,
            pe_dbm=pe_corr,
            n_sample=tx_params.n_sample,
        )

    def configure(self, tx_params, rx_params):
        # Store current TX/RX parameters and configure both Pluto devices
        self.current_tx_params = tx_params
        self.current_rx_params = rx_params

        # Configure TX if the interface is connected
        if self.tx_iface.is_connected():
            self.tx_iface.configure_tx(tx_params)

        # Configure RX if the interface is connected
        if self.rx_iface.is_connected():
            self.rx_iface.configure_rx(rx_params)
        pass

    def send_tx(self, tx_params=None):
        # Generate and send TX waveform, then compute theoretical spectrum for display
        # Use previously stored parameters if none are explicitly provided
        if tx_params is None:
            tx_params = self.current_tx_params
        if tx_params is None:
            self.err_mgr.error("TX params not configured before send_tx()")

        # Check that TX interface is available
        if not self.tx_iface.is_connected():
            self.err_mgr.error("Pluto TX not connected")
            return None, None

        # Apply TX calibration before waveform generation
        tx_corr = self._apply_tx_calibration(tx_params)
        if tx_corr.pe_dbm > 0:
            # Positive correction is unexpected; abort to avoid overdriving TX
            self.err_mgr.warning("Calibration correction is positive, which may indicate an issue.")
            return None, None, None, None

        # 1) Generate baseband two-tone signal and DAC codes
        # Convention: pe_dbm = power per tone, delta_f = spacing between the two tones
        # Generate signal using corrected TX power
        self.err_mgr.info(f"Generating two-tone signal: f_rf={tx_corr.f_rf:.3e} Hz, ")
        self.err_mgr.info(f"pe_dbm={tx_corr.pe_dbm:.1f} dBm, delta_f={tx_corr.delta_f:.1e} Hz, ")
        self.err_mgr.info(f"n_sample={tx_corr.n_sample}")
        signal_v, signal_codes = self.signal_utils.generate_two_tone_baseband(
            pe_dbm=tx_corr.pe_dbm,
            delta_f=tx_corr.delta_f,
            n_sample=tx_corr.n_sample,
        )

        # 2) Send waveform to Pluto TX
        if self.tx_iface.is_connected():
            # Reconfigure TX as a safety step, then load and start cyclic waveform
            self.tx_iface.configure_tx(tx_corr)  # security: reconfigure if needed
            self.tx_iface.load_waveform(signal_codes)
            self.err_mgr.info(
                f"TX started: f_rf={tx_params.f_rf:.3e} Hz, P={tx_params.pe_dbm:.1f} dBm"
            )

        # 3) Compute theoretical FFT from generated signal for visualization
        freq_abs, P_bin, P_dBm, A_sample = self.signal_utils.compute_fft(
            signal_v,
            tx_corr.fs,
            tx_corr.f_rf  # consistent with current SignalUtils design
        )

        return freq_abs, P_bin, P_dBm, A_sample

    def receive_rx(self, rx_params=None):
        # Capture RX samples using current or provided RX parameters
        # Use previously stored RX parameters if none are given
        if rx_params is None:
            rx_params = self.current_rx_params

        # Check that RX interface is available
        if not self.rx_iface.is_connected():
            self.err_mgr.error("Pluto RX not connected")
            return None

        if rx_params is None:
            # RX not configured before capture
            self.err_mgr.error("RX params not configured before receive_rx()")
            return None

        # Configure RX hardware with requested parameters
        self.rx_iface.configure_rx(rx_params)

        # Clear RX buffers to avoid leftover samples from previous captures
        self.rx_iface.flush_buffers(n=10)

        # Placeholders for potential spectrum accumulation (not used yet)
        acc_spec = None
        acc_freq = None

        # Capture raw RX samples from Pluto
        rx_samples = self.rx_iface.receive(n_samples=rx_params.n_sample)
        self.err_mgr.info(
            f"RX captured: f_rf={rx_params.f_rf:.3e} Hz, fs={rx_params.fs:.3e} Hz"
        )
        return rx_samples


@dataclass
class IIP3Result:
    # Container for a complete IIP3 measurement result set
    freq_tx: list[float]   # TX frequency axis (Hz)
    spec_tx: list[float]   # TX spectrum (dBm)
    freq_rx: list[float]   # RX frequency axis (Hz)
    spec_rx: list[float]   # RX spectrum (dBm)
    iip3_dbm: float        # Computed IIP3 value (dBm)
    delta_db: float        # Measured IM3 delta (dB)
    p1_avg_dbm: float      # Average carrier power (dBm)
