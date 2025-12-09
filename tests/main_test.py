from tests.test_pluto_tx    import *
from tests.test_end_to_end  import *
from tests.test_pluto_rx    import *
from tests.test_end_to_end  import *
from tests.test_utils       import *
class main_window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # === Parameter declaration ===
        self.tx = test_tx()
        self.rx = test_rx()
        self.tx_rx = test_tx_rx()
        self.utils = utils()
        # === Main windows ===
        self.title("PlutoSDR Signal Generator GUI")
        self.geometry("1000x600")

        # === Set template ===
        frame_left = ttk.Frame(self, padding=10)
        frame_left.pack(side="left", fill="y")

        frame_right = ttk.Frame(self, padding=10)
        frame_right.pack(side="right", expand=True, fill="both")

        # === User fields ===
        ttk.Label(frame_left, text="Power Tx (dB):").pack(anchor="w")
        self.entry_power = ttk.Entry(frame_left)
        self.entry_power.insert(0, "-20")
        self.entry_power.pack(fill="x")

        ttk.Label(frame_left, text="Delta f (Hz):").pack(anchor="w")
        self.entry_delta_f = ttk.Entry(frame_left)
        self.entry_delta_f.insert(0, "10e6")
        self.entry_delta_f.pack(fill="x")

        ttk.Label(frame_left, text="Frequency RF (Hz):").pack(anchor="w")
        self.entry_rf = ttk.Entry(frame_left)
        self.entry_rf.insert(0, "2.4e9")
        self.entry_rf.pack(fill="x")

        ttk.Label(frame_left, text="Sample Frequency (Hz):").pack(anchor="w")
        self.entry_fs = ttk.Entry(frame_left)
        self.entry_fs.insert(0, "1e6")
        self.entry_fs.pack(fill="x")

        ttk.Label(frame_left, text="Gain:").pack(anchor="w")
        self.entry_gain = ttk.Entry(frame_left)
        self.entry_gain.insert(0, "1")
        self.entry_gain.pack(fill="x")

        ttk.Label(frame_left, text="Sample number:").pack(anchor="w")
        self.entry_N = ttk.Entry(frame_left)
        self.entry_N.insert(0, "10000")
        self.entry_N.pack(fill="x")

        # === Buttons ===
        ttk.Button(frame_left, text="Generate signal on tx" , command=self.send).pack(pady=20)
        ttk.Button(frame_left, text="Receive signal on rx"  , command=self.send_receive).pack(pady=20)
        ttk.Button(frame_left, text="General tx / Receiv rx", command=self.send_receive).pack(pady=20)  
        ttk.Button(frame_left, text="Generate fft"          , command=self.generate_fft).pack(pady=20)  
        # === Spectrum ===
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def on_close(self):
        plt.close('all')      # ferme proprement les figures Matplotlib
        self.destroy()        # détruit la fenêtre Tkinter
        self.quit()           # sort de la boucle mainloop
        
    def send(self): 
        try:
            f_rf     = int(float(self.entry_rf.get()))
            g        = int(float(self.entry_gain.get()))
            delta_f  = int(float(self.entry_delta_f.get()))
            fs       = int(float(self.entry_fs.get()))
            n_sample = int(float(self.entry_N.get()))  
            pe       = int(float(self.entry_power.get())) 
        except ValueError:
            print("Erreur : une des valeurs saisies est invalide.")
            return
        self.tx.send_signal_to_pluto(f_rf, g, delta_f, fs, n_sample, pe)
    
    def receive(self): 
        try:
            f_rf     = int(float(self.entry_rf.get()))
            g        = int(float(self.entry_gain.get()))
            delta_f  = int(float(self.entry_delta_f.get()))
            fs       = int(float(self.entry_fs.get()))
            n_sample = int(float(self.entry_N.get()))  
            pe       = int(float(self.entry_power.get())) 
        except ValueError:
            print("Erreur : une des valeurs saisies est invalide.")
            return
        rx_signal = self.tx_rx.receive_signal_from_pluto(f_rf, g, delta_f, fs, n_sample, pe)
        if(rx_signal is None):
            return None
        self.rx.display_fft(rx_signal, fs, n_sample,f_rf,delta_f)
                
    def send_receive(self): 
        try:
            f_rf     = int(float(self.entry_rf.get()))
            g        = int(float(self.entry_gain.get()))
            delta_f  = int(float(self.entry_delta_f.get()))
            fs       = int(float(self.entry_fs.get()))
            n_sample = int(float(self.entry_N.get()))  
            pe       = int(float(self.entry_power.get())) 
        except ValueError:
            print("Erreur : une des valeurs saisies est invalide.")
            return
        rx_signal = self.tx_rx.send_and_receive(f_rf, g, delta_f, fs, n_sample, pe)
        if(rx_signal is None):
            return None
        self.tx_rx.display_fft(rx_signal, fs, n_sample,f_rf,delta_f)
        
    def generate_fft(self): 
        try:
            g        = int(float(self.entry_gain.get()))
            delta_f  = int(float(self.entry_delta_f.get()))
            fs       = int(float(self.entry_fs.get()))
            n_sample = int(float(self.entry_N.get()))  
        except ValueError:
            print("Erreur : une des valeurs saisies est invalide.")
            return
        self.utils.test_fft_calculation_base_band(g, delta_f, fs, n_sample)        
def main():
        app = main_window()
        app.mainloop()

  
if __name__ == "__main__":
    main()