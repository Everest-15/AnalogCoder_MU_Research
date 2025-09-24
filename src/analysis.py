import os
import re
import subprocess
from typing import Tuple, Optional, List, Iterable

import numpy as np
import pandas as pd


# -----------------------------
# Helpers
# -----------------------------
def _split_csv_like(s: str) -> List[str]:
    """
    Split an input like 'a, b ,c' into ['a','b','c'] with trimming and no empties.
    """
    return [t.strip() for t in s.split(",") if t.strip()]


# -----------------------------
# Code extraction / patching
# -----------------------------
def extract_code(generated_content: str, use_ngspice: bool) -> Tuple[int, str]:
    """
    Extract the first fenced code block, add required imports, and return the full code.
    Returns (empty_code_error_flag, code).
    """
    empty_code_error = 0
    assert generated_content != "", "generated_content is empty"

    # Grab the FIRST fenced code block (any language)
    regex = r".*?```.*?\n(.*?)```"
    matches = re.finditer(regex, generated_content, re.DOTALL)
    first_match = next(matches, None)
    try:
        code = first_match.group(1)
        # Preserve structure; trim trailing spaces only
        code = "\n".join([line.rstrip() for line in code.split("\n")])
    except Exception:
        return 1, ""

    # Ensure PySpice imports are present for consistent execution
    required_imports = []
    if "from PySpice.Spice.Netlist import Circuit" not in code:
        required_imports.append("from PySpice.Spice.Netlist import Circuit")
    if "from PySpice.Unit import *" not in code:
        required_imports.append("from PySpice.Unit import *")

    if required_imports:
        code = "\n".join(required_imports) + "\n" + code

    # Do NOT truncate after 'circuit.simulator()'; keep full script so analyses remain intact
    return empty_code_error, code


# -----------------------------
# Numeric utilities
# -----------------------------
def get_best_voltage(dc_file_path: str) -> Tuple[int, float]:
    """
    Given a DC sweep result file with two lines (vin, vout),
    find vin such that vout is closest to 2.5 V.
    Returns (error_flag, best_voltage).
    """
    with open(dc_file_path, "r") as fopen:
        vin = np.array([float(x) for x in fopen.readline().strip().split() if x])
        vout = np.array([float(x) for x in fopen.readline().strip().split() if x])

    if vin.size == 0 or vout.size == 0:
        return 1, 0.0
    if np.max(vout) - np.min(vout) < 1e-3:
        return 1, 0.0

    idx = int(np.argmin(np.abs(vout - 2.5)))
    return 0, float(vin[idx])


# -----------------------------
# Netlist / PySpice parsing
# -----------------------------
def get_vin_name(netlist_content: str, task_type: str) -> Tuple[str, Optional[str]]:
    """
    Parse netlist text to find voltage source names for input(s).
    For Amplifier: returns (vinn_name, None)
    For Opamp: returns (vinn_name, vinp_name)
    """
    vinn_name = "in"
    vinp_name = None
    for line in netlist_content.splitlines():
        ls = line.lower().split()
        if not ls or not ls[0].startswith("v") or len(ls) < 2:
            continue
        if task_type == "Amplifier" and "vin" in ls[1]:
            vinn_name = line.split()[0][1:]
        if task_type == "Opamp" and "vinp" in ls[1]:
            vinp_name = line.split()[0][1:]
        if task_type == "Opamp" and "vinn" in ls[1]:
            vinn_name = line.split()[0][1:]
    return vinn_name, vinp_name


def replace_voltage(raw_code: str,
                    best_voltage: float,
                    vinn_name: Optional[str],
                    vinp_name: Optional[str]) -> str:
    """
    Replace voltage source value for vinn/vinp in PySpice code with best_voltage.
    Works for calls like circuit.V('vinn', 'n+', 'n-', value)
    """
    def _rewrite_line(line: str, target: str) -> str:
        # Drop inline comment, split args, set the last arg to numeric best_voltage
        args_part = line.split("#")[0].strip().rstrip(")")
        parts = [p.strip() for p in args_part.split("(", 1)[1].split(",")]
        if parts:
            parts[-1] = str(best_voltage)
        return f"circuit.V({', '.join(parts)})"

    new_lines: List[str] = []
    for line in raw_code.splitlines():
        lower = line.strip().lower()
        if not lower.startswith("circuit.v"):
            new_lines.append(line)
            continue

        matched = False
        if vinn_name:
            if lower.startswith(f"circuit.v('{vinn_name.lower()}'") or lower.startswith(
               f'circuit.v("{vinn_name.lower()}"'):
                new_lines.append(_rewrite_line(line, vinn_name))
                matched = True
        if (not matched) and vinp_name:
            if lower.startswith(f"circuit.v('{vinp_name.lower()}'") or lower.startswith(
               f'circuit.v("{vinp_name.lower()}"'):
                new_lines.append(_rewrite_line(line, vinp_name))
                matched = True

        if not matched:
            new_lines.append(line)

    return "\n".join(new_lines) + "\n"


