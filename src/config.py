from src.iip3_bench import *
# Import IIP3-related types (e.g., TxParams, RxParams) used in configuration utilities

PLUTO_TX_IP = "ip:192.168.2.10"
PLUTO_RX_IP = "ip:192.168.2.11"

def load_user_settings(path="settings.json"):
    """
    Load user-specific TX/RX settings from a JSON file.

    Currently returns default TxParams and RxParams instances and ignores the file.
    """
    return TxParams(), RxParams()

def load_pluto_spec(path="pluto_spec.json"):
    """
    Return a dictionary describing the allowed operating ranges of the Pluto SDR.

    The ranges include RF frequency, sampling rate, TX power and RX gain limits.
    The 'path' argument is reserved for a future implementation that might read
    these specifications from an external JSON file.
    """
    pluto_spec = {
        "f_min": 325e6,
        "f_max": 3.8e9,
        "fs_min": 1e6,
        "fs_max": 20e6,
        "pe_min": -90,
        "pe_max": 0,
        "g_rx_min": 0,
        "g_rx_max": 70
    }
    return pluto_spec 

def validate_params(Tx_params, rx_params, pluto_spec) :
    """
    Validate TX and RX parameters against the Pluto specification.

    This function is intended to check that frequencies, sample rates,
    TX power and RX gain are within the limits given by 'pluto_spec'.
    Currently not implemented.
    """
    pass