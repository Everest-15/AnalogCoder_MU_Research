"""
Lightweight retrieval helper for complex tasks.

Selects related subcircuit IDs from data_files/problem_set.tsv based on type
(and optionally circuit name), returning up to top-k IDs.
"""
from pathlib import Path
from typing import List
import pandas as pd

def get_retrieval(config, task: str, task_id: int) -> List[int]:
    """
    Return related subcircuit IDs for complex tasks, based on problem_set.tsv.

    Strategy:
    - Load ../data_files/problem_set.tsv relative to this file.
    - Find the row for `task_id` to get its Type (and Circuit if present).
    - Return up to K IDs of the same Type, prioritizing exact Circuit matches if available.
    - Gracefully fall back to [task_id] if the file/columns/rows are missing.

    K is taken from config.top_k (or config.k) if present, else defaults to 5.
    """
    # Determine how many related IDs to return
    k = int(getattr(config, "top_k", getattr(config, "k", 5)))

    # Resolve data file path relative to this source file
    base_dir = Path(__file__).resolve().parent
    problem_set_path = (base_dir.parent / "data_files" / "problem_set.tsv")

    try:
        df = pd.read_csv(problem_set_path, delimiter="\t")
    except Exception:
        # If we cannot read the table, at least return the current task for downstream logic
        try:
            return [int(task_id)]
        except Exception:
            return []

    # Ensure required columns are present
    if "Id" not in df.columns or "Type" not in df.columns:
        try:
            return [int(task_id)]
        except Exception:
            return []

    # Locate the current task row
    try:
        row = df.loc[df["Id"] == task_id].iloc[0]
    except Exception:
        # If the task is not found, return the ID itself
        try:
            return [int(task_id)]
        except Exception:
            return []

    task_type = str(row.get("Type", "")).strip()
    task_circuit = str(row.get("Circuit", "")).strip() if "Circuit" in df.columns else ""

    # Collect candidates of the same Type
    candidates = df.loc[df["Type"].astype(str).str.strip() == task_type].copy()

    # If Circuit column exists, prioritize exact circuit name matches first
    prioritized_ids: List[int] = []
    if "Circuit" in candidates.columns and task_circuit:
        exact = candidates.loc[candidates["Circuit"].astype(str).str.strip() == task_circuit]
        others = candidates.loc[candidates["Circuit"].astype(str).str.strip() != task_circuit]
        prioritized_ids.extend(exact["Id"].tolist())
        prioritized_ids.extend(others["Id"].tolist())
    else:
        prioritized_ids.extend(candidates["Id"].tolist())

    # Deduplicate while preserving order; ensure current task_id is included
    seen = set()
    ordered: List[int] = []
    for cid in prioritized_ids:
        if cid not in seen:
            seen.add(cid)
            ordered.append(int(cid))

    if task_id not in seen:
        ordered.insert(0, int(task_id))

    # Limit to top-k
    if k > 0:
        ordered = ordered[:k]

    # Final fallback to guarantee a non-empty list
    return ordered or [int(task_id)]