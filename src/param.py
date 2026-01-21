from dataclasses import dataclass
@dataclass
class TxParams:
    # Parameters for TX path configuration and waveform generation
    f_rf: int       # RF carrier frequency in Hz
    delta_f: int    # Tone spacing for two-tone tests in Hz
    fs: int         # Sampling rate in Hz
    pe_dbm: int     # Output power per tone in dBm
    n_sample: int   # Number of samples in the generated waveform


@dataclass
class RxParams:
    # Parameters for RX path configuration and sample acquisition
    f_rf: int       # RF center frequency in Hz
    fs: int         # Sampling rate in Hz
    n_sample: int   # Number of samples to capture
    g_rx_db: int    # RX gain setting in dB
