### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the resistive load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin for signal input, Vbias for biasing
- **Capacitors**: Not specified but can be included for coupling and bypass applications if required

#### Common-Gate Amplifier with Resistive Load
1. **Transistor Setup**:
   - **M1** (NMOS) is used as the main amplifying transistor.
   - The source of **M1** is connected to the input node **Vin**.
   - The gate of **M1** is connected to a bias voltage **Vbias** to set the operating point.
   - The drain of **M1** is connected to the output node **Vout** through resistor **R1**.

2. **Load and Biasing**:
   - **R1** connects the drain of **M1** to **Vdd**. This resistor converts the current through **M1** into an output voltage.
   - **Vbias** is used to bias the gate of **M1**, ensuring it is properly biased to operate in the saturation region.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Common-Gate Amplifier')
# Define the NMOS model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supply and Bias Voltage
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply
circuit.V('bias', 'Vbias', circuit.gnd, 1.0) # 1V bias voltage (= V_th + 0.5 = 0.5 + 0.5 = 1.0)

# Common-Gate Amplifier
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This design uses a common-gate configuration where the input is applied to the source, the output is taken from the drain, and the gate is biased with a DC voltage. The resistive load at the drain provides the necessary voltage conversion for the amplifier.