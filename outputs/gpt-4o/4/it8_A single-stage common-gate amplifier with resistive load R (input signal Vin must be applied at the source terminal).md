### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin for the input signal, Vbias for biasing
- **Capacitors**: Not specified but can be used for coupling and bypass applications if required

#### Common-Gate Amplifier with Resistor Load
1. **Transistor Setup**:
   - **M1** (NMOS) is used as the amplifying transistor.
   - The source of **M1** is connected to the input node **Vin**.
   - The gate of **M1** is connected to the bias voltage **Vbias**.
   - The drain of **M1** is connected to the output node **Vout** through resistor **R1**.

2. **Biasing**:
   - **Vbias** is used to set the gate voltage of **M1** to ensure it operates in the saturation region.
   - **Vin** provides the input signal at the source of **M1**.

3. **Load and Output**:
   - **R1** connects the drain of **M1** to **Vdd**. This resistor converts the current through **M1** into an output voltage.
   - The output node **Vout** is taken from the drain of **M1**.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Common-Gate Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supplies for the power and input signal
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply
circuit.V('bias', 'Vbias', circuit.gnd, 1.5) # 1.5V bias voltage (= V_th + 1.0 = 0.5 + 1.0)

# Input signal source
circuit.V('in', 'Vin', circuit.gnd, 0.0) # 0V input for bias point analysis

# Common-Gate Amplifier with Resistor Load
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This design provides a common-gate amplifier configuration using an NMOS transistor with a resistive load. The input signal is applied at the source, and the output is taken from the drain, with the gate biased to ensure proper operation in the saturation region.