def connect_vinn_vinp(dc_sweep_code: str,
                      vinn_name: Optional[str],
                      vinp_name: Optional[str]) -> str:
    """
    For Opamp DC sweep, tie Vinn and Vinp with a 0V source so we can sweep the differential.
    Inserts a new ideal source once (does not duplicate).
    """
    if not (vinn_name and vinp_name):
        return dc_sweep_code

    lines = dc_sweep_code.splitlines()
    already_added = any("circuit.V('dc', 'Vinn', 'Vinp', 0.0)" in l or
                        'circuit.V("dc", "Vinn", "Vinp", 0.0)' in l for l in lines)

    new_lines: List[str] = []
    for line in lines:
        new_lines.append(line)
        l = line.strip().lower()
        # Insert AFTER we see Vinp declaration the first time
        if (not already_added) and l.startswith("circuit.v(") and (
            l.startswith(f"circuit.v('{vinp_name.lower()}'") or
            l.startswith(f'circuit.v("{vinp_name.lower()}"')
        ):
            new_lines.append("circuit.V('dc', 'Vinn', 'Vinp', 0.0)")

    return "\n".join(new_lines) + "\n"


# -----------------------------
# Tables / notes / call info
# -----------------------------
def get_subcircuits_info(subcircuits: Iterable[int],
                         lib_data_path: str = "lib_info.tsv",
                         task_data_path: str = "problem_set.tsv") -> str:
    """
    Build a tab-separated info table for the requested subcircuit IDs.
    """
    lib_df = pd.read_csv(lib_data_path, delimiter="\t")
    task_df = pd.read_csv(task_data_path, delimiter="\t")

    columns = [
        "Id",
        "Circuit Type",
        "Gain/Differential-mode gain (dB)",
        "Common-mode gain (dB)",
        "Input",
        "Output",
    ]
    subcircuits_df = pd.DataFrame(columns=columns)

    for sub_id in subcircuits:
        # .item() will raise if missing; that's fine to surface a clean error
        sub_type = task_df.loc[task_df["Id"] == sub_id, "Type"].item()
        sub_gain = float(lib_df.loc[lib_df["Id"] == sub_id, "Av (dB)"].item())
        sub_com_gain = float(lib_df.loc[lib_df["Id"] == sub_id, "Com Av (dB)"].item())

        sub_input = task_df.loc[task_df["Id"] == sub_id, "Input"].item()
        input_node_list = [n for n in _split_csv_like(sub_input) if "bias" not in n.lower()]

        sub_output = task_df.loc[task_df["Id"] == sub_id, "Output"].item()
        # keep only "plain" outputs (drop differential labels), case-insensitive
        output_node_list = [
            n for n in _split_csv_like(sub_output)
            if ("outn" not in n.lower() and "outp" not in n.lower())
        ]

        new_row = {
            "Id": sub_id,
            "Circuit Type": sub_type,
            "Gain/Differential-mode gain (dB)": f"{sub_gain:.2f}",
            "Common-mode gain (dB)": f"{sub_com_gain:.2f}",
            "Input": ", ".join(input_node_list),
            "Output": ", ".join(output_node_list),
        }
        subcircuits_df = pd.concat([subcircuits_df, pd.DataFrame([new_row])], ignore_index=True)

    return subcircuits_df.to_csv(sep="\t", index=False)


