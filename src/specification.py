class specification:
    
     def __init__(self, verbose=True):
        self.verbose = verbose
        
        #-------------------------------------#
        #---        Parameter general       --#
        #-------------------------------------#
        self.channel_bw_min = 200e3
        self.channel_bw_max = 56e6
        
        #-------------------------------------#
        #---        Parameter for tx        --#
        #-------------------------------------#
        self.tx_rf_min = 47e6
        self.tx_rf_max = 6e9
        self.tx_power_min = -90
        self.tx_power_max = 0
        
        #-------------------------------------#
        #---        Parameter for rx        --#
        #-------------------------------------#
        self.rx_rf_max = 70e6
        self.rx_rf_min = 6e9
        self.rx_power_min = -90
        self.rx_power_max = 0
        