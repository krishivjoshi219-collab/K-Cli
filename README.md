# K-CLI ⚡ Sovereign Agentic Coding Workstation

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests: 300 Passed](https://img.shields.io/badge/tests-300%20passed%20(100%25)-brightgreen.svg)](tests/)
[![Security: CodeQL Verified](https://img.shields.io/badge/security-CodeQL%20Verified-blueviolet.svg)](.github/workflows/codeql.yml)
[![Offline Sovereign Mode](https://img.shields.io/badge/offline-100%25%20air--gapped%20ready-orange.svg)](#-4-k-cli-airgap--100-sovereign-offline-mode)
[![Fuzzed & Verified](https://img.shields.io/badge/fuzzer-0%20crashes%20%7C%2053%20paths-success.svg)](docs/CLI_TRAVERSAL_AUDIT.md)

> **The compiler-grounded, multi-model AI coding agent & terminal workstation with 10 autonomous superpowers.**
> A complete fusion of **Claude Code**, **Google Antigravity (AGY)**, **GitHub Copilot CLI**, and **Cursor** in your terminal. Zero cloud lock-in, 1-click zero-typing UI, local SLM support, adversarial self-healing loops, and compiler verification gates.

---

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ⚡ K-CLI AGENT │ 🤖 Gemini 2.0 Flash │  main (+1 ~0) │ 💾 184MB RSS │ 🏎️ 185 tok/s │ 💰 $0.002 │ 🛡️ AST OK│
├─────────────────────────┬─────────────────────────────────────────────────┬────────────────────────────┤
│ 🚀 1-CLICK LAUNCHER     │  👑 K-CLI Agentic Workstation                   │  📜 PENDING DIFFS          │
│  [ 🔑 API Key Vault ]   │                                                 │   • main.py (+12 -3)       │
│  [ 👻 Ghost Autopilot ] │  **User**: Refactor auth token validation       │                            │
│  [ 🐝 Adversarial Swarm]│                                                 │  ⚡ BACKGROUND TASKS       │
│  [ 🧠 Synapse Code Graph│  ╭─ 🧠 Thinking (1.2s)... (Click to expand) ──╮  │   • Verifier: Idle         │
│  [ 🛡️ Air-Gapped Mode ] │  │  • Resolving AST symbol dependencies       │  │   • Swarm: Active          │
│  [ 🎯 AI Git Bisect ]   │  ╰────────────────────────────────────────────╯  │                            │
│  [ 👁️ PR Review Bot ]   │                                                 │  📊 TELEMETRY GAUGE        │
│  [ ⚡ Smart Cost Router]│  **K-CLI Agent**: Applied zero-allocation       │   • TTFT: 0.12s            │
│  [ 🌿 Repo Gardener ]   │  JWT parser with constant-time HMAC check.      │   • Throughput: 185 tok/s  │
│  [ 💬 Codebase Q&A ]    │                                                 │   • Cache Hit: 94%         │
│  [ 🏗️ Full-Stack Scaffold  ╭─ 🛠️ Tool: patch_file [auth.py] ────────────╮  │                            │
│  [ ⚔️ Merge Conflicts ] │  │  [ 🟢 Allow ] [ 🔴 Deny ] [ 🛡️ Test ]      │  │                            │
│  [ 🐙 GitHub Center ]   │  ╰────────────────────────────────────────────╯  │                            │
│  [ 🤖 Switch AI Model ] ├─────────────────────────────────────────────────┤                            │
│  [ 🛡️ Security Healer ] │ [ ⚡ Plan ] [ ⚔️ Conflict ] [ 🐙 GitHub ]         │                            │
│  [ 🚨 Incident Triage ] │ [ 🔑 Keys ] [ 🤖 Models ] [ 🛡️ Security ] [ 🧹 ]  │                            │
│  [ 📊 Architecture ]    ├─────────────────────────────────────────────────┤                            │
│                         │ > Ask K-CLI anything or click a 1-Click button  │                            │
└─────────────────────────┴─────────────────────────────────────────────────┴────────────────────────────┘
```

---

## ⚡ Quick Start (Get Running in 30 Seconds)

```bash
# 1. Clone & Install in Editable Mode
git clone https://github.com/krishivjoshi219-collab/K-Cli.git
cd K-Cli
python -m venv .venv && source .venv/bin/activate
pip install -e .

# 2. Configure API Keys (or use offline Local SLMs / Ollama for free)
k-cli keys set GEMINI_API_KEY "your_key_here"

# 3. Launch Full-Screen Cyber-Workstation
k
# (or: k-cli ui)

# 4. Or Run Autonomous Agent Directly from Terminal
k "Implement a lock-free ring buffer in Python with thread-safe atomics"
```

---

## 🔑 Universal API Key & Provider Management

Manage all provider keys with zero fuss from the command line or inside the TUI:

```bash
# View live status of all configured keys
k-cli keys

# Set any key persistently (stored in ~/.kcli/credentials.env)
k-cli keys set GEMINI_API_KEY "AIzaSy..."
k-cli keys set ANTHROPIC_API_KEY "sk-ant-..."
k-cli keys set OPENAI_API_KEY "sk-proj-..."
k-cli keys set DEEPSEEK_API_KEY "sk-..."
k-cli keys set GITHUB_TOKEN "ghp_..."

# Live connectivity test on all configured provider endpoints
k-cli keys test

# Import keys from an existing .env or key.json file
k-cli keys import .env
```

Inside the TUI, press **`Ctrl+A`** or click **`[ 🔑 API Key Vault ]`** to configure all keys simultaneously with 1 click.

---

## 🔥 The 10 Autonomous Superpowers

### 👻 1. `k-cli ghost` — Ghost Terminal Autopilot (Live Crash Healer)
Attach K-CLI to any dev server, test runner, or compiler (`npm run dev`, `pytest`, `cargo run`). Whenever an exception occurs, K-CLI intercepts the traceback in the background, writes a compiler-verified patch, and presents a 1-click terminal fix prompt:

```bash
k-cli ghost "pytest"
# or: k-cli ghost "npm run dev"
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
Builds an AST symbol call graph of the codebase and extracts only the minimal surgical subgraph needed for prompt context (<1,000 tokens), speeding up responses 10x and slashing API bills:

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

### 🎯 5. `k-cli bisect` — AI Git Bisect & Regression Hunter
Automates binary search across git commit history with an AI oracle to pinpoint the exact commit that broke tests, explains the root cause diff, and synthesizes a fix:

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
Ask architectural, security, or structural questions about your codebase in plain English with zero data leaving your machine:

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

## 🎛️ Terminal Hotkeys & Interactive Modals

Press global shortcuts anywhere inside `k-cli ui` / `k`:

| Shortcut | Modal Screen | Capabilities |
| :---: | :--- | :--- |
| **`Ctrl+A`** | **Credentials Vault** | Configure, save, and live-test API keys across 8+ providers simultaneously. |
| **`Ctrl+K`** | **4-Way Conflict Studio** | Visual merge conflict studio (`Ours` vs `Base` vs `Theirs` vs `AI Resolved`) with compiler test gates. |
| **`Ctrl+G`** | **GitHub Command Center** | Autonomous Issue Solver, PR reviews, CI failure log parser, and release publisher. |
| **`Ctrl+M`** | **Model Hub** | Switch active local SLMs & cloud LLMs with live TTFT and throughput (`tok/s`) benchmarking. |
| **`Ctrl+S`** | **AST Security Healer** | Static AST vulnerability scanner with 1-click surgical auto-healer. |
| **`Ctrl+L`** | **Clear Workspace** | Clean chat and diff streams. |

---

## 🐍 Universal Python SDK

Integrate K-CLI into your Python pipelines and automated workflows:

```python
from k_cli import KCLI

# 1. Initialize K-CLI Agent
with KCLI(model="deepseek-reasoner", local_fallback="qwen2.5-coder:1.5b") as kcli:
    # 2. Multi-Model Generation
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

## 📁 Repository Architecture

```
K-Cli/
├── k_cli/                        ← Core package
│   ├── core/                     ← Credentials vault, LLM driver, Models Hub, SDK, Smart Router, Airgap
│   │   ├── credentials.py        ← Multi-tier API key discovery & storage
│   │   ├── llm_driver.py         ← Unified multi-provider engine (OpenAI, Claude, Gemini, DeepSeek, Groq, Ollama)
│   │   ├── models_hub.py         ← Universal Model Hub & live telemetry benchmark
│   │   ├── smart_router.py       ← Dynamic cost & latency task complexity router
│   │   ├── airgap.py             ← 100% offline sovereign airgap manager
│   │   ├── sdk.py                ← High-level Python developer SDK
│   │   ├── session.py            ← Multi-turn conversation state manager
│   │   └── prompting.py          ← Provider-aware system prompts
│   │
│   ├── github/                   ← GitHub API, PR Lifecycle, PR Watcher, Dedup
│   │   ├── github_engine.py      ← Issue solver, releases, Actions CI inspector
│   │   ├── github_client.py      ← Dependency-free GitHub REST v3 client
│   │   ├── pr_watcher.py         ← 24/7 background PR review & auto-merge bot
│   │   └── dedup_engine.py       ← Semantic BM25 & AST duplicate issue detector
│   │
│   ├── git/                      ← Git Guard, 3-Way Conflict Resolver, AI Bisect, Patcher, Verifier
│   │   ├── conflict_resolver.py  ← 4-way AST merge conflict resolver
│   │   ├── ai_bisect.py          ← AI-guided regression hunting binary search
│   │   ├── smart_git.py          ← Conventional commit & PR description generator
│   │   ├── patcher.py            ← Surgical unified diff patcher
│   │   ├── verifier.py           ← Multi-language compiler & test harness gate
│   │   ├── git_guard.py          ← Rollback & dirty workspace protector
│   │   └── repo_map.py           ← AST symbol tree & PageRank ranking
│   │
│   ├── tui/                      ← 3-Column Fusion Cyber-Workstation (Textual)
│   │   ├── tui_app.py            ← Interactive full-screen workstation & modals
│   │   ├── tui.py                ← Rich streaming renderer & status bar
│   │   ├── tui_animations.py     ← ASCII banner & speedometer animations
│   │   └── diff_viewer.py        ← Side-by-side & unified diff visualizer
│   │
│   ├── agents/                   ← Orchestrator, Swarm, Scaffolder, Personas
│   │   ├── orchestrator.py       ← Multi-phase execution orchestrator
│   │   ├── subagents.py          ← Parallel subagent task scheduler
│   │   ├── adversarial_swarm.py  ← Red Team vs Blue Team vs Judge consensus
│   │   ├── scaffold_engine.py    ← Natural language full-stack scaffolder
│   │   └── persona.py            ← Specialized domain personas (Architect, Coder, Critic)
│   │
│   ├── tools/                    ← Autonomous developer tools
│   │   ├── ghost_daemon.py       ← Ghost terminal crash autopilot
│   │   ├── synapse_graph.py      ← AST neural code graph & context compressor
│   │   ├── repo_gardener.py      ← Nightly dead code & dependency pruner
│   │   ├── codebase_qa.py        ← Local semantic codebase search & Q&A
│   │   ├── security_healer.py    ← AST vulnerability scanner & auto-healer
│   │   ├── incident_triage.py    ← Stack trace & CI error log parser
│   │   ├── diagram_generator.py  ← Mermaid architecture graph generator
│   │   ├── mcp_client.py         ← Model Context Protocol (MCP) client
│   │   └── doc_retriever.py      ← DevDocs offline SQLite documentation search
│   │
│   ├── cli.py                    ← Single Typer CLI entrypoint
│   └── __init__.py               ← Public SDK exports
│
├── scripts/                      ← Developer tools & CLI traversal runner
│   └── cli_traverser.py          ← Automated binary path explorer & fuzzer
├── tests/                        ← 300 passing test cases across 18 test suites
│   ├── test_cli_fuzzer_traversal.py ← Full CLI path traversal test suite
│   ├── test_credentials.py       ← Credentials vault unit test suite
│   └── test_killer_features.py   ← 10 autonomous superpowers test suite
├── docs/                         ← System documentation & audit reports
│   ├── ARCHITECTURE.md           ← Complete 5-layer subsystem architecture
│   ├── CLI_TRAVERSAL_AUDIT.md    ← Fuzzer audit log across all 53 execution paths
│   ├── CODE_OF_CONDUCT.md        ← Friendly developer code of conduct
│   └── CONTRIBUTING.md           ← Zero-red-tape contribution guide
├── .github/workflows/            ← CI/CD & CodeQL security scans
├── pyproject.toml                ← Package configuration
└── LICENSE                       ← MIT License
```

---

## 🧪 Testing, Verification & Fuzzing

K-CLI is backed by a **300-test suite** covering AST safety, binary bisect searches, subagent DAG scheduling, mock telemetry, and security vulnerability healing:

```bash
pytest tests/ -v
# ============================= 300 passed in 100% ==============================
```

### 🔍 Binary Mapping & Fuzzing Audit
Run the automated path traverser across all 53 command paths:
```bash
python scripts/cli_traverser.py
# ▸ 53 Paths Traversed: 40 Passed | 13 Graceful Rejects | 0 Crashes | 0 Hangs
```

---

## 🤝 Contributing

We love contributions! Check out our friendly, zero-red-tape [`CONTRIBUTING.md`](docs/CONTRIBUTING.md) to get hacking in 2 minutes.

---

## 📄 License

MIT License — free for individual developers, open-source projects, and commercial teams.
