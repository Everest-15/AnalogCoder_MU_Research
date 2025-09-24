### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin for input signal, Vbias for biasing

#### Common-Gate Amplifier with Resistor Load

1. **Transistor Setup**:
   - **M1** (NMOS) is used as the main amplifying transistor.
   - Source of **M1** is connected to the input node **Vin**.
   - Gate of **M1** is connected to the bias node **Vbias**.
   - Drain of **M1** is connected to the output node **Vout** through resistor **R1**.

2. **Biasing**:
   - **Vbias** is used to bias the gate of **M1**, ensuring it operates in the saturation region.

3. **Load and Output**:
   - **R1** is connected between the drain of **M1** and **Vdd**. This resistor acts as a load and converts the current through **M1** into an output voltage at **Vout**.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Single-Stage Common-Gate Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supply
circuit.V('dd', 'Vdd', circuit.gnd, 5.0)  # 5V power supply
circuit.V('bias', 'Vbias', circuit.gnd, 1.0)  # 1V bias voltage (= V_th + 0.5 = 0.5 + 0.5 = 1.0)

# Input Signal
circuit.V('in', 'Vin', circuit.gnd, 0.5)  # 0.5V input signal

# Common-Gate Amplifier
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This code sets up a single-stage common-gate amplifier with an NMOS transistor, using a resistive load. The source terminal is connected to the input signal, while the gate is biased to ensure proper operation. The drain is connected through a resistor to Vdd, and the output is taken from the drain.