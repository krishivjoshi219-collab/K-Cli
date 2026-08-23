<div align="center">

```
██╗  ██╗      ██████╗██╗     ██╗
██║ ██╔╝     ██╔════╝██║     ██║
█████╔╝      ██║     ██║     ██║
██╔═██╗      ██║     ██║     ██║
██║  ██╗     ╚██████╗███████╗██║
╚═╝  ╚═╝      ╚═════╝╚══════╝╚═╝
```

**The AI coding agent that lives in your terminal.**  
**It watches your crashes. It fixes your PRs. It argues with itself until the code is perfect.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-300%20passing-brightgreen?style=flat-square&logo=pytest)](tests/)
[![CodeQL](https://img.shields.io/badge/CodeQL-verified-blueviolet?style=flat-square&logo=github)](/.github/workflows/codeql.yml)
[![Providers](https://img.shields.io/badge/providers-Gemini%20%7C%20Claude%20%7C%20GPT--4%20%7C%20Ollama-orange?style=flat-square)](#-supported-models)
[![Offline](https://img.shields.io/badge/offline-100%25%20air--gapped-red?style=flat-square)](#-4-k-cli-airgap----sovereign-offline-mode)

</div>

---

## What is this?

You're building something. Your test runner crashes. Your PR sits un-reviewed for 3 days. Your junior dev just merge-conflicted main. You spend 40 minutes asking ChatGPT the same thing in 4 different tabs.

**K-CLI fixes all of that.**

It's an agentic AI workstation that plugs into your terminal, your git repo, and your GitHub. It doesn't just answer questions — it runs a **3-agent adversarial Red Team vs Blue Team vs Judge** loop to verify its own code before touching a single file. It watches your dev server in the background and **self-heals crashes while you sleep**. It routes tasks to cheap local models (free) or frontier models ($0.003) based on complexity — automatically.

```bash
pip install -e .
k "build me a FastAPI auth system with JWT and refresh tokens"
```

That's it. Watch it go.

---

## In 30 seconds

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ ⚡ K-CLI  │ gemini-2.0-flash  │  main (+3 ~0)  │ 🏎️ 185 tok/s  │ 💰 $0.027 saved  │
├──────────────────┬──────────────────────────────────────┬──────────────────────────┤
│ 🚀 1-CLICK       │ 👑 K-CLI Agentic Workstation          │ 📜 LIVE DIFFS            │
│                  │                                      │   • auth.py  (+42 -7)    │
│ [ 👻 Ghost ]     │ > build me a FastAPI auth system      │   • models.py (+18 -0)   │
│ [ 🐝 Swarm ]     │                                      │   • tests/   (+53 -0)    │
│ [ 🧠 Synapse ]   │ 🔵 Blue Agent → Writing code...      │                          │
│ [ 🛡️ Airgap ]   │ 🔴 Red Agent  → 14 attack tests      │ ⚡ BACKGROUND             │
│ [ 🎯 Bisect ]    │ ⚖️ Judge      → 14/14 passed ✔       │   Swarm: Active          │
│ [ 👁️ PR Watch ]  │                                      │   Ghost: Monitoring      │
│ [ ⚡ Router ]    │ ✔ auth.py verified (AST + pytest)    │   Verifier: Idle         │
│ [ 🌿 Garden ]    │ ✔ 53 lines written, 0 hallucinations │                          │
│ [ 💬 Explain ]   ├──────────────────────────────────────┤ 📊 METRICS               │
│ [ 🏗️ Scaffold ]  │ ⚡ Plan  ⚔️ Conflict  🐙 GitHub       │   TTFT:  0.12s           │
│ [ 🔑 API Keys ]  │ 🔑 Keys  🤖 Models   🛡️ Security      │   Saved: $0.027 today    │
└──────────────────┴──────────────────────────────────────┴──────────────────────────┘
```

Full-screen TUI (`k` or `k-cli ui`), or bare terminal (`k "your task"`). Your choice.

---

## The 10 things that make devs go "wait, that's real?"

### 👻 1. Ghost Terminal — It watches your crashes and heals them silently

Run your dev server, compiler, or test suite through K-CLI Ghost. The moment it sees a traceback, it extracts AST context, writes a surgical patch, verifies it compiles and tests pass, and pings you with a single keypress diff.

```bash
k-cli ghost "pytest"
```

```
👻  GHOST AUTOPILOT TRIGGERED
────────────────────────────────────────────────────────────────
  Intercepted: TypeError at src/auth/middleware.py:42
  Root cause:  jwt.decode() called without algorithms kwarg
  Confidence:  97.3%
  Patch ready: [ Y  Apply (1 line change) ]  [ D  View Diff ]  [ N  Dismiss ]
```

Works with `pytest`, `npm run dev`, `cargo run`, `go build`, `make` — anything that writes to stdout.

---

### 🐝 2. Adversarial Swarm — 3 agents argue until the code is bulletproof

Not "write me code and hope for the best." **Blue Agent** writes the implementation. **Red Agent** immediately generates 14 adversarial tests: null inputs, race conditions, boundary overflows, injection attacks. **Judge** runs everything through AST verification + compiler + pytest. Loop repeats until consensus.

```bash
k-cli swarm "implement a thread-safe rate limiter" --rounds 3
```

```
Round 1/3
  🔵 Blue  → Implemented TokenBucketRateLimiter with threading.Lock
  🔴 Red   → Race condition test: 500 threads hammering acquire()
  ⚖️ Judge → 1 ThreadSanitizer violation detected. Retrying...

Round 2/3
  🔵 Blue  → Switched to atomics via threading.Semaphore + double-checked lock
  🔴 Red   → 500-thread storm + negative limit edge case
  ⚖️ Judge → All 14 attacks neutralized. AST clean. ✔ CONSENSUS REACHED
```

Zero hallucinations. The code doesn't ship until it survives the red team.

---

### 🧠 3. Synapse Graph — 99.7% token compression via AST code graph

Indexing a whole repo into a prompt is expensive and slow. Synapse builds an in-memory SQLite AST dependency graph across every function, class, and module, then extracts *only the minimal subgraph* relevant to your task.

```bash
k-cli synapse "refactor the payment transaction rollback logic"
```

```
  Full repo context  →  1,200,000 tokens  ($3.60 per Claude 3.5 Sonnet call)
  Synapse subgraph   →      1,240 tokens  ($0.004)
  Compression ratio  →       99.7%
  Matched symbols    →  PaymentProcessor::rollback, Transaction::revert, db_session
  Latency            →       0.4s
```

Context goes in surgical. Answers come back precise.

---

### 🛡️ 4. `k-cli airgap` — Sovereign Offline Mode (zero bytes leave your machine)

Enterprises, defense contractors, and healthcare teams can run K-CLI completely offline. Airgap mode restricts all egress to `localhost`, detects your local toolchains (gcc, rustc, git, python), and routes all inference to Ollama/llama.cpp/GGUF local SLMs.

```bash
k-cli airgap
```

```
  🛡️  SOVEREIGN AIR-GAP ACTIVE
  ─────────────────────────────────────────
  Network egress    →  🚫 BLOCKED (0 bytes out)
  Local toolchains  →  Python AST, GCC/Clang, rustc, Git
  Local models      →  qwen2.5-coder:1.5b, deepseek-coder:6.7b
  Violations        →  0
```

---

### 🎯 5. `k-cli bisect` — AI-powered git blame on steroids

That bug that appeared 3 weeks ago and nobody noticed? Bisect runs binary search across your entire commit history with an AI oracle, isolates the exact commit that broke the test, explains the diff in plain English, and synthesizes a fix.

```bash
k-cli bisect "pytest tests/payment/ -q" --good HEAD~20 --bad HEAD
```

```
  Searching 20 commits...  [██████████] done
  ─────────────────────────────────────────────────────
  Culprit commit:  a3f921b  "chore: upgrade decimal lib"
  Root cause:      Decimal.quantize() default rounding changed in v2.1
                   Affects: order_total > $1,000 edge case
  Fix synthesized: 1 line change in utils/currency.py ✔
```

---

### 👁️ 6. `k-cli watch` — 24/7 autonomous PR reviewer

Point it at your GitHub repo. Every new PR gets a full compiler-grade review (security vulnerabilities, race conditions, null deref, performance regressions), a structured comment posted back to GitHub, and auto-merge if CI passes.

```bash
k-cli watch --interval 60 --auto-merge
```

```
  👁️  Watching krishivjoshi219-collab/K-Cli  (polling every 60s)
  ──────────────────────────────────────────────────────────────────
  PR #47 → "feat: add redis session store"
    Security   ✔  No injection vectors found
    Race cond. ✔  Session writes are atomic
    Tests      ✔  Coverage increased by 6%
    Verdict    →  ✔ Approved + posted review comment
    CI status  →  passed → auto-merged (squash)
```

---

### ⚡ 7. Smart Model Router — stops you burning money on GPT-4 for typos

Every task gets a complexity score (0–100). Trivial tasks (docstrings, formatting, comments) route to your local Ollama for **$0.00**. Medium tasks go to DeepSeek. Complex architecture work goes to Claude/GPT-4. Savings logged per session.

```bash
k-cli route "fix typo in README"
# Tier: TRIVIAL (score: 5/100)  →  Local Ollama    FREE    Saved: $0.030 vs GPT-4

k-cli route "architect a distributed event sourcing system with CQRS"
# Tier: COMPLEX (score: 95/100) →  Claude 3.5 Sonnet  $0.003  Saved: $0.027 vs GPT-4
```

Real routing logic. Not a gimmick.

---

### 🌿 8. `k-cli garden` — your repo has a health score now

Scans for dead unreferenced functions, unpinned `requirements.txt` deps, missing docstrings, stale TODO comments, and orphaned test files. Reports a health score. Optionally opens a clean maintenance PR.

```bash
k-cli garden
```

```
  🌿 Repo Health Report
  ────────────────────────────────────────────────────
  Score             →  91.5 / 100
  Dead functions    →  3  (utils/legacy.py:42, :88, old_api.py:15)
  Unpinned deps     →  2  (requests, boto3 — no version pin)
  Stale TODOs       →  7  (oldest: 14 months)
  Recommendation    →  Open maintenance PR? [Y/N]
```

---

### 💬 9. `k-cli explain` — ask your codebase anything in plain English

Semantic search over your entire codebase using AST symbol indexing. Ask architectural questions, trace data flows, find where a bug could live — without leaving the terminal.

```bash
k-cli explain "where does JWT token validation actually happen?"
```

```
  ▸ Flow traced across 3 files:
    1. core/session.py:88   → authenticate_request() → extracts Bearer token
    2. core/session.py:140  → verify_jwt_claims()    → exp, iat, nbf, aud checked
    3. agents/persona.py:22 → DomainPersona.bind()   → role injection post-verify
  ▸ No data leaves your machine.
```

---

### 🏗️ 10. `k-cli scaffold` — turn one sentence into a production codebase

Not a template. A full multi-file, tested, AST-valid, Docker-ready application generated from a single natural language prompt.

```bash
k-cli scaffold "FastAPI + SQLAlchemy 2.0 async + Redis cache + Alembic + pytest + Docker" --write
```

```
  🏗️  Scaffolded 7 production files  (0 AST errors, 92% test coverage)
  ──────────────────────────────────────────────────────────────────────
  ✔  main.py          (FastAPI app factory + lifespan events)
  ✔  models.py        (SQLAlchemy 2.0 async ORM models)
  ✔  schemas.py       (Pydantic v2 validators)
  ✔  config.py        (Pydantic Settings + env management)
  ✔  alembic/         (Migration environment pre-configured)
  ✔  Dockerfile       (Multi-stage, non-root user, slim final image)
  ✔  tests/test_api.py (Pytest async integration suite)
```

---

## Supported Models

K-CLI speaks to everything. Local, cloud, or hybrid.

| Provider | Models |
| :--- | :--- |
| **Ollama (local, free)** | `qwen2.5-coder`, `deepseek-r1`, `llama3.3`, `starcoder2`, `phi-4`, `mistral`, `codellama` |
| **llama.cpp / GGUF** | Any `.gguf` model via HTTP server or native in-process inference |
| **Google Gemini** | `gemini-2.0-flash`, `gemini-2.0-pro`, `gemini-1.5-pro` |
| **Anthropic** | `claude-3-7-sonnet`, `claude-3-5-sonnet`, `claude-3-5-haiku` |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini`, `o1`, `o3-mini` |
| **DeepSeek** | `deepseek-v3`, `deepseek-r1` |
| **Groq** | `llama-3.3-70b`, `qwen-2.5-coder-32b` @ 300+ tok/s |
| **Mistral** | `codestral`, `mistral-large` |
| **OpenRouter** | 100+ models via unified API |
| **vLLM / LM Studio / LocalAI / Jan** | Any OpenAI-compatible local endpoint |

Switch at runtime: `k-cli model set deepseek-r1`

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/krishivjoshi219-collab/K-Cli.git
cd K-Cli
python -m venv .venv && source .venv/bin/activate
pip install -e .

# 2. Set an API key — or skip and use Ollama locally for free
k-cli keys set GEMINI_API_KEY "your_key_here"

# 3. Open the full-screen workstation
k

# 4. Or run a task directly from the terminal
k "refactor my auth module to use async/await throughout"
```

---

## API Keys

```bash
k-cli keys                          # Check what's configured
k-cli keys set ANTHROPIC_API_KEY "sk-ant-..."
k-cli keys set OPENAI_API_KEY "sk-proj-..."
k-cli keys set DEEPSEEK_API_KEY "sk-..."
k-cli keys set GITHUB_TOKEN "ghp_..."
k-cli keys test                     # Live test all provider endpoints
k-cli keys import .env              # Import from existing .env file
```

All keys stored in `~/.kcli/credentials.env`. Nothing phoned home.

---

## All CLI Commands

```
k-cli run      "prompt"           →  Single-shot agentic task
k-cli ui                          →  Launch full-screen TUI workstation
k-cli ghost    "command"          →  Attach crash healer to any process
k-cli swarm    "task"             →  Adversarial 3-agent consensus loop
k-cli synapse  "query"            →  AST code graph context extraction
k-cli airgap                      →  Enable sovereign offline mode
k-cli bisect   "test cmd"         →  AI git bisect regression hunter
k-cli watch                       →  24/7 autonomous PR review bot
k-cli route    "task"             →  Smart cost/latency model router
k-cli garden                      →  Repo health audit & dead code sweep
k-cli explain  "question"         →  Natural language codebase Q&A
k-cli scaffold "description"      →  Full-stack project generator

k-cli pr list                     →  List open pull requests
k-cli pr review <num>             →  AI code review on a PR
k-cli pr fix    <num>             →  Auto-fix failing PR
k-cli pr merge  <num>             →  CI-gated auto-merge

k-cli conflict list               →  Find all merge conflicts in repo
k-cli conflict resolve            →  AI 4-way AST conflict resolution

k-cli mcp list                    →  List connected MCP servers
k-cli mcp add  <name> <cmd>       →  Connect a new MCP server
k-cli mcp call <tool> <args>      →  Call any MCP tool directly

k-cli keys                        →  Show API key status table
k-cli keys set <KEY> <value>      →  Persist a provider key
k-cli keys test                   →  Live test all provider endpoints

k-cli model list                  →  Show all available models
k-cli model set <model>           →  Switch active model
k-cli model pull <model>          →  Pull a local Ollama model
```

---

## Python SDK

```python
from k_cli import KCLI

with KCLI(model="deepseek-reasoner", local_fallback="qwen2.5-coder:1.5b") as agent:
    # Generate code with compiler verification gate
    result = agent.generate("write a lock-free queue in C++23")

    # Autonomous GitHub workflows
    agent.github.solve_issue(issue_number=42, auto_pr=True)
    agent.github.create_release(tag_name="v2.0.0")

    # 4-way AST merge conflict studio
    agent.conflicts.resolve_all()

    # Security vulnerability scan + auto-heal
    agent.security.heal_all()

    # Smart model routing with cost tracking
    decision = agent.route("architect a CQRS event sourcing system")
    print(f"→ {decision.selected_model} saves ${decision.savings_usd:.3f} vs GPT-4")

    # Synapse AST code graph context extraction
    ctx = agent.synapse("payment processing flow")
    print(f"→ {ctx.compression_ratio:.0%} token reduction")
```

---

## Architecture

```
k_cli/
├── core/
│   ├── llm_driver.py        ← Unified inference across 10+ providers with streaming
│   ├── credentials.py       ← Multi-tier key discovery: ~/.kcli → .env → key.json
│   ├── smart_router.py      ← Task complexity scorer + cost-optimal model selector
│   ├── models_hub.py        ← Dynamic model registry, benchmark, and switcher
│   ├── airgap.py            ← Sovereign offline mode with network egress restriction
│   └── session.py           ← Multi-turn conversation state + context manager
│
├── agents/
│   ├── adversarial_swarm.py ← Red Team vs Blue Team vs Judge consensus engine
│   ├── orchestrator.py      ← Multi-phase task planning and execution orchestrator
│   ├── subagents.py         ← Parallel subagent DAG scheduler
│   ├── scaffold_engine.py   ← Natural language → full-stack project generator
│   └── persona.py           ← Specialized domain personas (Architect, Security, DevOps)
│
├── git/
│   ├── conflict_resolver.py ← AST-aware 4-way merge conflict studio + LLM resolution
│   ├── ai_bisect.py         ← AI-guided binary regression hunter
│   ├── verifier.py          ← Multi-language AST + compiler + test verification gate
│   ├── patcher.py           ← Surgical unified diff patcher with rollback
│   ├── smart_git.py         ← Conventional commit + PR description generator
│   └── repo_map.py          ← Full AST symbol tree with PageRank ranking
│
├── github/
│   ├── github_client.py     ← Zero-dependency GitHub REST v3 client
│   ├── github_engine.py     ← Issue solver, release publisher, CI inspector
│   ├── pr_watcher.py        ← 24/7 background PR review and auto-merge bot
│   └── dedup_engine.py      ← BM25 + AST semantic duplicate issue detector
│
├── tools/
│   ├── ghost_daemon.py      ← PTY-attached crash interceptor and auto-healer
│   ├── synapse_graph.py     ← SQLite AST code graph + 99%+ context compressor
│   ├── security_healer.py   ← Static AST vulnerability scanner with auto-healer
│   ├── repo_gardener.py     ← Dead code + dependency + TODO health auditor
│   ├── codebase_qa.py       ← Local semantic codebase search engine
│   ├── incident_triage.py   ← Stack trace + CI log parser and root cause analyzer
│   ├── mcp_client.py        ← Full Model Context Protocol (MCP) JSON-RPC client
│   └── doc_retriever.py     ← Offline DevDocs SQLite documentation search
│
└── tui/
    ├── tui_app.py           ← 3-column Textual workstation with 1-click modals
    ├── tui.py               ← Rich streaming renderer + live status bar
    ├── tui_animations.py    ← ASCII banner + token throughput speedometer
    └── diff_viewer.py       ← Side-by-side and inline diff visualizer
```

---

## Testing

300 test cases. 18 test suites. Adversarial fuzzer traversed every CLI path (53 paths, 0 crashes, 0 hangs):

```bash
pytest tests/ -v
# 300 passed ✔

python scripts/cli_traverser.py
# 53 paths → 40 passed | 13 graceful rejects | 0 crashes | 0 hangs
```

Full audit at [`docs/CLI_TRAVERSAL_AUDIT.md`](docs/CLI_TRAVERSAL_AUDIT.md).

---

## Contributing

Read [`CONTRIBUTING.md`](docs/CONTRIBUTING.md). It's short, casual, and has zero red tape. PRs welcome — even drafts.

---

## License

MIT. Use it in anything.
