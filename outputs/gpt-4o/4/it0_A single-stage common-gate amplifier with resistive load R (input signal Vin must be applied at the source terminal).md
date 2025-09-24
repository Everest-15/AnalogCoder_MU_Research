### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin, Vbias for biasing and signal input

#### Common-Gate Amplifier with Resistive Load

1. **Transistor Setup**:
   - **M1** (NMOS) as the main amplifying transistor.
   - Source of **M1** is connected to the input node **Vin**.
   - Gate of **M1** is connected to the bias voltage **Vbias**.
   - Drain of **M1** is connected to the output node **Vout**.

2. **Biasing**:
   - **Vbias** is used to bias the gate of **M1**, ensuring it operates in the saturation region.

3. **Load**:
   - **R1**, a resistor, is connected between the drain of **M1** and **Vdd**. This resistor serves as the load for the amplifier, converting the current through **M1** into an output voltage.

4. **Output**:
   - The output voltage **Vout** is taken from the drain of **M1**.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Common-Gate Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supplies for the power and input signal
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply
circuit.V('in', 'Vin', circuit.gnd, 1.0) # 1V input for bias voltage (= V_th + 0.5 = 0.5 + 0.5 = 1.0)
circuit.V('bias', 'Vbias', circuit.gnd, 2.0) # 2V input for bias voltage

# Common-Gate Amplifier with Resistor Load
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This design uses a common-gate configuration where the input signal is applied to the source of the NMOS transistor. The gate is biased with a DC voltage to ensure proper operation. The resistor load is connected to the drain, and the output is taken from the drain of the NMOS transistor.