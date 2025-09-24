"""
LLM client wrapper around OpenAI/DeepSeek-compatible chat APIs with robust key
resolution and retry logic. Also contains prompt template utilities (legacy).
"""
import time
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import httpx
import openai
from openai import OpenAI
import os  # Added to read environment variables

from src.config import AppConfig, COMPLEX_TASK_TYPES

BIAS_USAGE = """Due to the operational range of the op-amp being 0 to 5V, please connect the nodes that were originally grounded to a 2.5V DC power source.
Please increase the gain as much as possible to maintain oscillation.
"""

def _project_root() -> Path:
    # src/ -> project root
    return Path(__file__).resolve().parent.parent

def _read_file_project_relative(rel_path: str) -> str:
    path = _project_root() / rel_path
    with open(path, "r") as f:
        return f.read()

def base_prompt_for(config: AppConfig) -> str:
    # Select prompt template under templates/
    if config.no_prompt:
        rel = 'templates/prompt_template_wo_prompt.md'
    elif config.no_context:
        rel = 'templates/prompt_template_wo_context.md'
    elif config.no_chain:
        rel = 'templates/prompt_template_wo_chain_of_thought.md'
    elif config.ngspice:
        rel = 'templates/prompt_template_ngspice.md'
    else:
        rel = 'templates/prompt_template.md'
    return _read_file_project_relative(rel)

def complex_prompt_template() -> str:
    return _read_file_project_relative('templates/prompt_template_complex.md')

def simulation_error_prompt() -> str:
    return _read_file_project_relative('templates/simulation_error.md')

def execution_error_prompt() -> str:
    return _read_file_project_relative('templates/execution_error.md')

def build_prompt(config: AppConfig, task: str, input_nodes: str, output_nodes: str, task_type: str,
                 subcircuits_info: str = "", note_info: str = "", call_info: str = "") -> Tuple[str, float]:
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


class LLMResponse:
    def __init__(self, text: str, total_tokens: int = 0, prompt_tokens: int = 0, completion_tokens: int = 0):
        self.text = text
        self.total_tokens = total_tokens
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class LLMClient:
    def __init__(self, model: str, api_key: Optional[str]):
        self.model = model
        # Respect provided api_key or environment configuration; never hardcode secrets.
        self.api_key = api_key
        self.client: Optional[OpenAI] = None
        self._init_client()

    def _init_client(self):
        """Initialize the underlying OpenAI-compatible client with timeouts and key resolution.

        The API key is resolved from (in order): explicit arg -> environment -> local_secrets.
        Also switches base_url for DeepSeek-compatible endpoints.
        """
        # Configure a client with explicit timeouts to prevent indefinite hangs.
        # httpx timeout in seconds
        http_timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)

        # Resolve API key robustly with fallbacks
        model_lower = (self.model or "").lower()
        is_deepseek = "deepseek-chat" in model_lower

        # 1) explicit arg
        resolved_key: Optional[str] = self.api_key

        # 2) env vars
        if not resolved_key:
            if is_deepseek:
                resolved_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
            else:
                resolved_key = os.getenv("OPENAI_API_KEY")

        # 3) local_secrets.py (project-root level) if still missing
        if not resolved_key:
            try:
                # Import lazily to avoid hard dependency
                import local_secrets  # type: ignore
                if is_deepseek:
                    resolved_key = getattr(local_secrets, "DEEPSEEK_API_KEY", None) or getattr(local_secrets, "OPENAI_API_KEY", None)
                else:
                    resolved_key = getattr(local_secrets, "OPENAI_API_KEY", None)
            except Exception:
                # Ignore import errors; we will raise a clear message below if still missing
                pass

        if not resolved_key:
            provider_name = "DeepSeek (DEEPSEEK_API_KEY or OPENAI_API_KEY)" if is_deepseek else "OpenAI (OPENAI_API_KEY)"
            raise ValueError(
                f"Missing API key for {provider_name}. "
                f"Provide api_key via config, set the environment variable, or define it in local_secrets.py."
            )

        # Instantiate the client; non-OpenAI models (e.g., local) set client to None.
        if "gpt" in model_lower and not is_deepseek:
            self.client = OpenAI(api_key=resolved_key, timeout=http_timeout)
        elif is_deepseek:
            self.client = OpenAI(api_key=resolved_key, base_url="https://api.deepseek.com/v1", timeout=http_timeout)
        else:
            self.client = None  # ollama or others handled via chat_ollama

    def chat_openai(self, messages: List[Dict[str, str]], temperature: float) -> LLMResponse:
        """Call the chat completion API with retries and return a normalized response."""
        assert self.client is not None
        # Bounded retries with exponential backoff
        max_retries = 5
        backoff = 2.0
        last_err: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    timeout=30.0,  # per-request timeout (seconds)
                )
                content = completion.choices[0].message.content
                usage = completion.usage
                return LLMResponse(
                    text=content or "",
                    total_tokens=getattr(usage, "total_tokens", 0),
                    prompt_tokens=getattr(usage, "prompt_tokens", 0),
                    completion_tokens=getattr(usage, "completion_tokens", 0),
                )
            except (openai.APIStatusError, openai.RateLimitError) as e:
                # Retry on service or rate issues with a growing backoff up to a cap
                last_err = e
                time.sleep(min(60.0, backoff))
                backoff *= 2.0
            except (openai.APIConnectionError, httpx.TimeoutException, httpx.HTTPError) as e:
                # Retry on transient network failures
                last_err = e
                time.sleep(min(30.0, backoff))
                backoff *= 2.0
            except Exception as e:
                # Non-retryable or unexpected
                last_err = e
                break
        # If we reach here, all retries failed
        if last_err:
            raise last_err
        raise RuntimeError("chat_openai failed without an exception (unexpected)")

    def is_openai_like(self) -> bool:
        """Return True for hosted chat APIs that use the OpenAI schema."""
        return "gpt" in self.model or "deepseek-chat" in self.model