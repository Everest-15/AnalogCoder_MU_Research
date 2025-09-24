from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Common-Gate Amplifier')
# Define the NMOS model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supply and Bias Voltage
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply
circuit.V('bias', 'Vbias', circuit.gnd, 1.0) # 1V bias voltage (= V_th + 0.5 = 0.5 + 0.5 = 1.0)

# Common-Gate Amplifier
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
