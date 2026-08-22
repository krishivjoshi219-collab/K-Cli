# K-CLI

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> A verification-first, multi-model coding agent for the terminal.

K-CLI helps you inspect a repository, plan a change, generate a minimal implementation, and verify the result locally before accepting it. It is built for developers who want a capable agent workflow on modest hardware, with optional local and cloud model providers.

## Why K-CLI

- **Verification before confidence** — Python AST/compile/pytest, Bash syntax, and C++ syntax guards give generated code a real local check.
- **3-Way AI Merge Conflict Resolver** — Resolves Git merge conflicts automatically using AST scope context, 3-way semantic synthesis, and local compiler verification.
- **GitHub PR Lifecycle in Terminal** — Review PRs, fix CI/CD failures, run compiler-grade AI code reviews, and auto-merge pull requests directly from your terminal.
- **Universal Model Context Protocol (MCP)** — Connects to any MCP server (GitHub, SQLite, DevDocs, Docker, PostgreSQL) with dynamic tool discovery and execution.
- **Deduplication & Anti-Overlap** — Scans Git history and AST symbol tables to alert you if a bug or feature is already solved in existing code.
- **Crash Log & Incident Healer** — Ingests raw stack traces (Python, Node, Rust, Go, C++, Docker) and automatically generates regression tests and verified patches.
- **Smart Conventional Commits** — Analyzes staged/unstaged diffs with AST inspection to produce clean Conventional Commits and rich PR descriptions.
- **Autonomous Security Healer** — Scans and auto-patches hardcoded secrets, SQL injection, unsafe `eval()`, ReDoS, and shell injections.
- **Cyber-TUI Workstation & Live Studio** — Interactive 3-Way Conflict Studio, GitHub PR Hub, MCP Inspector, Swarm Radar, and real-time token/cost speedometers.

K-CLI does not claim generated code is correct merely because it looks convincing. A successful result is one that passed the selected local verification guard.

**Execution safety:** verification runs generated code and supplied tests as credential-filtered, resource-limited local subprocesses with timeout cleanup. It is not a security sandbox and can still access the caller's filesystem and network. Do not verify untrusted code on a sensitive machine; use a disposable container or VM for untrusted repositories.

Optional project guidance can be supplied with `--rules .kcli/rules.md` on `run`, `plan`, and `prompt`. K-CLI bounds this file and labels it as untrusted repository context; it is never treated as executable policy.

CI integrations can consume stable JSON from all commands using `--json`.

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

# Resolve all merge conflicts in current repository with AI & AST verification
k-cli conflict resolve

# Review and auto-fix an open GitHub Pull Request
k-cli pr review 42
k-cli pr fix 42 --auto-push

# Connect to any Model Context Protocol (MCP) server
k-cli mcp add github npx -a "-y @modelcontextprotocol/server-github"

# Generate smart Conventional Commit and stage
k-cli commit --push

# Scan and surgically heal security vulnerabilities
k-cli security scan
k-cli security heal --all

# Launch the interactive Textual Cyber-Workstation
k-cli ui
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

## Universal Python SDK

K-CLI can be imported directly into Python applications as an agentic framework:

```python
from k_cli import KCLI

# 1. Initialize K-CLI Agent
with KCLI(model="deepseek-reasoner", local_fallback="qwen2.5-coder:1.5b") as kcli:
    # 2. Multi-Model Inference across local SLMs & Cloud LLMs
    response = kcli.generate("Write a lock-free ring buffer in C++23")

    # 3. Autonomous GitHub Operations
    kcli.github.solve_issue(issue_number=42, auto_pr=True)
    kcli.github.create_release(tag_name="v1.0.0")

    # 4. AST Merge Conflict Studio & Security Auto-Healer
    kcli.conflicts.resolve_all()
    kcli.security.heal_all()

    # 5. Visual Mermaid Architecture Generator
    kcli.diagrams.generate_mermaid_architecture(output_file="ARCHITECTURE.md")
```

## Commands

