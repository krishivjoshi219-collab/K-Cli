# K-CLI

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> A verification-first, multi-model coding agent for the terminal.

K-CLI helps you inspect a repository, plan a change, generate a minimal implementation, and verify the result locally before accepting it. It is built for developers who want a capable agent workflow on modest hardware, with optional local and cloud model providers.

## Why K-CLI

- **Verification before confidence** — Python AST/compile/pytest, Bash syntax, and C++ syntax guards give generated code a real local check.
- **Protected planning** — `k-cli plan` inspects a workspace and proposes a path without editing files.
- **Agent workflows** — focused personas, repository maps, offline DevDocs search, diff previews, Git checkpoints, and subagent task decomposition.
- **Local first, provider-flexible** — supports Ollama and compatible cloud providers when configured.
- **A proper terminal experience** — rich streaming output for daily use and a full Textual workstation for an immersive UI.

K-CLI does not claim generated code is correct merely because it looks convincing. A successful result is one that passed the selected local verification guard.

**Execution safety:** verification runs generated code and supplied tests as credential-filtered, resource-limited local subprocesses with timeout cleanup. It is not a security sandbox and can still access the caller's filesystem and network. Do not verify untrusted code on a sensitive machine; use a disposable container or VM for untrusted repositories.

Optional project guidance can be supplied with `--rules .kcli/rules.md` on `run`, `plan`, and `prompt`. K-CLI bounds this file and labels it as untrusted repository context; it is never treated as executable policy.

CI integrations can consume stable JSON from `k-cli plan ... --json`, `k-cli doctor --json`, `k-cli verify --json`, and `k-cli audit --json`.

## Quick start

K-CLI requires Python 3.11+.

```bash
# From a checkout of this repository:
cd k-cli
python -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .

# Check your local setup
k-cli doctor

# Create a read-only plan before you edit
k-cli plan "add structured logging to the API client"

# Generate and verify a small implementation (no model download required)
k-cli run "write a Python function that normalizes an email address" --mock
```

For local inference, install [Ollama](https://ollama.com/) and pull a coding model:

```bash
ollama pull qwen2.5-coder:1.5b
k-cli "add a timeout parameter to the HTTP client"
```

### Bring your own model endpoint

K-CLI supports Ollama, llama.cpp, native GGUF, OpenAI, Anthropic, Gemini,
DeepSeek, OpenRouter, and any endpoint implementing the OpenAI chat-completions
protocol (including common self-hosted and gateway deployments). Model output is
always treated as a candidate and goes through the same local verification flow.

```bash
export KCLI_API_KEY="your-provider-token"
k-cli run "add retry handling" \
  --model "your-coding-model" \
  --provider openai-compatible \
  --base-url "https://your-endpoint.example/v1"
```

## Commands

| Command | What it does |
| --- | --- |
| `k-cli` | Opens the interactive shell with slash commands and history. |
| `k-cli plan "goal"` | Builds a protected, read-only change plan. |
| `k-cli run "task"` | Runs the persona pipeline and verifies generated code. |
| `k-cli prompt "task" --model gemini` | Previews a compact model-aware prompt contract. |
| `k-cli audit "task" --models model-a,model-b` | Independently generates candidates and locally verifies each one. |
| `k-cli mesh "task" --targets gemini:gemini-2.5-pro,openrouter:anthropic/claude-3.7-sonnet` | Runs one task across many models at the same time with verification results. |
| `k-cli model-index --query coder` | Fetches a global web model index and inferred specialties. |
| `k-cli key-set --provider openai --key ...` | Stores provider API keys in keyring or encrypted local vault fallback. |
| `k-cli feature "capability" --require-tests` | Checks implementation and test evidence for a requested feature. |
| `k-cli verify file.py` | Verifies an existing Python, Bash, or C++ file. |
| `k-cli subagents "task"` | Decomposes a complex task into explorer, researcher, refactorer, and tester roles. |
| `k-cli map` | Prints a token-budgeted AST map of the current codebase. |
| `k-cli doc asyncio.Queue` | Searches the local DevDocs SQLite index. |
| `k-cli diff` | Renders the working-tree diff. |
| `k-cli review` | Performs a read-only AST review of changed Python files; supports `--json`. |
| `k-cli doctor` | Shows install, Git, model-runtime, and safety diagnostics. |
| `k-cli ui --mock` | Launches the full-screen Textual workstation. |

### Project guidance, without hidden policy

Use an explicit, reviewable rule file when a repository has conventions worth carrying into a task:

```text
# .kcli/rules.md
Keep public interfaces backward compatible.
Run focused tests before the full suite.
```

```bash
k-cli plan "add retry handling" --rules .kcli/rules.md
k-cli run "add retry handling" --rules .kcli/rules.md --mock
```

The command output preserves the guidance with an untrusted-context label, making the influence on the plan or prompt visible during review.

## Safe workflow

```text
plan → inspect → generate → verify → review → diff → apply/commit
```

Use `plan` when you want the agent to understand the work before changing it. Use `run` for isolated code generation and `subagents` for broader research/refactor/test tasks. Review diffs before applying patches to a real repository.

`audit` intentionally does not auto-apply a winner. It reports each candidate's independent local verification result so you can compare candidates and retain final control.

## Providers and configuration

Copy `.env.example` to `.env` only for local use. Never commit it. Provider credentials are read from environment variables such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GEMINI_API_KEY`.

For secure key handling, prefer `k-cli key-set ...` so credentials stay in OS keyring when available. If keyring is unavailable, K-CLI uses an encrypted local fallback that requires `KCLI_VAULT_PASSPHRASE`.

`HF_TOKEN` is only for optional private model publishing or training workflows. Training data, notebooks, model weights, and generated benchmark artifacts are intentionally excluded from the GitHub package. Keep reproducible training/evaluation work in a separate, documented repository or release artifact.

## Verification scope

K-CLI can verify syntax, compilation, and user-supplied tests. It cannot prove product correctness, security, or benchmark performance. Treat verification as a strong feedback loop, then review important changes as you normally would.

## Development

```bash
python -m pytest -q
python -m compileall -q .
```

The test suite runs offline by default using mock drivers. GitHub Actions runs it on Python 3.11 and 3.12. The repository currently includes unit, integration, adversarial, and end-to-end tests; run the command above for the authoritative result.

## Contributing and security

Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Please report security issues privately; see [SECURITY.md](SECURITY.md). The project is released under the [MIT License](LICENSE).
