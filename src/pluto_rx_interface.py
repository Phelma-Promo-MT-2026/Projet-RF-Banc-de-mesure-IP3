import adi
from src.param import *


class PlutoRxInterface:
    def __init__(self, ip_addr):
        # Initialize Pluto SDR RX interface using given IP address
        self.ip = ip_addr  # IP address of the Pluto device
        try:
            # Try to create a Pluto SDR object; consider it connected if this succeeds
            self.sdr = adi.Pluto(self.ip)
            self.connected = True
        except:
            # On failure, mark device as not connected (no detailed error handling here)
            self.connected = False
        pass

    def configure_rx(self, params: RxParams):
        # Configure RX path according to provided RxParams
        self.sdr.rx_lo = params.f_rf                   # Set RX LO frequency (Hz)
        self.sdr.rx_rf_bandwidth = params.fs           # Set RF bandwidth equal to sampling rate
        self.sdr.rx_buffer_size = params.n_sample      # Number of samples per RX buffer
        self.sdr.gain_control_mode_chan0 = "manual"    # Disable AGC, use manual gain
        self.sdr.rx_hardwaregain_chan0 = params.g_rx_db  # Set manual RX gain (dB)

    def flush_buffers(self, n=10):
        # Flush RX buffers by performing multiple dummy reads
        for _ in range(n):
            self.sdr.rx()

    def receive(self, n_samples=None):
        # Receive a buffer of samples, optionally overriding buffer size
        if n_samples is not None:
            self.sdr.rx_buffer_size = n_samples
        return self.sdr.rx()

    def is_connected(self):
        # Return connection status of the Pluto SDR device
        return self.connected
