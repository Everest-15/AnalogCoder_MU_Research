### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin for signal input

#### Common-Source Amplifier with Resistor Load
1. **Transistor Setup**:
   - **M1** (NMOS) as the main amplifying transistor.
   - Gate of **M1** is connected to the input node **Vin**.
   - Source of **M1** connected to the ground.
   - Drain of **M1** connected to **Vout** through resistor **R**.

2. **Load**:
   - Resistor **R** connects the drain of **M1** to **Vdd**. This resistor converts the current through **M1** into an output voltage.

### Task 2

```python
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
```