### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin for the input signal, Vbias for biasing
- **Capacitors**: Not specified but can be included for coupling and bypass applications if required

#### Single-Stage Common-Gate Amplifier with Resistor Load
1. **Transistor Setup**:
   - **M1** (NMOS) is the main amplifying transistor.
   - Gate of **M1** is connected to the bias voltage **Vbias**.
   - Source of **M1** is connected to the input node **Vin**.
   - Drain of **M1** is connected to the output node **Vout** through the resistor **R1**.

2. **Biasing**:
   - **Vbias** is used to bias the gate of **M1**, ensuring it operates in the saturation region.
   - **Vin** provides the input signal to the source of **M1**.

3. **Load Resistor (R1)**:
   - **R1** is connected between the drain of **M1** and **Vdd**.
   - This resistor converts the current through **M1** into an output voltage.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Single-Stage Common-Gate Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supply
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply
circuit.V('bias', 'Vbias', circuit.gnd, 1.5) # 1.5V bias voltage (Vth + 1.0 = 0.5 + 1.0 = 1.5)

# Input Signal
circuit.V('in', 'Vin', circuit.gnd, 0.0) # DC input for operating point

# Common-Gate Amplifier
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=100e-6, l=1e-6)

# Load Resistor
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This setup provides a common-gate amplifier with a resistive load, where the input is applied to the source, and the output is taken from the drain. The gate is biased to ensure the transistor operates in the desired region.