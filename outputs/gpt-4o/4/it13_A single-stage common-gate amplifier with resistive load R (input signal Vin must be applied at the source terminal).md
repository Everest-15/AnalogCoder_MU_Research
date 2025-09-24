### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin, Vbias for biasing and signal input
- **Capacitors**: Not specified but can be included for coupling and bypass applications if required

#### Common-Gate Amplifier with Resistor Load
1. **Transistor Setup**:
   - **M1** (NMOS) is the main amplifying transistor.
   - **Vin** is applied to the source of **M1**.
   - The gate of **M1** is connected to **Vbias** to set the operating point.
   - The drain of **M1** is connected to **Vout** through resistor **R1**.

2. **Biasing**:
   - **Vbias** is used to bias the gate of **M1**, ensuring it operates in the saturation region.

3. **Load and Output**:
   - **R1** connects the drain of **M1** to **Vdd**. This resistor converts the current through **M1** into an output voltage.
   - The output voltage **Vout** is taken from the drain of **M1**.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Single-Stage Common-Gate Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supplies for the power and input signal
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply
circuit.V('in', 'Vin', circuit.gnd, 1.0) # 1V input for bias voltage (= V_th + 0.5 = 0.5 + 0.5 = 1.0)
circuit.V('bias', 'Vbias', circuit.gnd, 2.0) # 2V input for bias voltage

# Common-Gate Amplifier
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This design outlines a single-stage common-gate amplifier with a resistive load, where the input signal is applied at the source terminal of the NMOS transistor. The circuit is biased appropriately to ensure the NMOS operates in the saturation region, and the output is taken from the drain of the transistor.