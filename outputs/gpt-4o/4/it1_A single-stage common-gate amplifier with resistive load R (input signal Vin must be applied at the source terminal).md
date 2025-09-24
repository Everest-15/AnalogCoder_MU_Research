### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin, Vbias for biasing and signal input

#### Single-Stage Common-Gate Amplifier with Resistor Load

1. **Transistor Setup**:
   - **M1** (NMOS) as the main amplifying transistor.
   - Source of **M1** is connected to the input node **Vin**.
   - Gate of **M1** is connected to **Vbias** to set the DC operating point.
   - Drain of **M1** is connected to **Vout** through resistor **R1**.

2. **Load and Biasing**:
   - **R1** connects the drain of **M1** to **Vdd**. This resistor converts the current through **M1** into an output voltage.
   - **Vbias** is used to bias the gate of **M1**, ensuring it operates in the saturation region.

3. **Biasing Considerations**:
   - **Vbias** should be set to a value that ensures **M1** is properly biased in the active region. Typically, **Vbias** is slightly above the threshold voltage of the NMOS.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Common-Gate Amplifier')

# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supply
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply

# Input Biasing
circuit.V('bias', 'Vbias', circuit.gnd, 1.0) # 1V input for bias voltage (= V_th + 0.5 = 0.5 + 0.5 = 1.0)

# Common-Gate Amplifier
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This design sets up a common-gate amplifier using an NMOS transistor with a resistive load. The input is applied at the source, and the gate bias is set to ensure the transistor operates in the active region. The output is taken at the drain, with the resistor converting the current to a voltage.