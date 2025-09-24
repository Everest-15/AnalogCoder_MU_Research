### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin for the input signal, Vbias for biasing
- **Capacitors**: Not specified but can be included for coupling and bypass applications if required

#### Common-Gate Amplifier with Resistor Load
1. **Transistor Setup**:
   - **M1** (NMOS) is configured as the amplifying transistor in a common-gate configuration.
   - The gate of **M1** is connected to the bias voltage **Vbias**.
   - The source of **M1** is connected to the input node **Vin**.
   - The drain of **M1** is connected to the output node **Vout**.

2. **Biasing**:
   - **Vbias** is used to set the gate voltage of **M1** to ensure it operates in the saturation region.
   - The bias voltage should be set to a value that allows the transistor to remain in saturation for the expected input signal range.

3. **Load and Coupling**:
   - **R1** is connected between the drain of **M1** and **Vdd**. This resistor converts the current through **M1** into an output voltage at **Vout**.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Single-Stage Common-Gate Amplifier')

# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supply
circuit.V('dd', 'Vdd', circuit.gnd, 5.0)  # 5V power supply

# Biasing Voltage
circuit.V('bias', 'Vbias', circuit.gnd, 1.5)  # 1.5V bias voltage (Vbias > Vth)

# Input Signal
circuit.V('in', 'Vin', circuit.gnd, 1.0)  # 1V input signal

# Common-Gate Amplifier
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)

# Load Resistor
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This code sets up a single-stage common-gate amplifier with an NMOS transistor and a resistive load. The input signal is applied at the source of the NMOS, while the gate is connected to a bias voltage, ensuring proper operation in the saturation region. The output is taken from the drain of the NMOS, connected through a resistor to Vdd.