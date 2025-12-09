'''
Projet      : Banc_test_IP3
A propos    : 
- class pluto_interface pour piloter facilement le dispositif ADALM-PLUTO (analog device)
- transmettre un signal RF 1 ton ou 2 ton : sélection des fréquences, puissance)
- recevoir un signal RF

Auteur      : Sacha Lutoff
Date        : 17/10/2025

'''

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
        self.tool = utils()
    #-------------------------------------------------------------
    #                  Send Signal to PLUTO by IIO
    #-------------------------------------------------------------
    

    def send_waveform(self, f_rf, g, delta_f, fs, n_sample, pe):
        signal = self.tool.generate_waveform_base_band(g, delta_f, fs, n_sample)
        #-------------------------------------#
        #--          SDR configuration      --#
        #-------------------------------------#
        if(self.pluto_connected == False):
            print("Pluto SDR not connected")
            return
        self.sdr.sample_rate            = int(fs)    # Sample rate
        self.sdr.tx_rf_bandwidth        = int(fs)    # Filter cut frequency
        self.sdr.tx_lo                  = int(f_rf)  # Local oscillator frequency
        self.sdr.tx_hardwaregain_chan0  = pe    # Power tx : valid between -90dB and 0dB
        self.sdr.tx_destroy_buffer()
        self.sdr.tx_cyclic_buffer       = True       # Send sample unlimited time
        self.sdr.tx(signal)
        
        
    #------------------------------------------------------------   -
    #               Recveid Signal from PLUTO by IIO
    #-------------------------------------------------------------
    def receive_waveform(self, f_rf, g, delta_f, fs, n_sample):
        #-------------------------------------#
        #--          SDR configuration      --#
        #-------------------------------------#
        if(self.pluto_connected == False):
            print("Pluto SDR not connected")
            return
        self.sdr.rx_lo                      = int(f_rf)
        self.sdr.rx_rf_bandwidth            = int(fs)
        self.sdr.rx_buffer_size             = n_sample
        self.sdr.gain_control_mode_chan0    = 'manual'
        self.sdr.rx_hardwaregain_chan0      = 0.0 # dB, augmenter pour augmenter le gain de réception, mais attention à ne pas saturer le CAN
        
        #clean RX buffer
        for i in range (0, 10):
            raw_data = self.sdr.rx()

        # Receive sample
        rx_samples = self.sdr.rx()
        print(rx_samples)
        return rx_samples
           
    
    def send_and_receive(self, f_rf, g, delta_f, fs, n_sample, pe):
        if(self.pluto_connected == False):
            print("Pluto SDR not connected")
            return
        self.sdr.tx_destroy_buffer()
        self.send_waveform(f_rf, g, delta_f, fs, n_sample, pe)     
        rx_signal = self.receive_waveform(f_rf, g, delta_f, fs, n_sample)
        self.sdr.tx_destroy_buffer()
        return rx_signal