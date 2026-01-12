
import tkinter as tk
from src.iip3_bench import *

class MainWindow:
    def __init__(self):
        self.bench: IIP3Bench # contrôleur métier.
        self.delta_f: float # fréquence de décalage baseband.
        self.fs_pluto: float # fréquence d’échantillonnage RF (TX/RX):.
        self.n_sample: int # nombre d’échantillons.
        self.f_rf: float # fréquence RF centrale.
        self.pe: float # puissance TX demandée (dBm):.
        self.g_rx: float # gain RX demandé (dB):.
        self.fig_tx, self.ax_tx # figure/axe matplotlib TX.
        self.fig_rx, self.ax_rx # figure/axe matplotlib RX.
        #self.log: Log # gestionnaire de messages UI.
        pass

    def open_parameter_window(): # ouvre la fenêtre de paramètres avancés
        pass
    
    def update_entries_from_params(): # synchro GUI ↔ attributs.
        pass
    
    def send_tx(): # lit GUI → appelle bench.send_tx(tx_params):, affiche TX attendu.
        pass
    
    def receive_rx(): # lit GUI → appelle bench.receive_rx(rx_params):, affiche RX + IIP3.
        pass
    
    def run_tx_rx(): # séquence complète: TX + RX + calcul IIP3.
        pass
    
    def generate_fft_local(): # FFT théorique à partir de signal_utils (sans Pluto):.
        pass
    
    def display_spectrum_tx(x, y): # trace TX.
        pass
    
    def display_spectrum_rx(x, y): # trace RX.
        pass
    
    def clear_log_messages(): # efface le log.
        pass
    
    def on_close(): # ferme proprement matplotlib + Tk.
        pass
    
class ParameterWindow:

    def __init__(self,parent) :# construit les champs.
        self.parent: MainWindow # fenêtre principale.
        #Widgets: entry_delta_f, entry_n_sample, entry_f_sample, entry_f_rf, entry_pe, entry_g_rx
        pass
        
    def _read_fields() :# lit les entrées, renvoie un dict typé.
        pass
    def apply_and_close(): # applique dans parent puis détruit la fenêtre.
        pass
    def save_defaults(): # écrit dans settings.json.
        pass
    def on_close(): # applique puis ferme (croix).
        pass