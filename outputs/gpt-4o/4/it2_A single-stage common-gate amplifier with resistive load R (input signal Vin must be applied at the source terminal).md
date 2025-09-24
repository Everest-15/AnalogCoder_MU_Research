### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin, Vbias for biasing and signal input

#### Common-Gate Amplifier with Resistive Load
1. **Transistor Setup**:
   - **M1** (NMOS) is the main amplifying transistor.
   - The source of **M1** is connected to the input node **Vin**.
   - The gate of **M1** is connected to a bias voltage **Vbias**.
   - The drain of **M1** is connected to the output node **Vout** through resistor **R1**.

2. **Biasing**:
   - **Vbias** is used to bias the gate of **M1**, ensuring it operates in the saturation region.
   - The bulk of **M1** is connected to its source to avoid body effect.

3. **Load Resistor (R1)**:
   - **R1** connects the drain of **M1** to **Vdd**. This resistor converts the current through **M1** into an output voltage.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Single-Stage Common-Gate Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supply for the power and input signal
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply
circuit.V('in', 'Vin', circuit.gnd, 1.0) # 1V input for bias voltage
circuit.V('bias', 'Vbias', circuit.gnd, 2.0) # 2V input for bias voltage (example value)

# Common-Gate Amplifier with Resistive Load
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

### Explanation:
- The NMOS transistor M1 is set up in a common-gate configuration, where the input signal is applied at the source terminal.
- The resistor R1 acts as the load and is connected between the drain of M1 and the power supply Vdd.
- The gate of M1 is biased with a fixed voltage Vbias to ensure the NMOS operates in the saturation region.
- The input node is Vin, and the output node is Vout, as specified.