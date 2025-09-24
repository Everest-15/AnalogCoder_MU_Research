To design a single-stage common-gate amplifier with a resistive load, we need to focus on the configuration where the input signal is applied at the source terminal, and the gate is biased with a DC voltage. The drain will be connected to a resistive load, which is connected to the power supply.

### Task 1

#### Components Needed
- **NMOS Transistor**: M1
- **Resistor**: R1 for the load
- **Power Supply**: Vdd for DC supply
- **Input Signal Source**: Vin for the input signal, Vbias for gate biasing

#### Common-Gate Amplifier with Resistive Load
1. **Transistor Setup**:
   - **M1** (NMOS) is used as the amplifying transistor.
   - Source of **M1** is connected to the input node **Vin**.
   - Gate of **M1** is connected to the bias voltage **Vbias**.
   - Drain of **M1** is connected to **Vout** through resistor **R1**.

2. **Biasing**:
   - **Vbias** is used to ensure that **M1** operates in the saturation region. Typically, **Vbias** should be slightly above the threshold voltage of the NMOS to keep it in saturation.

3. **Load**:
   - **R1** is connected between the drain of **M1** and **Vdd**. This resistor converts the current through **M1** into an output voltage.

### Task 2

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('Common-Gate Amplifier')
# Define the MOSFET models
circuit.model('nmos_model', 'nmos', level=1, kp=100e-6, vto=0.5)

# Power Supplies for the power and input signal
circuit.V('dd', 'Vdd', circuit.gnd, 5.0) # 5V power supply
circuit.V('bias', 'Vbias', circuit.gnd, 1.0) # Bias voltage = V_th + 0.5 = 0.5 + 0.5 = 1.0

# Common-Gate Amplifier with Resistive Load
# parameters: name, drain, gate, source, bulk, model, w, l
circuit.MOSFET('1', 'Vout', 'Vbias', 'Vin', 'Vin', model='nmos_model', w=50e-6, l=1e-6)
circuit.R('1', 'Vout', 'Vdd', 1@u_kΩ)

# Analysis Part
simulator = circuit.simulator()
```

This design ensures that the NMOS transistor is in the common-gate configuration with a resistive load, allowing the input signal to be applied at the source terminal, and the output is taken from the drain. The gate is biased with a DC voltage to maintain the transistor in saturation for amplification.