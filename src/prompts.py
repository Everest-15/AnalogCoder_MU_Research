"""
Prompt assembly helpers.

Responsible for reading template files and filling them based on runtime config
and task metadata (type, I/O nodes, retrieval info for complex tasks).
"""
from typing import Tuple
from pathlib import Path
from src.config import AppConfig, COMPLEX_TASK_TYPES

BIAS_USAGE = """Due to the operational range of the op-amp being 0 to 5V, please connect the nodes that were originally grounded to a 2.5V DC power source.
Please increase the gain as much as possible to maintain oscillation.
"""

def _read_file(path: str) -> str:
    """Read a file by absolute path or relative to this module's directory."""
    base_dir = Path(__file__).resolve().parent
    target = Path(path)
    final_path = target if target.is_absolute() else (base_dir / target).resolve()
    with open(final_path, "r") as f:
        return f.read()

def base_prompt_for(config: AppConfig) -> str:
    """Select the base prompt template file according to flags in config."""
    # Select prompt template
    if config.no_prompt:
        path = 'prompt_template_wo_prompt.md'
    elif config.no_context:
        path = '../templates/prompt_template_wo_context.md'
    elif config.no_chain:
        path = '../templates/prompt_template_wo_chain_of_thought.md'
    elif config.ngspice:
        path = '../templates/prompt_template_ngspice.md'
    else:
        path = '../templates/prompt_template.md'
    return _read_file(path)

def complex_prompt_template() -> str:
    """Return the complex-task prompt template contents."""
    return _read_file('../templates/prompt_template_complex.md')

def simulation_error_prompt() -> str:
    """Return the simulation-error hint template."""
    return _read_file('../templates/simulation_error.md')

def execution_error_prompt() -> str:
    """Return the execution-error hint template."""
    return _read_file('../templates/execution_error.md')

def build_prompt(config: AppConfig, task: str, input_nodes: str, output_nodes: str, task_type: str,
                 subcircuits_info: str = "", note_info: str = "", call_info: str = "") -> Tuple[str, float]:
    """Build the final user prompt string and return it along with a bias voltage hint.

    For complex tasks, optionally includes retrieval-derived guidance sections.
    Returns (prompt_text, bias_voltage_hint).
    """
    if task_type not in COMPLEX_TASK_TYPES or not config.skill:
        prompt = base_prompt_for(config)
        prompt = prompt.replace('[TASK]', task).replace('[INPUT]', input_nodes).replace('[OUTPUT]', output_nodes)
        bias_voltage = 2.5 if task_type in COMPLEX_TASK_TYPES else None
        if task_type in COMPLEX_TASK_TYPES:
            # Allow subcircuits in complex tasks
            prompt = prompt.replace('6. Avoid using subcircuits.', '').replace('7.', '6.').replace('8.', '7.')
        return prompt, (bias_voltage if bias_voltage is not None else 0.0)
    else:
        prompt = complex_prompt_template()
        prompt = (prompt.replace('[TASK]', task)
                        .replace('[INPUT]', input_nodes)
                        .replace('[OUTPUT]', output_nodes)
                        .replace('[SUBCIRCUITS_INFO]', subcircuits_info)
                        .replace('[NOTE_INFO]', note_info)
                        .replace('[CALL_INFO]', call_info))
        if task_type == "Oscillator":
            prompt += "\n" + BIAS_USAGE
        # note_info provider returns numeric bias voltage; caller can pass it back
        return prompt, 0.0