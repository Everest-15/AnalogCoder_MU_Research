### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin for signal input, Vbias for biasing

#### Single-Stage Common-Gate Amplifier with Resistive Load

1. **Transistor Setup**:
   - **M1** (NMOS) is used for the common-gate configuration.
   - Gate of **M1** is connected to a DC bias voltage, **Vbias**.
   - Source of **M1** is connected to the input node **Vin**.
   - Drain of **M1** is connected to the output node **Vout** and also to the load resistor **R1**.

2. **Biasing**:
   - **Vbias** is used to set the gate voltage of **M1** to ensure it operates in the saturation region.
   - **Vin** provides the input signal and is applied at the source terminal of **M1**.

3. **Load Resistor (R1)**:
   - **R1** is connected between the drain of **M1** and **Vdd**.
   - This resistor converts the current through **M1** into an output voltage.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Common-Gate Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supplies for the power and input signal
circuit.V('dd', 'Vdd', circuit.gnd, 5.0)  # 5V power supply
circuit.V('in', 'Vin', circuit.gnd, 1.0)  # 1V input for signal
circuit.V('bias', 'Vbias', circuit.gnd, 2.0)  # 2V input for bias voltage

# Common-Gate Amplifier with Resistor Load
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This design provides a single-stage common-gate amplifier with a resistive load. The input signal is applied at the source terminal, and the output is taken from the drain of the NMOS transistor. The gate is biased with a constant DC voltage to ensure proper operation.