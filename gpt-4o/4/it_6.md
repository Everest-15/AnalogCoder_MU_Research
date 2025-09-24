# Task 4, iteration 6

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

#### Single-Stage Common-Gate Amplifier with Resistive Load
1. **Transistor Setup**:
   - **M1** (NMOS) is used as the main amplifying transistor.
   - The source of **M1** is connected to the input node **Vin**.
   - The gate of **M1** is connected to **Vbias** to ensure proper biasing.
   - The drain of **M1** is connected to the output node **Vout** through the load resistor **R1**.

2. **Load and Biasing**:
   - **R1** connects the drain of **M1** to **Vdd**, converting the current through **M1** into an output voltage.
   - **Vbias** is used to set the gate voltage of **M1**, ensuring it operates in the saturation region.

3. **Power Supply**:
   - **Vdd** is provided as the DC supply voltage.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Common-Gate Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supplies for the power and input signal
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply
circuit.V('in', 'Vin', circuit.gnd, 1.5) # 1.5V input for bias voltage (Vgs = Vbias - Vin = Vth + 0.5 = 0.5 + 0.5 = 1.0, thus Vbias = Vin + 1.0 = 1.5)
circuit.V('bias', 'Vbias', circuit.gnd, 2.5) # 2.5V input for bias voltage (Vbias = Vgs + Vin = 1.0 + 1.5 = 2.5)

# Single-Stage Common-Gate Amplifier with Resistor Load
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This design ensures that the common-gate amplifier is properly biased and connected with a resistive load, allowing it to amplify signals applied to the source terminal. The gate voltage is set using **Vbias** to maintain the transistor in the saturation region.
