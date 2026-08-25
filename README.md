<div align="center">

```
██╗  ██╗      ██████╗██╗     ██╗
██║ ██╔╝     ██╔════╝██║     ██║
█████╔╝      ██║     ██║     ██║
██╔═██╗      ██║     ██║     ██║
██║  ██╗     ╚██████╗███████╗██║
╚═╝  ╚═╝      ╚═════╝╚══════╝╚═╝
```

### The AI coding agent that fixes bugs **while you sleep**, reviews PRs **before you wake up**, and runs 5 models simultaneously to argue over your code until it's perfect.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square&logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![CI](https://github.com/krishivjoshi219-collab/K-Cli/actions/workflows/ci.yml/badge.svg)](https://github.com/krishivjoshi219-collab/K-Cli/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-114%20passing-brightgreen?style=flat-square&logo=pytest)](tests/)
[![Models](https://img.shields.io/badge/models-ANY%20model%2C%20no%20lock--in-orange?style=flat-square)](#-supported-models)
[![Ollama](https://img.shields.io/badge/local-Ollama%20supported%20(free)-blueviolet?style=flat-square)](#-local-models-free-no-api-key)
[![Offline](https://img.shields.io/badge/offline-100%25%20air--gapped%20mode-red?style=flat-square)](#-air-gapped-sovereign-mode)
[![GitHub Stars](https://img.shields.io/github/stars/krishivjoshi219-collab/K-Cli?style=flat-square&color=gold)](https://github.com/krishivjoshi219-collab/K-Cli/stargazers)

</div>

---

## ⚡ Install in one line

```bash
curl -sSL https://raw.githubusercontent.com/krishivjoshi219-collab/K-Cli/main/install.sh | bash
```

Or with pip (if you already have Python 3.11+):

```bash
pip install -e . && k-cli codex
```

**No API key required to start** — works 100% locally with [Ollama](https://ollama.com).

---

## What is K-CLI?

You know that feeling when your CI fails at 2am, your PR has 47 unread comments, and you're context-switching between 4 AI tabs to fix a 3-line bug?

**K-CLI is the fix.**

It's a full **agentic AI workstation** that lives in your terminal. It doesn't just answer questions — it:

- 🔥 **Runs 5 AI models simultaneously** and picks the best code via consensus
- 👻 **Watches your crashes** in the background and heals them without you asking
- 🐙 **Reviews, fixes, and merges PRs** autonomously  
- ⚔️ **Resolves git merge conflicts** with 3-way AI semantic understanding
- 🛡️ **Scans for security vulnerabilities** and surgically patches them
- 🎯 **Bisects regressions** through git history to find the exact bad commit
- 🤖 **Uses ANY model** — your local Ollama, GPT-4o, Claude, Gemini, Groq — no lock-in

---

## The 30-second demo

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ ⚡ K-CLI  │ 🤖 gemini-2.0-flash  │  main (+3 ~0)  │ 🏎️ 192 tok/s  │ 💰 $0.031  │
├──────────────────┬──────────────────────────────────────┬──────────────────────────┤
│ 🚀 LAUNCHER      │ 💬 K-CLI Agentic Workstation          │ 📜 LIVE DIFFS            │
│                  │                                      │   auth.py   (+42 −7)     │
│ [ ⚡ 5-Swarm ]   │ > audit my auth module               │   models.py (+18 −0)     │
│ [ 🤖 Models ]    │                                      │   tests/    (+53 −0)     │
│ [ 📖 Codex ]     │ ╔══ 🧠 Thinking (1.2s)... ▼         │                          │
│ [ 🔑 API Keys ]  │ ║  · Scanning AST context            │ ⚡ BACKGROUND             │
│ [ 👻 Ghost ]     │ ║  · 5 models generating in parallel │   Swarm: 5/5 active      │
│ [ 🐝 Swarm ]     │ ║  · Cross-model peer review running │   Ghost: monitoring      │
│ [ ⚔️ Conflicts ] │ ╚═════════════════════════════════  │   Verifier: AST ✓        │
│ [ 🐙 GitHub ]    │                                      │                          │
│ [ 🛡️ Security ]  │ 🔴 CRITICAL: SQL injection line 47   │ 📊 TELEMETRY             │
│ [ 🎯 Bisect ]    │ 🟡 WARNING:  Weak JWT salt line 83   │   Tokens:  2,847         │
│ [ 👁️ PR Watch ]  │ 🟡 WARNING:  No rate limiting         │   Saved:   $0.031        │
│ [ 🌿 Garden ]    │                                      │   TTFT:    0.12s         │
│ [ 💬 Explain ]   │ ✅ Auto-healer patched 3 issues      │                          │
│ [ 🏗️ Scaffold ]  │ ✅ AST verified · 53 tests pass      │                          │
└──────────────────┴──────────────────────────────────────┴──────────────────────────┘
  Ctrl+O Codex · Ctrl+U 5-Swarm · Ctrl+M Models · Ctrl+A Keys · Ctrl+K Conflicts
```

Launch it:

```bash
k          # → full TUI workstation
k-cli ui   # → same thing
k-cli codex  # → interactive setup wizard
```

---

## The features that make devs go "wait, that's real?"

### 🤖 1. Use ANY model — no lock-in, ever

K-CLI dynamically discovers every model on your system by **asking Ollama directly** (`/api/tags`) and querying live Cloud APIs. No hardcoded model lists. No "we only support these 5 models." 

Type literally anything:

```bash
k-cli audit "build a rate limiter" --models "gemini-2.0-flash,claude-3-7-sonnet,deepseek-reasoner,gpt-4o,qwen2.5-coder:7b"
```

```
✔  gemini-2.0-flash        → candidate generated (0.84s, 847 tokens, AST: pass)
✔  claude-3-7-sonnet       → candidate generated (1.24s, 1203 tokens, AST: pass)
✔  deepseek-reasoner       → candidate generated (2.10s, 2847 tokens, AST: pass)
✔  gpt-4o                  → candidate generated (0.97s, 934 tokens, AST: pass)
✔  qwen2.5-coder:7b        → candidate generated (3.41s, 1102 tokens, AST: pass)

Cross-model peer review complete. Consensus: deepseek-reasoner (score: 9.2/10)
```

Supports **any model string** — `ollama/llama3.2`, `openai/o3-mini`, `anthropic/claude-3-7-sonnet`, `groq/llama-3.3-70b-versatile`, `krishivjoshi/bankai-7b`, custom fine-tunes. If your inference backend serves it, K-CLI runs it.

---

### ⚡ 2. 5-Model Parallel Audit & Consensus Swarm

Not "one model writes code and you hope for the best." **Five models generate simultaneously.** Then they peer-review each other's code. Then an AST verifier runs ground-truth tests. The winner is selected (or synthesized) from the consensus.

```bash
k-cli audit "implement thread-safe connection pool" --models "gemini-2.0-flash,gpt-4o,claude-3-7-sonnet,deepseek-reasoner,qwen2.5-coder:7b"
```

Or press **`Ctrl+U`** in the TUI. Or type `/audit <task>` in the chat stream.

```
⚡ 5-Model Consensus Audit
─────────────────────────────────────────────────────────────────────────
  Model                  Latency    Tokens    AST   Peer Score
  ─────────────────────────────────────────────────────────────────────
  deepseek-reasoner      2.1s       2847      ✓      9.2/10  ← WINNER
  claude-3-7-sonnet      1.2s       1203      ✓      8.8/10
  gemini-2.0-flash       0.8s        847      ✓      8.4/10
  gpt-4o                 1.0s        934      ✓      8.1/10
  qwen2.5-coder:7b       3.4s       1102      ✓      7.9/10
─────────────────────────────────────────────────────────────────────────
  Consensus achieved · 100% AST pass · Applying winner
```

---

### 👻 3. Ghost Terminal — watches and heals crashes while you work

Run your dev server, test suite, or build through K-CLI Ghost. The moment it sees a stack trace, it extracts AST context, generates a surgical patch, verifies it passes tests, and shows you a 1-keypress diff.

```bash
k-cli ghost "pytest"
k-cli ghost "npm run dev"
k-cli ghost "cargo run"
```

```
👻  GHOST AUTOPILOT
────────────────────────────────────────────────────────────
  Intercepted: TypeError at src/auth/middleware.py:42
  Root cause:  jwt.decode() missing algorithms= kwarg
  Confidence:  97.3%  ·  Patch ready (1 line change)

  [ Y  Apply ]  [ D  View Diff ]  [ N  Skip ]  [ S  Open in TUI ]
```

Set it up once and it monitors forever. Works with anything that writes to stdout.

---

### ⚔️ 4. AI Merge Conflict Studio — 3-way semantic resolution

Not just "pick ours or theirs." K-CLI does **3-way semantic AST analysis** — understands _why_ the conflict happened and generates a resolution that preserves the intent of both sides.

```bash
k-cli conflict list      # find all conflicts in repo
k-cli conflict resolve   # AI resolves all of them
k-cli conflict resolve --file src/auth.py --auto-accept  # non-interactive
```

```
⚔️  Conflict Studio — src/auth.py
────────────────────────────────────────────────────────────
  Base intent:     rate limiting per IP (class method)
  HEAD adds:       Redis-based distributed rate limit
  Incoming adds:   in-memory LRU fallback
  AI resolution:   Redis-primary + LRU fallback (both preserved)
  AST verified:    ✓  Tests pass: ✓
```

---

### 🐙 5. Full GitHub PR Lifecycle — review, fix, merge autonomously

```bash
k-cli pr list                    # list open PRs
k-cli pr review 42               # AI reviews PR #42 (bugs, security, perf)
k-cli pr review 42 --post-comment  # posts review as GitHub comment
k-cli pr fix 42                  # fetches, fixes, verifies, pushes
k-cli pr merge 42 --method squash  # merges after CI passes
```

---

### 🛡️ 6. Security Auto-Healer — AST scanner + surgical patcher

```bash
k-cli security scan .            # scan entire codebase
k-cli security heal src/auth.py  # fix all vulns in one file
```

```
🛡️  Security Scan · src/auth.py
────────────────────────────────────────────────────────────
  🔴 CRITICAL  SQL injection via f-string interpolation (line 47)
  🟡 WARNING   No rate limiting on /login endpoint (line 83)
  🟡 WARNING   JWT secret hardcoded in source (line 12)
  🟢 INFO      HTTPS enforced

  Healing...  [████████████████████] 3/3 patches applied · All tests pass
```

---

### 🎯 7. AI Git Bisect — finds the exact commit that broke your tests

```bash
k-cli bisect "pytest tests/ -q"
```

```
🎯  AI Git Bisect
────────────────────────────────────────────────────────────
  Running binary search over 847 commits...
  Bad commit found: a3f9c2d (2 days ago)
  Author: @you
  Message: "refactor: extract auth middleware"
  Culprit: removed token refresh handler (line 127 deleted)
  Fix suggestion: restore refresh_token() in middleware.py
```

---

### 🌿 8. Repo Gardener — sweeps dead code, stale branches, and TODOs

```bash
k-cli garden --sweep
```

Finds dead code, stale branches (no activity in 90d), TODO/FIXME comments with suggested fixes, duplicate functions, and missing docstrings. All with 1-click apply.

---

### 📦 9. Local Models — completely free, no API key needed

K-CLI discovers every model installed in Ollama with full metadata:

```bash
k-cli models list
```

```
🤖  Discovered Models (Ollama · live scan)
──────────────────────────────────────────────────────────────────────
  MODEL                    SIZE    QUANT     SPEED     BEST FOR
  ──────────────────────────────────────────────────────────────────
  qwen2.5-coder:7b         4.7GB   Q4_K_M    fast      Code generation
  llama3.2:3b              2.0GB   Q4_K_M    fastest   Quick edits
  deepseek-coder-v2:16b    9.1GB   Q4_K_M    medium    Complex refactors
  codellama:13b            7.4GB   Q4_K_M    medium    Code Q&A
──────────────────────────────────────────────────────────────────────

Or type any custom model: ollama/qwen2.5:32b, openai/o3-mini, groq/llama-3.3-70b...
```

---

### 🛡️ 10. Air-Gapped Mode — 100% offline, zero data leaves your machine

```bash
k-cli airgap --enable
k "fix this auth bug"  # runs entirely locally, zero telemetry
```

Perfect for enterprise, regulated industries, or when you simply don't want your code leaving your laptop.

---

## Supported Models

| Provider | How K-CLI discovers them |
|---|---|
| **Ollama** (local, free) | Live query of `/api/tags` — every model you've pulled |
| **LM Studio** | Auto-detected at `localhost:1234` |
| **Google Gemini** | Dynamic API enumeration |
| **OpenAI** | Any GPT-4, o1, o3 model |
| **Anthropic Claude** | Claude 3.5, 3.7 Sonnet, Opus |
| **Groq** | Live query of `/v1/models` — high-speed LPU inference |
| **DeepSeek** | DeepSeek Coder, Reasoner |
| **Custom / fine-tuned** | Type any model string. No restrictions. |

---

## Keyboard Shortcuts (TUI)

| Key | Action |
|---|---|
| `Ctrl+O` | 📖 Codex Setup Hub (APIs, local models, DevDocs) |
| `Ctrl+U` | ⚡ 5-Model Swarm Audit |
| `Ctrl+M` | 🤖 Dynamic Model Hub |
| `Ctrl+A` | 🔑 Universal API Key Vault |
| `Ctrl+K` | ⚔️ 3-Way Merge Conflict Studio |
| `Ctrl+G` | 🐙 GitHub Command Center |
| `Ctrl+S` | 🛡️ Security Auto-Healer |
| `Ctrl+H` | 🏠 Local GitHub Hub |
| `Ctrl+R` | 🔥 Trending Repos |
| `Ctrl+L` | 🧹 Clear canvas |

### Slash commands

```
/audit <task>    → 5-model swarm audit
/swarm           → same as above
/codex           → open setup hub
/model           → switch model
/keys            → open API vault
/gh              → GitHub center
/conflict        → conflict studio
/security        → security scanner
/plan            → structured task planner
/demo            → watch a live demo (no API key needed)
/clear           → clear canvas
```

---

## Quickstart

### Option A — Local only (free, no API key)

```bash
# Install Ollama first: https://ollama.com
ollama pull qwen2.5-coder:7b   # 4.7GB, best free coding model

# Install K-CLI
curl -sSL https://raw.githubusercontent.com/krishivjoshi219-collab/K-Cli/main/install.sh | bash

# Launch
k
```

### Option B — With Cloud APIs (faster, smarter)

```bash
# Install
curl -sSL https://raw.githubusercontent.com/krishivjoshi219-collab/K-Cli/main/install.sh | bash

# Open Codex setup hub (auto-detects your keys)
k-cli codex

# Or set keys directly
k-cli keys set GEMINI_API_KEY=AIza...
k-cli keys set OPENAI_API_KEY=sk-...
k-cli keys set GROQ_API_KEY=gsk_...
```

### Option C — pip install

```bash
git clone https://github.com/krishivjoshi219-collab/K-Cli.git
cd K-Cli
pip install -e .
k-cli codex
```

---

## Architecture

```
K-CLI Project Bankai v0.4
│
├── k_cli/cli.py              → Typer CLI entry point (k-cli <command>)
├── k_cli/tui/tui_app.py      → Full-screen Textual workstation
│
├── k_cli/core/
│   ├── llm_driver.py         → Universal LLM driver (all providers)
│   ├── models_hub.py         → Dynamic model discovery (Ollama + Cloud)
│   ├── credentials.py        → Universal API key vault
│   ├── smart_router.py       → Cost-optimized model router
│   └── session.py            → Persistent session manager
│
├── k_cli/agents/
│   ├── adversarial_swarm.py  → 5+ model parallel audit consensus engine
│   └── subagents.py          → Specialized agent roles
│
├── k_cli/git/
│   ├── conflict_resolver.py  → 3-way semantic git conflict resolution
│   ├── verifier.py           → AST + compiler verification gate
│   ├── patcher.py            → Surgical diff patcher
│   ├── ai_bisect.py          → AI git bisect regression hunter
│   └── smart_git.py          → Git workflow automation
│
├── k_cli/github/
│   ├── github_client.py      → GitHub REST API v3 client
│   ├── github_engine.py      → PR review, CI inspect, release manager
│   ├── pr_watcher.py         → Autonomous PR watcher daemon
│   ├── local_hub.py          → Local GitHub Hub aggregator
│   ├── trending.py           → GitHub trending engine
│   └── dedup_engine.py       → Request deduplication (BM25 + AST)
│
└── k_cli/tools/
    ├── doc_retriever.py      → Offline DevDocs FTS5 database (Python, Rust, C++...)
    ├── mcp_client.py         → Model Context Protocol (MCP) client
    ├── security_healer.py    → AST security scanner + auto-patcher
    ├── synapse_graph.py      → Code dependency graph engine
    ├── repo_gardener.py      → Dead code + stale branch sweeper
    └── incident_triage.py    → Stack trace parser + fix generator
```

---

## Why not just use ChatGPT / Copilot / Cursor?

| Feature | ChatGPT | GitHub Copilot | Cursor | **K-CLI** |
|---|:---:|:---:|:---:|:---:|
| Lives in terminal | ✗ | ✓ | ✗ | ✅ |
| Watches crashes in background | ✗ | ✗ | ✗ | ✅ |
| 5+ models simultaneously | ✗ | ✗ | ✗ | ✅ |
| ANY model, no lock-in | ✗ | ✗ | ✗ | ✅ |
| Reviews + merges PRs | ✗ | ✗ | ✗ | ✅ |
| AI merge conflict resolution | ✗ | ✗ | ✗ | ✅ |
| Security scanner + auto-healer | ✗ | ✗ | partial | ✅ |
| AI git bisect | ✗ | ✗ | ✗ | ✅ |
| 100% offline / air-gapped | ✗ | ✗ | ✗ | ✅ |
| Free with local Ollama | ✗ | ✗ | ✗ | ✅ |
| Open source | ✗ | ✗ | ✗ | ✅ MIT |

---

## Contributing

PRs welcome! Run the tests first:

```bash
pip install -e .
pytest tests/ -v
```

114 tests, all passing. If you add a feature, add a test.

---

## License

MIT — build whatever you want with it.

---

<div align="center">

**Built by [@krishivjoshi219](https://github.com/krishivjoshi219-collab)**

⭐ Star this if you want "lazy dev autopilot" to become a real thing

[Report a Bug](https://github.com/krishivjoshi219-collab/K-Cli/issues) · [Request a Feature](https://github.com/krishivjoshi219-collab/K-Cli/issues) · [Discussions](https://github.com/krishivjoshi219-collab/K-Cli/discussions)

</div>
