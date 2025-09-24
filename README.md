# AnalogCoder: Analog Circuit Design via Training-Free Code Generation

Repository status
- This repository is a working fork of the AnalogCoder project accompanying the paper “AnalogCoder: Analog Circuit Design via Training-Free Code Generation.” Some paths have been reorganized (for example, benchmark TSV files moved under data_files/ and prompt templates under templates/).
- Upstream reference: TODO: verify the official upstream URL (the previous README referenced both github.com/laiyao/analogcoder and github.com/laiyao1/analogcoder).

Overview
AnalogCoder is a training-free LLM-powered agent for analog circuit design. Given a textual task description (e.g., “design a low-pass filter with specified input/output nodes”), the agent crafts a domain-specific prompt, queries an LLM, extracts runnable Python code for simulation, and validates the result using PySpice-based checkers. It supports composing designs from a library of reusable “subcircuits” for more complex problems.

Key ideas
- Training-free flow with domain prompts, error handling, and feedback.
- Optional subcircuit skill library for composite designs (oscillator, integrator, differentiator, adder, subtractor, Schmitt trigger, etc.).
- Benchmark of 24 tasks; results are logged per iteration and model.

Stack and dependencies
- Language: Python (3.10+)
- Simulation: PySpice (1.5)
- LLM APIs: OpenAI-compatible clients (OpenAI, DeepSeek-compatible via base_url)
- Package/environment: Conda (environment.yml)
- Other scientific packages: numpy, pandas, scipy, matplotlib

Requirements
- Python 3.10 or newer
- Conda (recommended) with the provided environment file
- Access to an OpenAI-compatible LLM API (e.g., OpenAI, DeepSeek)

Create environment
- conda env create -f environment.yml
- conda activate analog

Environment check
A quick smoke test for the local SPICE execution can be run using included sample scripts:
- cd sample_design
- python test_all_sample_design.py
If you see “All tasks passed.” your environment is functioning. If failures occur, verify your Python environment and PySpice installation.

Project layout
- data_files/ — benchmark TSVs (problem_set.tsv, lib_info.tsv, teaser.png, etc.)
- extra/ — images and badges (AnalogCoder.png, AnalogCoder_label.png)
- outputs/ — generated outputs per model and task (it_*.md, code snippets)
- problem_check/ — checkers and test-benches
- sample_design/ — example scripts (p1.py … p24.py) and a test harness
- src/ — Python sources (entrypoints, config, prompts, LLM client, retrieval, analysis)
- subcircuit_lib/ — provided reusable circuit library
- templates/ — prompt templates and error-message templates
- environment.yml — Conda environment with Python dependencies

Entry points and how to run
The primary entry point delegates to a worker module:
- python src/gpt_run.py
- Alternatively, python -m src.gpt_run

Common flags (from src/config.py)
- --model: model name (default: gpt-3.5-turbo). OpenAI or DeepSeek models are supported via an OpenAI-compatible client.
- --temperature: sampling temperature (default: 0.5)
- --task_id: which benchmark task to run (default: 1)
- --num_per_task: number of attempts/iterations per task (default: 15)
- --num_of_retry: internal retry budget (default: 3; reduced when --skill is on)
- --num_of_done: starting iteration index (default: 0)
- --ngspice: use NGSPICE-specific prompt template
- --no_prompt | --no_context | --no_chain: ablation flags to switch templates
- --skill: enable the subcircuit library for complex tasks
- --retrieval: enable subcircuit retrieval for complex tasks
- --api_key: explicit API key (otherwise read from environment variables or local_secrets.py)

Quick start
Run a single task with default settings (reads API key from env if not provided):
- export OPENAI_API_KEY=your_key_here
- python src/gpt_run.py --task_id=1 --num_per_task=1
Outputs will be saved under outputs/<model>/<task_id>/ as markdown and code snippets.

Scripts
- Generate/augment the subcircuit tool library from generated basics:
  - python src/write_all_library.py
