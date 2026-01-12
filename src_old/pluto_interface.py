# ============================================================================
#  PlutoSDR interface (pyadi-iio / adi.Pluto)
#  Objet principal : sdr = adi.Pluto("ip:192.168.2.1")
# ============================================================================
# --- Méthodes principales de l’objet sdr ------------------------------------
# sdr.rx()
#   - Récupère un buffer d’échantillons complexes I/Q depuis le RX.
#   - Taille = rx_buffer_size, canaux = rx_enabled_channels. 
# sdr.tx(data)
#   - Envoie un vecteur ou une liste de vecteurs d’échantillons I/Q vers le TX.
#   - Canaux utilisés = tx_enabled_channels. 
# sdr.tx_destroy_buffer()
#   - Détruit le buffer TX courant.
#   - Obligatoire avant de changer les échantillons en mode tx_cyclic_buffer. 

# --- Propriétés RF courantes -------------------------------------------------
# sdr.sample_rate
#   - Fréquence d’échantillonnage globale (Hz). 
# sdr.rx_sample_rate / sdr.tx_sample_rate
#   - Fréquences d’échantillonnage séparées RX / TX (si supportées). 
# sdr.rx_lo / sdr.tx_lo
#   - Fréquences LO RX / TX (Hz). 
# sdr.rx_rf_bandwidth / sdr.tx_rf_bandwidth
#   - Largeur de bande RF des filtres (Hz). 
# sdr.rx_buffer_size
#   - Taille du buffer renvoyé par rx() (nombre d’échantillons complexes). 
# sdr.tx_cyclic_buffer
#   - Booléen, True => le Pluto rejoue en boucle le dernier buffer TX. 

# --- Propriétés de gain / AGC -----------------------------------------------
# sdr.gain_control_mode_chan0 / sdr.gain_control_mode_chan1
#   - Mode de contrôle de gain RX : "slow_attack", "fast_attack", "manual", etc. 
# sdr.rx_hardwaregain_chan0 / sdr.rx_hardwaregain_chan1
#   - Gain RF d’entrée RX (dB), utilisable en mode "manual". 
# sdr.tx_hardwaregain_chan0
#   - Atténuateur/gain RF TX (dB, souvent valeur négative pour atténuation). 

# --- Sélection de canaux -----------------------------------------------------
# sdr.rx_enabled_channels
#   - Liste des index de canaux RX activés (ex. [0] pour RX0 I/Q). 
# sdr.tx_enabled_channels
#   - Liste des index de canaux TX activés (ex. [0] pour TX0 I/Q). 

import adi
import numpy as np
import matplotlib.pyplot as plt
from src.error_manager import  error_manager
from src.utils         import  *
###################################################################
###         Manage communication TX/RX with ADALM-PLUTO         ###
###################################################################
interface_error = error_manager ()


