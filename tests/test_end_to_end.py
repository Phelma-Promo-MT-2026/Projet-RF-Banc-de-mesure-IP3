import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk

from src.pluto_interface import pluto_interface
from src.error_manager import error_manager

class test_tx_rx():

    def send_and_receive(self,f_rf, g, delta_f, fs, n_sample, pe):
        #----------------------------------------------#
        #---            Tx/rx from Pluto            ---#
        #----------------------------------------------#
        rx_signal = self.pluto.send_and_receive(f_rf, g, delta_f, fs, n_sample, pe)
        if(rx_signal is None):
            return None
        return rx_signal