- Analyze and check generated code/netlists (used internally):
  - src/analysis.py (imported by the worker; not a CLI by itself)

Benchmark assets
- Task descriptions: data_files/problem_set.tsv
- Provided circuit snippets: sample_design/
- Test-benches: problem_check/

Environment variables and secrets
- OPENAI_API_KEY: API key for OpenAI-compatible models (preferred)
- DEEPSEEK_API_KEY: API key for DeepSeek when using a DeepSeek-chat model
- Optional local file: local_secrets.py may define OPENAI_API_KEY or DEEPSEEK_API_KEY constants as a fallback.
Notes
- Avoid hardcoding secrets in code or README. The previous README displayed a real-looking key; do not do this. Remove or override the example with environment variables as shown above.
- The provided local_secrets.py currently contains OPEN_API_KEY, which is not read by the code paths. If you use local_secrets.py, rename the constant to OPENAI_API_KEY (and/or DEEPSEEK_API_KEY) to match src/llm_client.py expectations. TODO: align naming across the repo if needed.

Testing
- Sample functional test:
  - cd sample_design
  - python test_all_sample_design.py
- Basic LLM flow smoke test:
  - export OPENAI_API_KEY=your_key
  - python src/gpt_run.py --task_id=1 --num_per_task=1 --model=gpt-3.5-turbo

Outputs and logs
- outputs/<model>/<task_id>/it*.md: raw LLM responses
- outputs/<model>/<task_id>/it_*.py: extracted runnable snippets
- Timestamped *_log.txt files in the project root capture run summaries

License
- TODO: Add a LICENSE file to clarify usage terms. If this is intended to mirror an upstream project, copy the upstream license and reference it here.

Citations and results
The following table (from prior experiments) summarizes performance across models.

| LLM Model               |      Avg. Pass@1 |      Avg. Pass@5 |     # of Solved |
|-------------------------|-----------------:|-----------------:|----------------:|
| Llama2-7B               |              0.0 |              0.0 |               0 |
| Llama2-13B              |              0.0 |              0.0 |               0 |
| Llama3-8B               |              0.1 |              0.7 |               1 |
| CodeLlama-13B           |              0.6 |              2.5 |               2 |
| Mistral-7B              |              3.3 |              7.7 |               2 |
| Qwen-1.5-110B           |              0.3 |              1.4 |               2 |
| Llama 2-70B             |              5.1 |              9.8 |               3 |
| CodeLlama-7B            |              2.4 |              9.0 |               4 |
| CodeLlama-34B           |              1.9 |              7.4 |               4 |
| QwenCode-7B             |              1.1 |              5.6 |               4 |
| DeepSeek-Coder-33B      |              4.0 |             10.2 |               4 |
| Mixtral-8×7B            |              5.6 |             12.4 |               5 |
| CodeLlama-70B           |              3.2 |             12.2 |               7 |
| WizardCoder-33B         |              7.1 |             16.9 |               7 |
| GPT-3.5 (w/o context)   |              8.1 |             18.5 |               7 |
| GPT-3.5 (w/o CoT)       |             19.4 |             26.3 |               8 |
| GPT-3.5 (w/o flow)      |             12.8 |             25.3 |               8 |
| Codestral-22B           |             16.4 |             29.1 |               8 |
| GPT-3.5 (SPICE)         |             13.9 |             26.9 |               9 |
| GPT-3.5                 |             21.4 |             35.0 |              10 |
| GPT-3.5 (fine-tune)     |             28.1 |             39.6 |              10 |
| Llama3-70B              |             28.8 |             36.4 |              11 |
| DeepSeek-V2             |             38.6 |             44.3 |              13 |
| GPT-4o (w/o tool)       |             54.2 |             58.9 |              15 |
| AnalogCoder             |             66.1 |             75.9 |              20 |

Notes
1) All results above are meant to be reproducible given the environment and seeds.
2) The environment requires no sudo privileges.
