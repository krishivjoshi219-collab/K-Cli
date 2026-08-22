# K-CLI ⚡ Sovereign Agentic Coding Workstation

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests: 255 Passed](https://img.shields.io/badge/tests-255%20passed%20(100%25)-brightgreen.svg)](tests/)
[![Security: CodeQL Verified](https://img.shields.io/badge/security-CodeQL%20Verified-blueviolet.svg)](.github/workflows/codeql.yml)
[![Offline Sovereign Mode](https://img.shields.io/badge/offline-100%25%20air--gapped%20ready-orange.svg)](#-4-k-cli-airgap--100-sovereign-offline-mode)

> **The compiler-grounded, multi-model AI coding agent & terminal workstation with 10 autonomous superpowers.**
> A complete fusion of **Claude Code**, **Google Antigravity (AGY)**, **GitHub Copilot CLI**, and **Cursor** in your terminal. Zero cloud lock-in, 1-click zero-typing UI, local SLM support, adversarial self-healing loops, and compiler verification gates.

---

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ⚡ K-CLI AGENT │ 🤖 Gemini 2.0 Flash │  main (+1 ~0) │ 💾 184MB RSS │ 🏎️ 185 tok/s │ 💰 $0.002 │ 🛡️ AST OK│
├─────────────────────────┬─────────────────────────────────────────────────┬────────────────────────────┤
│ 🚀 1-CLICK LAUNCHER     │  👑 K-CLI Agentic Workstation                   │  📜 PENDING DIFFS          │
│  [ 🔑 API Key Vault ]   │                                                 │   • main.py (+12 -3)       │
│  [ ⚔️ Merge Conflicts ] │  **User**: Refactor auth token validation       │                            │
│  [ 🐙 GitHub Center ]   │                                                 │  ⚡ BACKGROUND TASKS       │
│  [ 🤖 Model Hub ]       │  ╭─ 🧠 Thinking (1.2s)... (Click to expand) ──╮  │   • Verifier: Idle         │
│  [ 🛡️ Security Healer ] │  │  • Resolving AST symbol dependencies       │  │   • Swarm: Active          │
│  [ 🚨 Incident Triage ] │  ╰────────────────────────────────────────────╯  │                            │
│  [ 📊 Architecture ]    │                                                 │  📊 TELEMETRY GAUGE        │
│                         │  **K-CLI Agent**: Applied zero-allocation       │   • TTFT: 0.12s            │
│ 📁 CONTEXT PINS         │  JWT parser with constant-time HMAC check.      │   • Throughput: 185 tok/s  │
│  • @main.py             │                                                 │   • Cache Hit: 94%         │
│  • @orchestrator.py     │  ╭─ 🛠️ Tool: patch_file [auth.py] ────────────╮  │                            │
│  • @sdk.py              │  │  [ 🟢 Allow ] [ 🔴 Deny ] [ 🛡️ Test ]      │  │                            │
│                         │  ╰────────────────────────────────────────────╯  │                            │
│ 🐝 SWARM RADAR          ├─────────────────────────────────────────────────┤                            │
│  🟢 Researcher: Ready   │ [ ⚡ Plan ] [ ⚔️ Conflict ] [ 🐙 GitHub ]         │                            │
│  🟣 Architect: Ready    │ [ 🔑 Keys ] [ 🤖 Models ] [ 🛡️ Security ] [ 🧹 ]  │                            │
│  🔵 Coder: Active       ├─────────────────────────────────────────────────┤                            │
│  🟡 Critic: Ready       │ > Ask K-CLI anything or click a 1-Click button  │                            │
│  🔴 Debugger: Ready     │                                                 │                            │
└─────────────────────────┴─────────────────────────────────────────────────┴────────────────────────────┘
```

---

## ⚡ Quick Start

```bash
# 1. Clone & Install
git clone https://github.com/krishivjoshi219-collab/K-Cli.git
cd K-Cli
python -m venv .venv && source .venv/bin/activate
pip install -e .

# 2. Launch Flagship Cyber-Workstation (Clean terminal, 1-click UI)
k-cli ui

# 3. Or use single-shot agent commands
k-cli run "Implement a lock-free queue in Python with thread-safe atomics"
```

---

## 🔥 The 10 Autonomous Superpowers

### 👻 1. `k-cli ghost` — Ghost Terminal Autopilot (Live Crash Healer)
Attach K-CLI to any dev server, compiler, or test runner. Whenever an error or stack trace occurs, K-CLI intercepts the traceback in the background, writes a verified patch, and presents a 1-click terminal fix prompt:

```bash
k-cli ghost "npm run dev"
# or: k-cli ghost "pytest -f"
# or: k-cli ghost "cargo run"

# 👻 K-CLI GHOST AUTOPILOT TRIGGERED:
# ▸ Intercepted TypeError at src/middleware/auth.ts:42
# ▸ Synthesizing verified patch in background...
# [ 🟢 Press (Y) to Apply Surgical Patch | (D) View Diff | (N) Dismiss ]
```

### 🐝 2. `k-cli swarm` — Adversarial Consensus Loop (Zero Hallucinations)
Runs a 3-agent adversarial loop where **Blue Team (Coder)** writes code, **Red Team (Adversarial Critic)** generates exploit & stress tests (race conditions, memory leaks, null values), and **Judge (Ground-Truth Compiler)** runs tests before anything touches disk:

```bash
k-cli swarm "Implement a high-throughput ring buffer in C++23" --rounds 3
# 🔵 Blue Agent: Synthesizing lock-free ring buffer...
# 🔴 Red Team Attack: 64 concurrent threads + ABA pointer race test...
# ⚖️ Judge: Running Clang ThreadSanitizer (-fsanitize=thread)...
# ✔ 100/100 tests passed, 0 Tsan errors, 0 memory leaks!
```

### 🧠 3. `k-cli synapse` — AST Code Graph (95%+ Context Compression)
Builds an AST symbol call graph of the codebase and extracts only the minimal surgical subgraph needed for prompt context (<1,000 tokens), speeding up responses 10x and slashing API costs:

```bash
k-cli synapse "refactor database transaction rollback"
# ▸ Full repo tokens: 1,200,000 ($3.60 on Claude 3.5 Sonnet)
# ▸ Synapse subgraph: 940 tokens ($0.0028 on Claude 3.5 Sonnet)
# ▸ Compression: 99.7% | Speed: 0.9s
```

### 🛡️ 4. `k-cli airgap` — 100% Sovereign Offline Mode
Guarantees zero outbound network packets and air-gapped security for enterprise, defense, and healthcare environments using local SLMs (Ollama / llama.cpp / GGUF):

```bash
k-cli airgap
# 🛡️ SOVEREIGN AIR-GAP ACTIVE:
# • Outbound Network: 🚫 BLOCKED (0 bytes transmitted)
# • Local Toolchains: Python AST, GCC/Clang, rustc, Git
# • Local SLMs: qwen2.5-coder (100% local CPU/GPU)
```

### 🎯 5. `k-cli bisect` — AI Git Bisect & Bug Hunter
Automates binary search across git commit history with an AI oracle to pinpoint the exact commit that introduced a bug, explains the root cause diff, and proposes a fix:

```bash
k-cli bisect "pytest tests/ -q" --good HEAD~10 --bad HEAD
# ▸ Isolated culprit commit: a3f921b ("refactor decimal precision")
# ▸ Root cause: Precision truncated when order_total > 1000
# ▸ Surgical fix synthesized & verified ✔
```

### 👁️ 6. `k-cli watch` — 24/7 Autonomous PR Review & Merge Bot
Monitors your GitHub repository for open PRs, performs multi-criteria reviews (security, edge cases, performance), posts review comments, and auto-merges when CI passes:

```bash
k-cli watch --interval 30 --auto-merge
# ▸ Watching for PRs...
# ▸ PR #42 opened: Running compiler-grade code review...
# ▸ Posted review comments + Approved ✔
# ▸ CI checks passed → Auto-merged pull request #42 (squash)
```

### ⚡ 7. `k-cli route` — Cost & Latency Smart Model Router
Analyzes task complexity (0–100) and automatically routes cheap tasks to local SLMs (free), medium tasks to DeepSeek/Groq, and heavy tasks to Claude/GPT-4, calculating real-time dollar savings:

```bash
k-cli route "fix typo in docstring"
# ▸ Tier: TRIVIAL → Routed to Local Ollama (FREE) | Saved: $0.0300 vs GPT-4

k-cli route "architect distributed consensus protocol"
# ▸ Tier: COMPLEX → Routed to Claude 3.5 Sonnet ($0.003) | Saved: $0.0270 vs GPT-4
```

### 🌿 8. `k-cli garden` — Nightly Autonomous Repo Maintenance
Sweeps your repository for dead/unreferenced functions, unpinned dependencies, and untracked technical debt, outputting actionable health scores or clean maintenance PRs:

```bash
k-cli garden
# 🌿 Repo Health Score: 94.5/100
# • Dead code: 2 unreferenced functions detected in utils/
# • Outdated deps: 1 unpinned dependency in requirements.txt
```

### 💬 9. `k-cli explain` — Codebase Natural Language Search & Q&A
Ask architectural, security, or structural questions about your codebase in plain English with zero data leaves your machine:

```bash
k-cli explain "Where does JWT token authentication and role checking happen?"
# ▸ Flow: middleware/auth.py:42 → models/user.py:18 → utils/jwt.py:12
# ▸ Referenced symbols: `authenticate_request`, `verify_jwt_claims`
```

### 🏗️ 10. `k-cli scaffold` — Natural Language Full-Stack Engine
Turns a 1-line natural language prompt into a complete, production-grade, multi-file, tested, and compiling application architecture with Docker configs:

```bash
k-cli scaffold "FastAPI + SQLAlchemy 2.0 Async + Redis Cache + Pytest + Docker" --write
# 🏗️ Scaffolded 5 production files:
# • main.py (Entry point)
# • config.py (Security & env)
# • models.py (Domain models)
# • Dockerfile (Multi-stage container)
# • tests/test_main.py (Pytest integration suite)
# ✔ 100% AST Valid
```

---

## 🔑 Dedicated 1-Click Modals

Press the global hotkeys anywhere in the terminal workstation:

| Hotkey | Modal | Capabilities |
| :---: | :--- | :--- |
| **`Ctrl+A`** | **Credentials Vault** | Configure and live-test all API keys at once (OpenAI, Claude, Gemini, DeepSeek, Groq, Mistral, GitHub, Ollama). |
| **`Ctrl+K`** | **4-Way Conflict Studio** | Visual merge conflict studio (`Ours` vs `Base` vs `Theirs` vs `AI Resolved`) with compiler test gates. |
| **`Ctrl+G`** | **GitHub Command Center** | Autonomous Issue Solver, PR reviews, CI failure log parser, and release publisher. |
| **`Ctrl+M`** | **Model Hub** | Switch active local SLMs & cloud LLMs with live TTFT and throughput (`tok/s`) benchmarking. |
| **`Ctrl+S`** | **AST Security Healer** | Static AST vulnerability scanner with 1-click surgical auto-healer. |
| **`Ctrl+L`** | **Clear Workspace** | Clean workspace canvas. |

---

## 🐍 Universal Python SDK

Import K-CLI directly into your Python pipelines and scripts:

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

    # 5. Smart Model Routing & Synapse Graph
    route = kcli.route("refactor payment engine")
    subgraph = kcli.synapse("payment_worker")

    # 6. Ghost Terminal & Adversarial Swarms
    kcli.swarm_adversarial("binary search algorithm")
    kcli.scaffold("FastAPI + Redis App", write_to_disk=True)
```

---

## 📁 Repository Structure

```
K-Cli/
├── k_cli/                        ← Installable Python package
│   ├── core/                     ← LLM driver, Models Hub, SDK, Smart Router, Airgap
│   │   ├── llm_driver.py
│   │   ├── models_hub.py
│   │   ├── smart_router.py
│   │   ├── airgap.py
│   │   ├── sdk.py
│   │   ├── session.py
│   │   └── prompting.py
│   │
│   ├── github/                   ← GitHub API, PR Lifecycle, PR Watcher, Dedup
│   │   ├── github_engine.py
│   │   ├── github_client.py
│   │   ├── pr_watcher.py
│   │   └── dedup_engine.py
│   │
│   ├── git/                      ← Conflict resolver, AI Bisect, Smart git, Patcher, Verifier
│   │   ├── conflict_resolver.py
│   │   ├── ai_bisect.py
│   │   ├── smart_git.py
│   │   ├── patcher.py
│   │   ├── verifier.py
│   │   ├── git_guard.py
│   │   └── repo_map.py
│   │
│   ├── tui/                      ← Flagship 3-Column TUI Workstation (Textual)
│   │   ├── tui_app.py
│   │   ├── tui.py
│   │   ├── tui_animations.py
│   │   └── diff_viewer.py
│   │
│   ├── agents/                   ← Orchestrator, Adversarial Swarm, Scaffolder, Personas
│   │   ├── orchestrator.py
│   │   ├── subagents.py
│   │   ├── adversarial_swarm.py
│   │   ├── scaffold_engine.py
│   │   └── persona.py
│   │
│   ├── tools/                    ← Ghost Daemon, Synapse Graph, Repo Gardener, Q&A, Security
│   │   ├── ghost_daemon.py
│   │   ├── synapse_graph.py
│   │   ├── repo_gardener.py
│   │   ├── codebase_qa.py
│   │   ├── security_healer.py
│   │   ├── incident_triage.py
│   │   ├── diagram_generator.py
│   │   ├── mcp_client.py
│   │   └── doc_retriever.py
│   │
│   ├── cli.py                    ← Single Typer CLI entrypoint
│   └── __init__.py               ← Public SDK exports
│
├── tests/                        ← 255 passing test cases across 16 test suites
├── docs/                         ← Architecture & documentation
├── .github/workflows/            ← CI/CD & CodeQL security scans
├── pyproject.toml                ← Package configuration
└── LICENSE                       ← MIT License
```

---

## 🧪 Testing & Verification

K-CLI is verified by a 255-test suite covering AST safety, binary bisect searches, subagent DAG scheduling, mock telemetry, and security vulnerability healing:

```bash
pytest tests/ -v
# ============================= 255 passed in 31.40s (100%) ======================
```

---

## 📄 License

MIT License — free for individual developers, open-source projects, and commercial teams.
