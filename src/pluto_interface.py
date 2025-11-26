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
from error_manager import  error_manager

###################################################################
###         Manage communication TX/RX with ADALM-PLUTO         ###
###################################################################
interface_error = error_manager ()


class pluto_interface:   

    def __init__(self):   
        self.sdr = adi.Pluto("ip:192.168.2.1")
        self.sdr = adi.Pluto()
        #print(self.sdr._device_name)
        pass
    #-------------------------------------------------------------
    #                  Send Signal to PLUTO by IIO
    #-------------------------------------------------------------
    def send_waveform(self, f_rf, g, delta_f, fs, n_sample, pe):
        #-------------------------------------#
        #--- Parameter and error management --#
        #-------------------------------------#
        """
        interface_error.check_range(g       ,0,1,"gain")
        interface_error.check_range(f_rf    ,0,1,"RF frequency")
        interface_error.check_range(delta_f ,0,1,"Δf for 2 ton around f_rf")
        interface_error.check_range(fs      ,0,1,"Sample rate")
        interface_error.check_range(n_sample,0,1,"Sample number") 
        interface_error.check_range(pe      ,0,1,"Tx power")
        """
        #-------------------------------------#
        #--          SDR configuration      --#
        #-------------------------------------#
        self.sdr.sample_rate            = int(fs)    # Sample rate
        self.sdr.tx_rf_bandwidth        = int(fs)    # Filter cut frequency
        self.sdr.tx_lo                  = int(f_rf)  # Local oscillator frequency
        self.sdr.tx_hardwaregain_chan0  = pe    # Power tx : valid between -90dB and 0dB
        #-------------------------------------#
        #--       Signal Configuration      --#
        #-------------------------------------#
        t = np.linspace(0,1/fs,n_sample)
        signal = g*np.exp(2j*np.pi*(delta_f)*t)
        signal *=2**14                              # PLUTO SDR need sample between [-2^14;+2^14], not [-1;+1]
        
        ########################################
        self.sdr.tx_cyclic_buffer       = True       # Send sample unlimited time
        self.sdr.tx(signal)
        

        
    #------------------------------------------------------------   -
    #               Recveid Signal from PLUTO by IIO
    #-------------------------------------------------------------
    def receive_waveform(self, f_rf, g, delta_f, fs, n_sample):
        #-------------------------------------#
        #--- Parameter and error management --#
        #-------------------------------------#
        
        #-------------------------------------#
        #--          SDR configuration      --#
        #-------------------------------------#
        self.sdr.rx_lo                      = int(f_rf)
        self.sdr.rx_rf_bandwidth            = int(fs)
        self.sdr.rx_buffer_size             = n_sample
        self.sdr.gain_control_mode_chan0    = 'manual'
        self.sdr.rx_hardwaregain_chan0      = 0.0 # dB, augmenter pour augmenter le gain de réception, mais attention à ne pas saturer le CAN
        
        for i in range (0, 10):
            raw_data = self.sdr.rx()

        # Recevoir des échantillons
        rx_samples = self.sdr.rx()
        print(rx_samples)

        # Arrêter la transmission
        self.sdr.tx_destroy_buffer()

        # Calculer la densité spectrale de puissance (version du signal dans le domaine de la fréquence)
        psd = np.abs(np.fft.fftshift(np.fft.fft(rx_samples)))**2
        psd_dB = 10*np.log10(psd)
        f = np.linspace(fs/-2, fs/2, len(psd))

        # Tracer le domaine temporel
        plt.figure(0)
        plt.plot(np.real(rx_samples[::100]))
        plt.plot(np.imag(rx_samples[::100]))
        plt.xlabel("temps")

        # Tracer le domaine freq
        plt.figure(1)
        plt.plot(f/1e6, psd_dB)
        plt.xlabel("Frequences [MHz]")
        plt.ylabel("DSP")
        plt.show()
        pass
    
    
