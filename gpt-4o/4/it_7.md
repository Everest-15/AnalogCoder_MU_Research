# Task 4, iteration 7

## Description
A single-stage common-gate amplifier with resistive load R (input signal Vin must be applied at the source terminal)

## LLM Output

### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin for the signal input, Vbias for biasing
- **Capacitors**: Not specified but can be included for coupling and bypass applications if required

#### Common-Gate Amplifier with Resistor Load

1. **Transistor Setup**:
   - **M1** (NMOS) as the main amplifying transistor.
   - Source of **M1** is connected to the input node **Vin**.
   - Gate of **M1** is connected to **Vbias** to provide the necessary biasing.
   - Drain of **M1** is connected to the output node **Vout** through resistor **R1**.

2. **Load and Biasing**:
   - **R1** connects the drain of **M1** to **Vdd**, serving as the resistive load.
   - **Vbias** is used to set the gate voltage of **M1** to ensure it operates in the saturation region.

3. **Power Supply**:
   - **Vdd** provides the necessary DC supply voltage for the circuit operation.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Single-Stage Common-Gate Amplifier')
# Define the MOSFET model
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supplies for the power and input signal
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply
circuit.V('in', 'Vin', circuit.gnd, 1.5) # 1.5V input for bias voltage (= V_th + 1.0 = 0.5 + 1.0 = 1.5)
circuit.V('bias', 'Vbias', circuit.gnd, 2.0) # 2V input for bias voltage (chosen to keep M1 in saturation)

# Common-Gate Amplifier with Resistor Load
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This design provides a common-gate amplifier with a resistive load, ensuring the input signal is applied at the source terminal, and the output is taken from the drain. The biasing ensures the NMOS transistor operates in the saturation region for amplification.
