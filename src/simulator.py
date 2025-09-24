"""
Simulation utilities.

- run_code: executes a generated Python design script and heuristically parses its
  stdout/stderr to classify failures as execution vs. simulation errors.
- write_pyspice_code: converts a simple SPICE-like netlist into a minimal PySpice
  script that computes operating point voltages.
- tmux helpers: start/kill background sessions for long-running tasks.
"""
import os
import sys
import time
import subprocess
from typing import Tuple

def run_code(file: str) -> Tuple[int, int, str, str]:
    """Run a Python file and attempt to detect execution vs. simulation failures.

    Returns (execution_error, simulation_error, execution_error_info, floating_node).
    """
    print("IN RUN_CODE : {}".format(file))
    simulation_error = 0
    execution_error = 0
    execution_error_info = ""
    floating_node = ""
    try:
        print("-----------------running code-----------------")
        print("file:", file)
        result = subprocess.run(["python", "-u", file], check=True, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        # Mirror the original parsing
        if len(result.stdout.split("\n")) >= 2 and ("failed" in result.stdout.split("\n")[-2] or "failed" in result.stdout.split("\n")[-1]):
            if len(result.stdout.split("\n")) >= 2:
                if "check node" in result.stdout.split("\n")[1]:
                    simulation_error = 1
                    floating_node = result.stdout.split("\n")[1].split()[-1]
                else:
                    execution_error = 1
                    if "ERROR" in result.stdout.split("\n")[1]:
                        execution_error_info = "ERROR" + result.stdout.split("\n")[1].split("ERROR")[-1]
                    elif "Error" in result.stdout.split("\n")[1]:
                        execution_error_info = "Error" + result.stdout.split("\n")[1].split("Error")[-1]
                    if len(result.stdout.split("\n"))>=3 and "ERROR" in result.stdout.split("\n")[2]:
                        execution_error_info += "\nERROR" + result.stdout.split("\n")[2].split("ERROR")[-1]
                    elif len(result.stdout.split("\n"))>=3 and "Error" in result.stdout.split("\n")[2]:
                        execution_error_info += "\nError" + result.stdout.split("\n")[2].split("Error")[-1]
                    if len(result.stdout.split("\n"))>=4 and "ERROR" in result.stdout.split("\n")[3]:
                        execution_error_info += "\nERROR" + result.stdout.split("\n")[3].split("ERROR")[-1]
                    elif len(result.stdout.split("\n"))>=4 and "Error" in result.stdout.split("\n")[3]:
                        execution_error_info += "\nError" + result.stdout.split("\n")[3].split("Error")[-1]
            if len(result.stderr.split("\n")) >= 2:
                if "check node" in result.stderr.split("\n")[1]:
                    simulation_error = 1
                    floating_node = result.stderr.split("\n")[1].split()[-1]
                else:
                    execution_error = 1
                    if "ERROR" in result.stderr.split("\n")[1]:
                        execution_error_info = "ERROR" + result.stderr.split("\n")[1].split("ERROR")[-1]
                    elif "Error" in result.stderr.split("\n")[1]:
                        execution_error_info = "Error" + result.stderr.split("\n")[1].split("Error")[-1]
                    if len(result.stdout.split("\n"))>=3 and "ERROR" in result.stderr.split("\n")[2]:
                        execution_error_info += "\nERROR" + result.stderr.split("\n")[2].split("ERROR")[-1]
                    elif len(result.stdout.split("\n"))>=3 and "Error" in result.stderr.split("\n")[2]:
                        execution_error_info += "\nError" + result.stderr.split("\n")[2].split("Error")[-1]
                    if len(result.stdout.split("\n"))>=4 and "ERROR" in result.stderr.split("\n")[3]:
                        execution_error_info += "\nERROR" + result.stderr.split("\n")[3].split("ERROR")[-1]
                    elif len(result.stdout.split("\n"))>=4 and "Error" in result.stderr.split("\n")[3]:
                        execution_error_info += "\nError" + result.stderr.split("\n")[3].split("Error")[-1]
            if simulation_error == 1:
                execution_error = 0
            if execution_error_info == "" and execution_error == 1:
                execution_error_info = "Simulation failed."
        code_content = open(file, "r").read()
        if "circuit.X" in code_content:
            execution_error_info += "\nPlease avoid using the subcircuit (X) in the code."
        if "error" in result.stdout.lower() and not "<<NAN, error".lower() in result.stdout.lower() and simulation_error == 0:
            execution_error = 1
            execution_error_info = result.stdout + result.stderr
        return execution_error, simulation_error, execution_error_info, floating_node
    except subprocess.CalledProcessError as e:
        print(f"error when running: {e}")
        print("stderr", e.stderr, file=sys.stderr)
        simulation_error = 0
        if "failed" in e.stdout:
            if len(e.stderr.split("\n")) >= 2 and "check node" in e.stderr.split("\n")[1]:
                simulation_error = 1
                floating_node = e.stderr.split("\n")[1].split()[-1]
        execution_error = 1
        execution_error_info = e.stdout + e.stderr
        if simulation_error == 1:
            execution_error = 0
            execution_error_info = "Simulation failed."
        return execution_error, simulation_error, execution_error_info, floating_node
    except subprocess.TimeoutExpired:
        execution_error = 1
        execution_error_info = "Suggestion: Avoid letting users input in Python code.\n"
        return execution_error, 0, execution_error_info, ""

def write_pyspice_code(sp_code_path: str, code_path: str, op_path: str) -> None:
    """Create a minimal PySpice script from a simplified SPICE netlist.

    The generated script computes operating point voltages and writes them to op_path.
    """
    import_template = """
from PySpice.SPICE.Netlist import Circuit
from PySpice.Unit import *
"""
    pyspice_template = """
try:
    analysis = simulator.operating_point()
    fopen = open("[OP_PATH]", "w")
    for node in analysis.nodes.values():
        fopen.write(f"{str(node)}\\t{float(analysis[str(node)][0]):.6f}\\n")
    fopen.close()
except Exception as e:
    print("Analysis failed due to an error:")
    print(str(e))
"""
    with open(sp_code_path, 'r') as sp_code, open(code_path, 'w') as code:
        code.write(import_template)
        code.write("circuit = Circuit('circuit')\n")
        for line in sp_code.readlines():
            if line.startswith(".model"):
                parts = line.split()
                if len(parts) < 6:
                    continue
                code.write(f"circuit.model('{parts[1]}', '{parts[2]}', {parts[3]}, {parts[4]}, {parts[5]})\n")
            elif line.startswith(('R','C','V','I')):
                type_name = line[0]
                parts = line.split()
                if len(parts) < 4:
                    continue
                name, n1, n2, value = parts[0][1:], parts[1], parts[2], parts[3]
                code.write(f"circuit.{type_name}('{name}', '{n1}', '{n2}', '{value}')\n")
            elif line.startswith('M'):
                parts = line.split()
                if len(parts) < 8:
                    continue
                name, drain, gate, source, bulk, model, w, l = parts[0][1:], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6], parts[7]
                code.write(f"circuit.MOSFET('{name}', '{drain}', '{gate}', '{source}', '{bulk}', model='{model}', {w}, {l})\n")
        code.write("simulator = circuit.simulator()\n")
        code.write(pyspice_template.replace("[OP_PATH]", op_path))

def start_tmux_session(session_name: str, command: str) -> None:
    """Start a detached tmux session and execute a command inside it."""
    subprocess.run(['tmux', 'new-session', '-d', '-s', session_name])
    subprocess.run(['tmux', 'send-keys', '-t', session_name, command, 'C-m'])
    print(f"tmux session '{session_name}' started, running command: {command}")

def kill_tmux_session(session_name: str) -> None:
    """Attempt to kill a tmux session by name, logging the outcome."""
    try:
        subprocess.run(['tmux', 'kill-session', '-t', session_name], check=True)
        print(f"tmux session '{session_name}' has been killed successfully.")
    except subprocess.CalledProcessError:
        print(f"Failed to kill tmux session '{session_name}'. Session might not exist.")