| Command | What it does |
| --- | --- |
| `k-cli` | Opens the interactive shell with slash commands, streaming animations, and history. |
| `k-cli ui` | Launches the full-screen Textual Cyber-Workstation with 3-Way Conflict Studio and PR Hub. |
| `k-cli models list` | Lists all local SLMs (Ollama, llama.cpp, GGUF) and cloud models with context & pricing. |
| `k-cli models test <model>` | Benchmarks model throughput (tok/s), Time-to-First-Token (TTFT), and RAM RSS. |
| `k-cli models pull <model>` | Pulls local model weights onto machine via Ollama daemon. |
| `k-cli models providers` | Inspects active API keys and local daemon connectivity across all providers. |
| `k-cli gh issues` / `k-cli issue list` | Lists open issues with labels, authors, and comment counts. |
| `k-cli gh solve <issue_num>` | Autonomously investigates an issue, generates verified fixes, commits, and opens a PR. |
| `k-cli gh releases` / `release list` | Lists releases and published assets. |
| `k-cli release create <tag>` | Synthesizes an AST Conventional Changelog and publishes a GitHub release. |
| `k-cli gh actions` / `action runs` | Lists GitHub Actions CI/CD runs and step execution statuses. |
| `k-cli gist create <file>` | Creates public or secret GitHub Gists directly from files. |
| `k-cli conflict list` | Scans repository and lists all active 2-way and 3-way Git merge conflicts. |
| `k-cli conflict resolve` | Automatically resolves merge conflicts with AI and runs local AST/test verification. |
| `k-cli pr list` | Lists open/closed GitHub PRs with conflict tags, review state, and CI status pills. |
| `k-cli pr view <pr_num>` | Inspects PR details, commit history, and diff summary in terminal. |
| `k-cli pr review <pr_num>` | Performs multi-model code review with security, performance, and line suggestions. |
| `k-cli pr fix <pr_num>` | Checks out PR branch, analyzes review/CI failures, generates verified fixes, and pushes. |
| `k-cli pr merge <pr_num>` | Validates CI status and local test suite, then merges PR via GitHub API. |
| `k-cli mcp list` | Lists configured MCP servers and active connection states. |
| `k-cli mcp add <name> <cmd>` | Registers a new stdio or SSE/HTTP Model Context Protocol server. |
| `k-cli mcp tools` | Discovers available tools across all connected MCP servers. |
| `k-cli mcp call <tool> <args>` | Executes an MCP tool with JSON arguments directly from the command line. |
| `k-cli dedup check "goal"` | Scans Git commits and AST symbol maps to detect if a task is already completed. |
| `k-cli commit [--push]` | Generates AST-grounded Conventional Commits and stages/pushes atomic changes. |
| `k-cli security scan` | High-speed AST & regex scan for API keys, SQL injection, unsafe eval, and ReDoS. |
| `k-cli security heal` | Surgically auto-heals security vulnerabilities with verified AST replacements. |
| `k-cli triage "trace/log"` | Diagnoses crash logs, isolates culprit source lines, and auto-heals incidents. |
| `k-cli plan "goal"` | Builds a protected, read-only change plan with deduplication detection. |
| `k-cli run "task"` | Runs the persona pipeline and verifies generated code locally. |
| `k-cli audit "task"` | Independently generates candidates across multiple models and verifies each one. |
| `k-cli feature "name"` | Checks implementation and test evidence for a requested feature. |
| `k-cli verify file.py` | Verifies an existing Python, Bash, or C++ file against AST/compilers/test suites. |
| `k-cli subagents "task"` | Decomposes complex tasks across parallel role-specialized subagents. |
| `k-cli map` | Prints a token-budgeted PageRank AST map of the current codebase. |
| `k-cli doc <symbol>` | High-speed offline SQLite FTS5 DevDocs documentation search (< 5ms). |
| `k-cli diff` | Renders color-coded side-by-side or inline working-tree diffs. |
| `k-cli doctor` | Shows installation, Git, model runtime, and safety diagnostics. |

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
