# src/error_manager.py

class error_manager:
    """
    Centralized error/message manager.
    This class only formats messages; the GUI decides how to display them.
    """

    def __init__(self):
        # You can add global state or configuration here if needed
        pass

    def pluto_connection_error(self, exception: Exception) -> str:
        return f"[ERROR] Pluto SDR connection error: {exception}"

    def pluto_not_connected(self) -> str:
        return "[ERROR] Pluto SDR not connected"

    def tx_no_channel_selected(self) -> str:
        return "[ERROR] No channel selected for TX"

    def rx_invalid_params(self) -> str:
        return "[ERROR] Invalid RX parameters"

    def invalid_rf_or_power(self) -> str:
        return "[ERROR] Invalid RF frequency or power value"

    def invalid_rf(self) -> str:
        return "[ERROR] Invalid RF frequency value"

    def tx_pluto_not_connected(self) -> str:
        return "[ERROR] Impossible to send waveform on tx: Pluto not connected"

    def waveform_no_channel(self) -> str:
        return "[ERROR] No channel selected for waveform generation"