def get_note_info(subcircuits: Iterable[int],
                  lib_data_path: str = "lib_info.tsv",
                  task_data_path: str = "problem_set.tsv"):
    """
    Compose note text for amplifier/opamp subcircuits; also return bias voltage.
    Returns (note_info: str, sub_bias_voltage: float)
    """
    lib_df = pd.read_csv(lib_data_path, delimiter="\t")
    task_df = pd.read_csv(task_data_path, delimiter="\t")

    note_info_lines: List[str] = []
    sub_bias_voltage = 0.0  # last seen

    for sub_id in subcircuits:
        sub_type = task_df.loc[task_df["Id"] == sub_id, "Type"].item()
        sub_name = task_df.loc[task_df["Id"] == sub_id, "Submodule Name"].item()
        sub_bias_voltage = float(lib_df.loc[lib_df["Id"] == sub_id, "Voltage Bias"].item())

        # Only craft notes for amplifier-like types
        if ("Amplifier" not in sub_type) and ("Opamp" not in sub_type):
            continue

        # Column name as provided (kept verbatim)
        sub_phase = task_df.loc[task_df["Id"] == sub_id, "Vin(n) Phase"].item()
        other_sub_phase = "non-inverting" if str(sub_phase).lower() == "inverting" else "inverting"

        if sub_type == "Amplifier":
            note_info_lines.append(f"The Vin of {sub_name} is the {sub_phase} input.")
            note_info_lines.append(f"There is NO {other_sub_phase} input in {sub_name}.")
            note_info_lines.append(f"The DC operating voltage for Vin is {sub_bias_voltage} V.")
        elif sub_type == "Opamp":
            note_info_lines.append(f"The Vinn of {sub_name} is the {sub_phase} input.")
            note_info_lines.append(f"The Vinp of {sub_name} is the {other_sub_phase} input.")
            note_info_lines.append(f"The DC operating voltage for Vinn/Vinp is {sub_bias_voltage} V.")

    return ("\n".join(note_info_lines) + ("\n" if note_info_lines else "")), sub_bias_voltage


def get_call_info(subcircuits: Iterable[int],
                  lib_data_path: str = "lib_info.tsv",
                  task_data_path: str = "problem_set.tsv") -> str:
    """
    Return example usage snippets for the subcircuits.
    Uses info from problem_set.tsv to build an X-instance call with proper pin order.
    """
    task_df = pd.read_csv(task_data_path, delimiter="\t")

    template = (
        "```python\n"
        "from p[ID]_lib import *\n"
        "# declare the subcircuit\n"
        "circuit.subcircuit([SUBMODULE_NAME]())\n"
        "# create a subcircuit instance\n"
        "circuit.X('1', '[SUBMODULE_NAME]', [INPUT_OUTPUT])\n"
        "```\n"
    )

    call_info_parts: List[str] = []
    for sub_id in subcircuits:
        row = task_df.loc[task_df["Id"] == sub_id]
        if row.empty:
            # Surface an explicit, concise message per missing ID
            call_info_parts.append(f"# Warning: subcircuit Id {sub_id} not found in {task_data_path}\n")
            continue

        submodule_name = row["Submodule Name"].item()
        # Build pin list (inputs then outputs), preserving CSV order given in file
        inputs = _split_csv_like(row["Input"].item())
        outputs = _split_csv_like(row["Output"].item())
        io = ", ".join([*inputs, *outputs])  # PySpice expects ordered node list

        snippet = template.replace("[ID]", str(sub_id)) \
                          .replace("[SUBMODULE_NAME]", submodule_name) \
                          .replace("[INPUT_OUTPUT]", io)
        call_info_parts.append(snippet)

    return "".join(call_info_parts)