class pluto_interface:   
    def __init__(self):  
        try:
            self.sdr = adi.Pluto("ip:192.168.2.1")
            self.pluto_connected = True
        except Exception as e:
            print("Pluto SDR connection error",e)
            self.sdr = None
            self.pluto_connected = False
        
        if self.pluto_connected:
            print(self.sdr._device_name)
        else:
            print("Pluto SDR not connected")
        self.tools = utils()
    #-------------------------------------------------------------
    #                  Send Signal to PLUTO by IIO
    #-------------------------------------------------------------
    

    def send_waveform(self, f_rf, delta_f, fs_pluto, n_sample, pe, I_enable, Q_enable):
        signal_v, signal_pluto = self.tools.generate_waveform_base_band(pe, delta_f, n_sample, I_enable, Q_enable)
        if signal_v is None :
            return 2
        if signal_pluto is None :
            return 2
        #-------------------------------------#
        #--         Pe correction           --#
        #-------------------------------------#
        # Corrective offset : 8dB + 1dB/800MHz
        #   * -3dB because we don't use the complexe part
        #   * -3dB because 2 tons generate around f_rf takes (pe/2) each
        #   * -2dB because of the implementation of the DAC on Pluto
        #   * -1dB/800MHz caracterize with 3 differents pluto between [800MHz;3.8GHz]
        """pe = pe + 8 + (f_rf/800e6)
        if(pe > 0):
            print("Warning: Power correction exceed max power of Pluto (0dBm)")
            pe = 0  # Max power Pluto is 0dBm"""
        #-------------------------------------#
        #--          SDR configuration      --#
        #-------------------------------------#
        if(self.pluto_connected == False):
            return 0
        '''
        if(I_enable == False and Q_enable == False):
            print("No channel selected for TX")
            return 
        elif(I_enable == True and Q_enable == False):
            self.sdr.tx_enabled_channels = [0]   # TX0 : I only
        elif(I_enable == False and Q_enable == True):       
            self.sdr.tx_enabled_channels = [1]   # TX1 : Q only
        elif(I_enable == True and Q_enable == True):
            self.sdr.tx_enabled_channels = [0, 1]   # TX0 & TX1 : I & Q
        '''
            
        self.sdr.sample_rate            = int(fs_pluto)    # Sample rate
        self.sdr.tx_rf_bandwidth        = int(fs_pluto)    # Filter cut frequency
        self.sdr.tx_lo                  = int(f_rf)        # Local oscillator frequency
        self.sdr.tx_hardwaregain_chan0  = pe               # Power tx : valid between -90dB and 0dB
        self.sdr.tx_destroy_buffer()
        self.sdr.tx_cyclic_buffer       = True       # Send sample unlimited time
        self.sdr.tx(signal_pluto)
        
        return 1
        
        
    #------------------------------------------------------------   -
    #               Recveid Signal from PLUTO by IIO
    #-------------------------------------------------------------
    def receive_waveform(self, f_rf, delta_f, fs_pluto, n_sample,g_rx):
        #-------------------------------------#
        #--          SDR configuration      --#
        #-------------------------------------#
        if(self.pluto_connected == False):
            print("Pluto SDR not connected")
            return
        self.sdr.rx_lo                      = int(f_rf)
        self.sdr.rx_rf_bandwidth            = int(fs_pluto)
        self.sdr.rx_buffer_size             = n_sample
        self.sdr.gain_control_mode_chan0    = 'manual'
        self.sdr.rx_hardwaregain_chan0      = g_rx # dB
        
        #clean RX buffer
        for i in range (0, 10):
            raw_data = self.sdr.rx()

        # Receive sample
        rx_samples = self.sdr.rx()
        
        return  rx_samples

    
    def spectrum_to_dBm(self, rx_samples, fs, f_rf):
        """
        Spectre en dBm par bin avec FFT centrée.
        Axe fréquence : absolu autour de f_rf.
        rx_samples : échantillons complexes issus de l'ADC (int16 ou float).
        """
        N = len(rx_samples)

        # FFT centrée et normalisée (sur les codes ADC bruts)
        X = np.fft.fftshift(np.fft.fft(rx_samples)) / N

        #X = np.fftshift(np.fft.fft(rx_samples)) / N
        
        A_sample = np.abs(X)
        # Puissance par bin en unités ADC^2
        P_bin = (np.abs(X) ** 2)/50       # réel

        # éviter log(0)
        P_bin_safe = P_bin.copy()
        P_bin_safe[P_bin_safe <= 0] = 1e-20

        P_dBm = 10 * np.log10(P_bin_safe)

        # Axe fréquence centré
        freq_base = np.fft.fftshift(np.fft.fftfreq(N, d=1.0 / fs))   # [-fs/2; +fs/2]
        #freq_base = np.fft.fftfreq(N, d=1.0 / fs)
        freq_abs  = freq_base + f_rf

        # On renvoie freq_abs (ou freq_base), P_bin réel et P_dBm
        return freq_abs, P_bin, P_dBm, A_sample