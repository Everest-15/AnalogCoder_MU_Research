"""
Worker module orchestrates a single design iteration for a given analog-circuit task.

Responsibilities:
- Build the appropriate prompt for the task (simple vs. complex with skills/retrieval).
- Call the LLM and persist raw outputs for traceability.
- Extract runnable code from the LLM response and save a snippet per-iteration.
- Run lightweight checks on the produced code/netlist to validate basics.
- Maintain a simple token-cost accounting approximation.
"""
import time
import pandas as pd
from typing import Optional, List
from pathlib import Path

def _save_answer(project_root: Path, model: str, task_id: int, it: int, task: str, answer: str) -> Path:
    """
    Save raw LLM answer to a markdown file and return its path.
    """
    out_dir = project_root / "outputs" / model / f"{task_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_md = out_dir / f"it{it}_{task}.md"
    out_md.write_text(answer, encoding="utf-8")
    return out_md

from src.config import parse_args, AppConfig, COMPLEX_TASK_TYPES
from src.llm_client import LLMClient
from src.prompts import build_prompt, execution_error_prompt, simulation_error_prompt
from src.retrieval import get_retrieval
from src.analysis import (
    get_subcircuits_info, get_note_info, get_call_info,
    extract_code, check_function
)

def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent

def _model_dir_name(model: str) -> str:
    # Safe folder name from model string, e.g., "gpt-4o" -> "gpt-4o"
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in model)

def _open_log(config: AppConfig, circuit_id: int, suffix: str) -> str:
    strftime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    return f'{strftime}_{config.model}_{circuit_id}{suffix}.txt'

def _decide_log_suffix(config: AppConfig, task_type: str) -> str:
    if config.ngspice: return "_ngspice_log"
    if config.no_prompt: return "_no_prompt_log"
    if config.no_context: return "_no_context_log"
    if config.no_chain: return "_no_chain_log"
    if not config.skill and task_type in COMPLEX_TASK_TYPES: return "_log_no_skill"
    return "_log"

def _write_snippet(base_dir: Path, model: str, task_id: int, it: int, code_text: str) -> Path:
    model_dir = base_dir / _model_dir_name(model) / str(task_id)
    model_dir.mkdir(parents=True, exist_ok=True)
    out_path = model_dir / f"it_{it}.py"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(code_text)
    return out_path

def work_one(config: AppConfig, row, it: int, flog, remaining_money: float) -> float:
    task = row['Circuit']
    input_nodes = row['Input'].strip()
    output_nodes = row['Output'].strip()
    task_type = row['Type']
    subcircuits: Optional[List[int]] = None
    if task_type in COMPLEX_TASK_TYPES:
        subcircuits = get_retrieval(config, task, config.task_id)

    # Build prompt
    if task_type in COMPLEX_TASK_TYPES and config.skill:
        sub_info = get_subcircuits_info(subcircuits)
        note_info, bias_voltage = get_note_info(subcircuits)
        call_info = get_call_info(subcircuits)
        prompt, _ = build_prompt(config, task, input_nodes, output_nodes, task_type,
                                 subcircuits_info=sub_info, note_info=note_info, call_info=call_info)
    else:
        prompt, bias_voltage = build_prompt(config, task, input_nodes, output_nodes, task_type)

    messages = [
        {"role": "system", "content": "You are an analog integrated circuits expert."},
        {"role": "user", "content": prompt}
    ]

    exec_err_prompt = execution_error_prompt()
    sim_err_prompt = simulation_error_prompt()

    client = LLMClient(config.model, config.api_key)
    # Call LLM
    if client.is_openai_like():
        try:
            response = client.chat_openai(messages, temperature=config.temperature)
            answer = response.text
            total_tokens = response.total_tokens
            prompt_tokens = response.prompt_tokens
            completion_tokens = response.completion_tokens
            # simple money accounting
            if "ft:gpt-3.5" in config.model:
                remaining_money -= (prompt_tokens / 1e6 * 3) + (completion_tokens / 1e6 * 6)
            elif "gpt-3" in config.model:
                remaining_money -= (prompt_tokens / 1e6 * 0.5) + (completion_tokens / 1e6 * 1.5)
            elif "gpt-4" in config.model:
                remaining_money -= (prompt_tokens / 1e6 * 10) + (completion_tokens / 1e6 * 30)

            # Persist the raw text
            out_md = _save_answer(_project_root(), config.model, row['Id'], it, task, answer)
            flog.write(f"Saved output to: {out_md}\n")

            # Try to extract runnable code
            empty_err, code_text = extract_code(answer, use_ngspice=config.ngspice)
            if empty_err or not code_text.strip():
                flog.write(f"Extraction failed for task {row['Id']} (it={it}): no code block found\n")
                flog.flush()
                return remaining_money

            # Save snippet and run checker
            base_dir = _project_root()
            code_path = _write_snippet(base_dir, config.model, row['Id'], it, code_text)
            flog.write(f"Saved code to: {code_path}\n")
            flog.flush()

            # Determine task_type for checker
            task_type = row['Type']
            func_err, msg = check_function(row['Id'], str(code_path), task_type)
            if func_err:
                flog.write(f"Check failed for task {row['Id']} (it={it}): {msg}\n")
            else:
                flog.write(f"Check passed for task {row['Id']} (it={it})\n")
            flog.flush()

        except Exception as e:
            flog.write(f"LLM call failed on task {row['Id']} (it={it}): {repr(e)}\n")
            flog.flush()
            return remaining_money
    else:
        raise NotImplementedError("Ollama path should be wired similarly to original if needed.")
    return remaining_money

def main():
    config = parse_args()
    base_dir = _project_root()
    df_path = base_dir / 'data_files' / 'problem_set.tsv'
    df = pd.read_csv(df_path, delimiter='\t')
    remaining_money = 2
    for _, row in df.iterrows():
        if row['Id'] != config.task_id:
            continue
        log_suffix = _decide_log_suffix(config, row['Type'])
        log_path = _open_log(config, row['Id'], log_suffix)
        with open(base_dir / log_path, 'w') as flog:
            for it in range(config.num_of_done, config.num_per_task):
                flog.write(f"task: {row['Id']}, it: {it}\n")
                flog.flush()
                remaining_money = work_one(config, row, it, flog, remaining_money)
                if remaining_money < 0:
                    break