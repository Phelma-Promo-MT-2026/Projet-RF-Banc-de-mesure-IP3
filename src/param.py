from dataclasses import dataclass

@dataclass
class TxParams:
    f_rf: int
    delta_f: int
    fs: int
    pe_dbm: int
    n_sample: int

@dataclass
class RxParams:
    f_rf: int
    fs: int
    n_sample: int
    g_rx_db: int