# -----------------------------
# Checking / validation
# -----------------------------
def check_function(task_id: int, code_path: str, task_type: str):
    """
    Append the checker code for the given task type and execute it.
    Returns (func_error_flag, message).
    """
    fwrite_code_path = f"{code_path.rsplit('.', 1)[0]}_check.py"
    try:
        if task_type == "CurrentMirror":
            with open("../test_bench/CurrentMirror.py", "r") as ftest, open(code_path, "r") as fcode, open(fwrite_code_path, "w") as out:
                out.write(fcode.read() + "\n" + ftest.read())
        elif task_type in ("Amplifier", "Opamp"):
            test_code = open(f"test_bench/{task_type}.py", "r").read()
            with open(code_path, "r") as fcode, open(fwrite_code_path, "w") as out:
                for line in fcode.readlines():
                    if line.startswith("circuit.V") and "vin" in line.lower():
                        parts = line.split("#")[0].strip().rstrip(")").split(",")
                        raw_voltage = parts[-1].strip()
                        if raw_voltage and raw_voltage[0] in ("'", '"'):
                            raw_voltage = raw_voltage[1:-1]
                        voltage = raw_voltage.split(" ")[1] if "dc" in raw_voltage.lower() else raw_voltage
                        parts[-1] = f' "dc {voltage} ac 1u"'
                        line = ",".join(parts) + ")\n"
                    out.write(line)
                out.write("\n" + test_code)
        elif task_type == "Inverter":
            with open("../test_bench/Inverter.py", "r") as ftest, open(code_path, "r") as fcode, open(fwrite_code_path, "w") as out:
                out.write(fcode.read() + "\n" + ftest.read())
        else:
            return 0, ""
    except FileNotFoundError as e:
        # Bubble up a clean message if check files are missing
        return 1, f"Checker assets missing: {e}"

    try:
        result = subprocess.run(
            ["python", "-u", fwrite_code_path],
            check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print(result.stdout)
        print("function correct.")
        return 0, ""
    except subprocess.CalledProcessError as e:
        print("function error.")
        print("e.stdout", e.stdout)
        print("e.stderr", e.stderr)
        return 1, "\n".join(e.stdout.split("\n"))


def check_netlist(netlist_path: str,
                  operating_point_path: str,
                  input_nodes: str,
                  output_nodes: str,
                  task_id: int,
                  task_type: str):
    """
    Analyze operating point and netlist for MOSFET sanity checks and task-specific constraints.
    Returns (warning_flag, message).
    """
    warning = 0
    warning_message = ""

    if not os.path.exists(operating_point_path):
        return 0, ""

    fopen_op_text = open(operating_point_path, "r").read()

    # Verify given input/output node names appear in OP results (case-insensitive)
    for input_node in input_nodes.split(", "):
        if input_node.lower() not in fopen_op_text.lower():
            warning_message += f"The given input node ({input_node}) is not found in the netlist.\n"
            warning = 1
    for output_node in output_nodes.split(", "):
        if output_node.lower() not in fopen_op_text.lower():
            warning_message += f"The given output node ({output_node}) is not found in the netlist.\n"
            warning = 1

    if warning == 1:
        warning_message += (
            "Suggestion: You can replace the nodes actually used for input/output with the given names. "
            "Please rewrite the corrected complete code.\n"
        )

    if task_type == "Inverter":
        return (1 if warning_message else 0), warning_message.strip()

    # Parse key node voltages from OP file
    vdd_voltage = 5.0
    vinn_voltage = 1.0
    vinp_voltage = 1.0
    for line in fopen_op_text.splitlines():
        line_l = line.lower()
        try:
            if line_l.startswith("vdd"):
                vdd_voltage = float(line.split("\t")[-1])
            if line_l.startswith("vinn"):
                vinn_voltage = float(line.split("\t")[-1])
            if line_l.startswith("vinp"):
                vinp_voltage = float(line.split("\t")[-1])
        except Exception:
            pass

    if abs(vinn_voltage - vinp_voltage) > 1e-12:
        warning_message += "The given input voltages of Vinn and Vinp are not equal.\n"
        warning = 1
        warning_message += "Suggestion: Please make sure the input voltages are equal.\n"

    # Load OP voltages into dict
    voltages: dict = {}
    for line in fopen_op_text.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        node, voltage = parts[0], parts[1]
        try:
            voltages[node.lower()] = float(voltage)
        except Exception:
            continue
    voltages["0"] = 0.0
    voltages["gnd"] = 0.0

    vthn = 0.5
    vthp = 0.5
    miller_node_1 = None
    miller_node_2 = None
    resistance_exist = 0
    has_diodeload = 0
    first_stage_out = None

    with open(netlist_path, "r") as fnet:
        for line in fnet:
            if not line.strip() or line.startswith("."):
                continue

            if line.startswith("C"):
                if task_id == 9:
                    tokens = line.split()
                    if len(tokens) >= 3:
                        miller_node_1 = tokens[1].lower()
                        miller_node_2 = tokens[2].lower()

            if line.startswith("R"):
                resistance_exist = 1

            if line.startswith("M"):
                tokens = line.split()
                if len(tokens) < 6:
                    continue
                _, drain, gate, source, bulk, model = tokens[:6]
                drain = drain.lower()
                source = source.lower()
                bulk = bulk.lower()
                gate = gate.lower()
                mos_type = "NMOS" if "nmos" in model.lower() else "PMOS"

                # Task-specific structural checks
                if task_id == 4:
                    if drain == "vin" or gate == "vin":
                        warning_message += "For a common-gate amplifier, the vin should be connected to source.\n"
                        warning_message += "Suggestion: Please connect the vin to the source node.\n"
                        warning = 1
                elif task_id == 3:
                    if drain == "vout" or gate == "vout":
                        warning_message += "For a common-drain amplifier, the vout should be connected to source.\n"
                        warning_message += "Suggestion: Please connect the vout to the source node.\n"
                        warning = 1
                elif task_id == 10:
                    if gate == drain:
                        has_diodeload = 1
                elif task_id == 9:
                    if gate == "vin":
                        first_stage_out = drain

                # NMOS operating checks
                if mos_type == "NMOS":
                    vds_error = 0
                    vd = voltages.get(drain, 0.0)
                    vs = voltages.get(source, 0.0)
                    if vd == 0.0:
                        if drain in ("0", "gnd"):
                            warning_message += f"Suggestion: Please avoid connecting {mos_type} drain to ground.\n"
                        else:
                            vds_error = 1
                            warning_message += f"For {mos_type}, the drain node ({drain}) voltage is 0.\n"
                    elif vd < vs:
                        vds_error = 1
                        warning_message += f"For {mos_type}, the drain node ({drain}) voltage is lower than the source node ({source}) voltage.\n"
                    if vds_error == 1:
                        warning_message += "Suggestion: Ensure the device is active and V_DS > V_GS - V_TH.\n"

                    vgs_error = 0
                    vg = voltages.get(gate, 0.0)
                    if vg == vs:
                        if gate == source:
                            warning_message += f"For {mos_type}, the gate node ({gate}) is shorted to the source node ({source}).\n"
                            warning_message += "Suggestion: Separate the gate and source connections.\n"
                        else:
                            vgs_error = 1
                            warning_message += f"For {mos_type}, Vg equals Vs; device may be off.\n"
                    elif vg < vs:
                        vgs_error = 1
                        warning_message += f"For {mos_type}, gate voltage is lower than source voltage.\n"
                    elif vg <= vs + vthn:
                        vgs_error = 1
                        warning_message += f"For {mos_type}, V_GS is not sufficiently above V_TH.\n"
                    if vgs_error == 1:
                        warning_message += "Suggestion: Increase gate or decrease source to satisfy V_GS > V_TH.\n"

                # PMOS operating checks
                if mos_type == "PMOS":
                    vds_error = 0
                    vd = voltages.get(drain, 0.0)
                    vs = voltages.get(source, 0.0)
                    if vd == vdd_voltage:
                        if drain == "vdd":
                            warning_message += "Suggestion: Please avoid connecting PMOS drain to VDD directly.\n"
                        else:
                            vds_error = 1
                            warning_message += f"For PMOS, the drain node ({drain}) is at V_DD.\n"
                    elif vd > vs:
                        vds_error = 1
                        warning_message += f"For PMOS, drain voltage is higher than source voltage.\n"
                    if vds_error == 1:
                        warning_message += "Suggestion: Ensure the device is active and V_DS < V_GS - V_TH.\n"

                    vgs_error = 0
                    vg = voltages.get(gate, 0.0)
                    if vg == vs:
                        if gate == source:
                            warning_message += f"For PMOS, the gate node ({gate}) is shorted to the source node ({source}).\n"
                            warning_message += "Suggestion: Separate the gate and source connections.\n"
                        else:
                            vgs_error = 1
                            warning_message += "For PMOS, Vg equals Vs; device may be off.\n"
                    elif vg > vs:
                        vgs_error = 1
                        warning_message += "For PMOS, gate voltage is higher than source voltage.\n"
                    elif vg >= vs - vthp:
                        vgs_error = 1
                        warning_message += "For PMOS, |V_GS| is not sufficiently above V_TH.\n"
                    if vgs_error == 1:
                        warning_message += "Suggestion: Decrease gate or increase source so that V_GS < -V_TH (pmos on).\n"

    # Task-wide checks
    if task_id in [1, 2, 3, 4, 5, 6, 8, 13]:
        if resistance_exist == 0:
            warning_message += "There is no resistance in the netlist.\n"
            warning_message += "Suggestion: Please add a resistive load in the netlist.\n"
            warning = 1

    if task_id == 9:
        if first_stage_out is None:
            warning_message += "There is no first stage output in the netlist.\n"
            warning_message += "Suggestion: Please add a first stage output in the netlist.\n"
            warning = 1
        elif not (
            (first_stage_out == miller_node_1 and miller_node_2 == "vout") or
            (first_stage_out == miller_node_2 and miller_node_1 == "vout")
        ):
            if miller_node_1 is None:
                warning_message += "There is no Miller capacitor in the netlist.\n"
                warning_message += "Suggestion: Please correctly connect the Miller compensation capacitor."
            else:
                warning_message += "The Miller compensation capacitor is not correctly connected.\n"
                warning_message += "Suggestion: Please correctly connect the Miller compensation capacitor."
            warning = 1

    if task_id == 10 and has_diodeload == 0:
        warning_message += "There is no diode-connected load in the netlist.\n"
        warning_message += "Suggestion: Please add a diode-connected load in the netlist.\n"
        warning = 1

    warning_message = warning_message.strip()
    if not warning_message:
        return 0, ""

    final_message = (
        "According to the operating point check, there are some issues, which defy the general operating "
        "principles of MOSFET devices.\n"
        f"{warning_message}\n\n"
        "Please help me fix the issues and rewrite the corrected complete code.\n"
    )
    return 1, final_message
