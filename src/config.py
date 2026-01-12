
from src.iip3_bench import *

PLUTO_TX_IP = "ip:192.168.2.10"
PLUTO_RX_IP = "ip:192.168.2.11"

def load_user_settings(path="settings.json"):
    return TxParams(), RxParams()

def load_pluto_spec(path="pluto_spec.json"):
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

def validate_params(Tx_params, rx_params, pluto_spec) : #– vérifie f_min, f_max, etc.
    pass