# Task 4, iteration 9

## Description
A single-stage common-gate amplifier with resistive load R (input signal Vin must be applied at the source terminal)

## LLM Output

### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin, Vbias for biasing and signal input
- **Capacitors**: Not specified but can be included for coupling and bypass applications if required

#### Single-Stage Common-Gate Amplifier with Resistor Load

1. **Transistor Setup**:
   - **M1** (NMOS) is used as the amplifying transistor.
   - Gate of **M1** connected to the bias voltage **Vbias**.
   - Source of **M1** connected to the input node **Vin**.
   - Drain of **M1** connected to the output node **Vout** through resistor **R1**.

2. **Biasing**:
   - **Vbias** is used to bias the gate of **M1**, ensuring it operates in the saturation region.
   - **Vin** provides the input signal directly at the source of **M1**.

3. **Load and Coupling**:
   - **R1** connects the drain of **M1** to **Vdd**. This resistor converts the current through **M1** into an output voltage.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Single-Stage Common-Gate Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supplies for the power and input signal
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply
circuit.V('in', 'Vin', circuit.gnd, 1.0) # 1V input signal
circuit.V('bias', 'Vbias', circuit.gnd, 1.5) # 1.5V bias voltage (= V_th + 1.0 = 0.5 + 1.0 = 1.5)

# Common-Gate Amplifier
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This code defines a single-stage common-gate amplifier with a resistive load using PySpice, ensuring all nodes and biasing are correctly set up for proper operation.
