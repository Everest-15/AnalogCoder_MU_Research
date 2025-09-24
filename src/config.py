"""
Configuration and CLI parsing utilities.

Defines AppConfig (runtime options) and parse_args() to build it from CLI flags.
"""
import argparse
from dataclasses import dataclass
from typing import Optional, List

OPEN_SOURCE_MODELS: List[str] = ["mistral", "wizardcoder", "deepseek-coder:33b-instruct", "codeqwen", "mixtral", "qwen"]
COMPLEX_TASK_TYPES = ['Oscillator', 'Integrator', 'Differentiator', 'Adder', 'Subtractor', 'Schmitt']

@dataclass
class AppConfig:
    """Container for application runtime configuration."""
    model: str
    temperature: float
    num_per_task: int
    num_of_retry: int
    num_of_done: int
    task_id: int
    ngspice: bool
    no_prompt: bool
    skill: bool
    no_context: bool
    no_chain: bool
    api_key: Optional[str]
    retrieval: bool

    @property
    def is_open_source_model(self) -> bool:
        """Return True if the model string suggests an open-source local model."""
        return any(m in self.model for m in OPEN_SOURCE_MODELS)

    @property
    def is_gpt_like(self) -> bool:
        """Return True for GPT-like hosted APIs (OpenAI/DeepSeek)."""
        return "gpt" in self.model or "deepseek-chat" in self.model

def parse_args() -> AppConfig:
    """Parse CLI flags into an AppConfig instance.

    Also resolves API key from explicit argument, local_secrets, or environment.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default="gpt-3.5-turbo")
    parser.add_argument('--temperature', type=float, default=0.5)
    parser.add_argument('--num_per_task', type=int, default=15)
    parser.add_argument('--num_of_retry', type=int, default=3)
    parser.add_argument("--num_of_done", type=int, default=0)
    parser.add_argument("--task_id", type=int, default=1)
    parser.add_argument("--ngspice", action="store_true", default=False)
    parser.add_argument("--no_prompt", action="store_true", default=False)
    parser.add_argument("--skill", action="store_true", default=False)
    parser.add_argument("--no_context", action="store_true", default=False)
    parser.add_argument("--no_chain", action="store_true", default=False)
    parser.add_argument('--api_key', type=str)
    parser.add_argument("--retrieval", action="store_true", default=False)
    args = parser.parse_args()

    # Python
    import os
    try:
        from src.local_secrets import OPENAI_API_KEY as LOCAL_KEY  # type: ignore
    except Exception:
        LOCAL_KEY = None

    api_key = args.api_key or LOCAL_KEY or os.getenv("OPENAI_API_KEY")

    num_of_retry = args.num_of_retry
    if args.skill:
        # With skills enabled prompts are longer/more specific; fewer retries keep costs bounded.
        num_of_retry = min(2, num_of_retry)

    return AppConfig(
        model=args.model,
        temperature=args.temperature,
        num_per_task=args.num_per_task,
        num_of_retry=num_of_retry,
        num_of_done=args.num_of_done,
        task_id=args.task_id,
        ngspice=args.ngspice,
        no_prompt=args.no_prompt,
        skill=args.skill,
        no_context=args.no_context,
        no_chain=args.no_chain,
        api_key=api_key,
        retrieval=args.retrieval,
    )