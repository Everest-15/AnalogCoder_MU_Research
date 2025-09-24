from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Common-Gate Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supply
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply

# Input and Bias Voltage
circuit.V('in', 'Vin', circuit.gnd, "dc 1.0 ac 1u")
circuit.V('bias', 'Vbias', circuit.gnd, 1.5) # 1.5V for gate biasing

# Common-Gate Amplifier
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()

simulator_id = circuit.simulator()
mosfet_names = []
import PySpice.Spice.BasicElement
for element in circuit.elements:
    if isinstance(element, PySpice.Spice.BasicElement.Mosfet):
        mosfet_names.append(element.name)

mosfet_name_ids = []
for mosfet_name in mosfet_names:
    mosfet_name_ids.append(f"@{mosfet_name}[id]")

simulator_id.save_internal_parameters(*mosfet_name_ids)
analysis_id = simulator_id.operating_point()

id_correct = 1
for mosfet_name in mosfet_names:
    mosfet_id = float(analysis_id[f"@{mosfet_name}[id]"][0])
    if mosfet_id < 1e-5:
        id_correct = 0
        print("The circuit does not function correctly. "
          "the current I_D for {} is 0. ".format(mosfet_name)
          .format(mosfet_name))

if id_correct == 0:
    print("Please fix the wrong operating point.\n")
    sys.exit(2)


frequency = 100@u_Hz
analysis = simulator.ac(start_frequency=frequency, stop_frequency=frequency*10, 
    number_of_points=2, variation='dec')

import numpy as np

node = 'vout'
output_voltage = analysis[node].as_ndarray()[0]
gain = np.abs(output_voltage / (1e-6))

print(f"Voltage Gain (Av) at 100 Hz: {gain}")

required_gain = 1e-5
import sys
if gain > required_gain:
    print("The circuit functions correctly at 100 Hz.\n")
    sys.exit(0)
else:
    print("The circuit does not function correctly.\n"
          "the gain is less than 1e-5.\n"
          "Please fix the wrong operating point.\n")
    sys.exit(2)