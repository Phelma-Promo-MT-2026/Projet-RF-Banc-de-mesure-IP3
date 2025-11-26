from pluto_interface import pluto_interface
from error_manager import  error_manager
from gui import main_window
#from signal_processing import compute_fft
#from ip3_calculation import compute_ip3
#from visualization import plot_spectrum
#import config
    
def main():
    ###################################################################
    ###                         LOAD GUI                            ###
    ###################################################################
        app = main_window()
        app.mainloop()
        
    ###################################################################
    ###                       DATA TREATMENT                        ###
    ###################################################################
    #spectrum = compute_fft(data)
    #ip3_value = compute_ip3(spectrum)

    #plot_spectrum(spectrum, ip3_value)


  
if __name__ == "__main__":
    main()