### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin, Vbias for biasing and signal input

#### Single-Stage Common-Gate Amplifier with Resistive Load

1. **Transistor Setup**:
   - **M1** (NMOS) is used as the main amplifying transistor.
   - The gate of **M1** is connected to the bias voltage **Vbias** to set the operating point.
   - The source of **M1** is connected to the input node **Vin**.
   - The drain of **M1** is connected to the output node **Vout** through resistor **R1**.

2. **Load and Biasing**:
   - **R1** connects the drain of **M1** to **Vdd**, providing a load for the amplifier.
   - **Vbias** is used to bias the gate of **M1** properly, ensuring it operates in the saturation region.

3. **Power Supply**:
   - **Vdd** provides the necessary supply voltage for the circuit operation.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Common-Gate Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supply
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply

# Input and Bias Voltage
circuit.V('in', 'Vin', circuit.gnd, 1.0) # 1V input for bias voltage (= V_th + 0.5 = 0.5 + 0.5 = 1.0)
circuit.V('bias', 'Vbias', circuit.gnd, 1.5) # 1.5V for gate biasing

# Common-Gate Amplifier
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This design outlines a simple common-gate amplifier with a resistive load, where the input signal is applied to the source terminal of the NMOS transistor, and the output is taken from the drain. The biasing is set to ensure the NMOS operates correctly in the saturation region.