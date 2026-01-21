import adi
from src.param import *

class PlutoTxInterface:
    def __init__(self, ip_addr):
        # Initialize Pluto SDR TX interface using the given IP address
        self.ip = ip_addr  # IP address of the Pluto TX device
        try:
            # Try to create a Pluto SDR object; mark as connected if this succeeds
            self.sdr = adi.Pluto(self.ip)
            self.connected = True
        except:
            # On failure, mark device as not connected (no detailed error handling here)
            self.connected = False
        pass

    def configure_tx(self, params: TxParams):
        # Configure TX path according to provided TxParams
        self.sdr.sample_rate = params.fs           # Set DAC sample rate (Hz)
        self.sdr.tx_rf_bandwidth = params.fs       # Set TX RF bandwidth equal to sample rate
        self.sdr.tx_lo = params.f_rf               # Set TX LO frequency (Hz)
        self.sdr.tx_hardwaregain_chan0 = params.pe_dbm  # Set TX output power (dB scale)

    def load_waveform(self, signal_codes):
        # Load a waveform into TX buffer and start cyclic transmission
        self.sdr.tx_destroy_buffer()      # Clear any previous TX buffer
        self.sdr.tx_cyclic_buffer = True  # Repeat the waveform continuously
        self.sdr.tx(signal_codes)         # Send waveform samples to the TX path

    def stop_tx(self):
        # Stop transmission by destroying the TX buffer
        self.sdr.tx_destroy_buffer()

    def is_connected(self):
        # Return connection status of the Pluto SDR device
        return self.connected
