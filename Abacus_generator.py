import pyvisa
import sys
import time
import csv
import numpy as np  # For linspace/arange
from src import signal_utils
from src.param import *
from src.pluto_tx_interface import PlutoTxInterface

# Configurable parameters
FREQ_START = 400e6      # Start frequency (Hz)
FREQ_END = 3.4e9        # End frequency (Hz)
FREQ_STEP = 100e6       # Frequency step (Hz) → generates [800M, 1G, 1.2G, ..., 2.4G]
POWER_START = -30       # Start power (dBm)
POWER_END = 0         # End power (dBm)
POWER_STEP = 1          # Power step (dBm) → generates [-20, -15]
SPAN = 2e6              # Span in Hz
RBW = 25e3              # RBW in Hz
FILENAME = 'pluto_characterization.csv'
STABILIZATION_DELAY = 0.1 # Delay after waveform transmission (s)

def open_ms2840a():
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource("TCPIP0::Anritsu-MS2840A::inst0::INSTR")
    inst.timeout = 5000
    inst.write("SYST:LANG SCPI")
    print(inst.query("*IDN?"))
    return inst

def measure_peak(inst, f_center, span, rbw):
    inst.write(f"SENSE:FREQUENCY:CENTER {f_center}")
    inst.write(f"SENSE:FREQUENCY:SPAN {span}")
    inst.write(f"SENSE:BANDWIDTH:RESOLUTION {rbw}")
    inst.write("INIT:CONT OFF")
    inst.write("INIT:IMM")
    inst.query("*OPC?")
    inst.write("CALC:MARK1:STATE ON")
    inst.write("CALC:MARK1:MAX")
    p = float(inst.query("CALC:MARK1:Y?"))
    f_peak = float(inst.query("CALC:MARK1:X?"))
    print(f"Peak at {f_peak/1e6:.3f} MHz: {p:.2f} dBm")
    return p

def wait_for_enter():
    input("Press Enter to continue...")

if __name__ == "__main__":
    inst = open_ms2840a()
    
    # Generate frequency and power arrays from start/end/step
    frequencies = np.arange(FREQ_START, FREQ_END + FREQ_STEP/2, FREQ_STEP)  # Inclusive end
    powers = np.arange(POWER_START, POWER_END + POWER_STEP/2, POWER_STEP)
    
    print(f"Frequencies: {len(frequencies)} points from {frequencies[0]/1e9:.1f} to {frequencies[-1]/1e9:.1f} GHz")
    print(f"Powers: {len(powers)} levels from {powers[0]} to {powers[-1]} dBm")
    
    # Initialize CSV header
    with open(FILENAME, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        header = ['Frequency (Hz)'] + [str(int(p)) for p in powers]  # -20, -15
        writer.writerow(header)
    
    # Dictionary to store results: {freq: {p_tx: p_meas}}
    results = {f: {p: None for p in powers} for f in frequencies}
    
    tx_iface = PlutoTxInterface("ip:192.168.2.1")
    utils = signal_utils.SignalUtils()
    
    # Loop: for each power, measure all frequencies
    for p_tx in powers:
        print(f"\n--- TX Power: {p_tx:.0f} dBm ---")
        for f_center in frequencies:
            print(f"Frequency: {f_center/1e9:.3f} GHz")
            
            # Generate and transmit two-tone signal
            tx_params = TxParams(
                f_rf    =int(f_center),
                delta_f =int(1e6),
                fs      =int(4e6),
                pe_dbm  =int(p_tx),
                n_sample=int(4096),
            )
            signal_v, signal_codes = utils.generate_two_tone_baseband(
                pe_dbm=tx_params.pe_dbm,
                delta_f=tx_params.delta_f,
                n_sample=tx_params.n_sample,
            )
            tx_iface.configure_tx(tx_params)
            tx_iface.load_waveform(signal_codes)
            
            time.sleep(STABILIZATION_DELAY)
            p_meas = measure_peak(inst, f_center, SPAN, RBW)
            
            # Store in dictionary
            results[f_center][p_tx] = p_meas
            
            # Visual verification pause
            #wait_for_enter()
    
    # FINAL WRITE: complete table
    with open(FILENAME, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for f_center in frequencies:
            row = [f_center] + [results[f_center][p] for p in powers]
            writer.writerow(row)
    
    print(f"Complete table ({len(frequencies)}x{len(powers)}) saved to {FILENAME}")
    inst.close()
