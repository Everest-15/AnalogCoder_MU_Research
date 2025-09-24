"""
Lightweight CLI entrypoint that defers heavy imports to speed up startup and
support running as both a module and a script.

Usage:
- python -m src.gpt_run
- python src/gpt_run.py
"""
import sys

def main() -> int:
    """Resolve and invoke the worker's main() regardless of import style."""
    # Defer heavy imports to keep entrypoint lightweight
    try:
        # When executed as a module (e.g., `python -m src.gpt_run`)
        from .worker import main as worker_main
    except ImportError:
        # When executed as a script (e.g., `python src/gpt_run.py`)
        # Fallback to absolute import from the same directory
        from worker import main as worker_main
    return worker_main()

if __name__ == "__main__":
    sys.exit(main())