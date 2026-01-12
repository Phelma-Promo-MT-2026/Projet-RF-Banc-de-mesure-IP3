import pyvisa
import sys
from src_old.pluto_interface import *

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

    f = float(inst.query("CALC:MARK1:X?"))
    p = float(inst.query("CALC:MARK1:Y?"))
    print(f"Measured peak at {f/1e6:.3f} MHz with power {p:.2f} dBm")
    #return f, p
    return

if __name__ == "__main__":
    inst = open_ms2840a()

    pluto = pluto_interface()
    return_code = pluto.send_waveform(2.4e9,1e6,4e6,4096,-10,True,False)
    measure_peak(inst, 2.4e9, 2e6, 25e3)
    #f, p = measure_peak(inst, 2.4e9, 2e6, 100e3)
    
    #print(f"Pic à {f/1e6:.3f} MHz, {p:.2f} dBm")
