from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
circuit = Circuit('Single-Stage Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=50e-6, vto=0.5)
# Power Supply for the power
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply
# Single-Stage Common-Source Amplifier with Resistor Load
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vin', circuit.gnd, circuit.gnd, model='nmos_model', w=50e-6, l=1e-6)
circuit.R('R', 'Vout', 'Vdd', 1@u_kΩ)
# Analysis Part
simulator = circuit.simulator()
