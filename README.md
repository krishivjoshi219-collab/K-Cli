<div align="center">

```
██╗  ██╗      ██████╗██╗     ██╗
██║ ██╔╝     ██╔════╝██║     ██║
█████╔╝      ██║     ██║     ██║
██╔═██╗      ██║     ██║     ██║
██║  ██╗     ╚██████╗███████╗██║
╚═╝  ╚═╝      ╚═════╝╚══════╝╚═╝
  Project Bankai v1.0.0 — Agentic AI Workstation
```

**Stop switching tabs. Stop waiting for reviews. Stop debugging alone at 2am.**  
K-CLI is an AI agent that lives in your terminal, watches your code, and ships fixes — automatically.

[![PyPI](https://img.shields.io/pypi/v/k-cli-ai?color=blue&style=flat-square&logo=pypi)](https://pypi.org/project/k-cli-ai/)
[![CI](https://github.com/krishivjoshi219-collab/K-Cli/actions/workflows/ci.yml/badge.svg)](https://github.com/krishivjoshi219-collab/K-Cli/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-362%20passing-brightgreen?style=flat-square&logo=pytest)](tests/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square&logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Ollama](https://img.shields.io/badge/works%20offline-Ollama%20%2B%20local%20models-blueviolet?style=flat-square)](https://ollama.com)
[![Models](https://img.shields.io/badge/models-ANY%20%E2%80%94%20no%20lock--in-orange?style=flat-square)](#-use-any-model--no-lock-in-ever)
<br/>

<img src="assets/demo.gif" alt="K-CLI Demo Recording" width="100%" style="border-radius: 8px; border: 1px solid #30363d;" />

</div>

---

## ⚡ Get started in 30 seconds

```bash
# Option 1: One-line installer (Recommended)
curl -sSL https://raw.githubusercontent.com/krishivjoshi219-collab/K-Cli/main/install.sh | bash

# Option 2: Install directly from PyPI
pip install k-cli-ai

# Launch the full-screen Cyber TUI workstation:
k
```

> **No API key required.** K-CLI works 100% offline with [Ollama](https://ollama.com). Pull a free model and go:
> ```bash
> ollama pull qwen2.5-coder:7b   # 4.7 GB · best free coding model
> ```

---

## What is this?

You're mid-sprint. CI is broken. Your PR has 12 unreviewed comments. You've got 4 ChatGPT tabs open for the same bug. You're copy-pasting code back and forth and none of it compiles.

**K-CLI is what should have existed instead.**

It's not a chatbot. It's not autocomplete. It's a full **agentic AI workstation** that plugs into your terminal, your git repo, and your GitHub — and actually *does* things:

| Instead of… | K-CLI does… |
|---|---|
| Asking ChatGPT to fix a bug | Watches your crashes live, writes the patch, verifies it compiles, shows you a diff |
| Waiting 3 days for PR review | Reviews, comments, fixes, and merges the PR — autonomously |
| Manually resolving merge conflicts | 3-way semantic AI resolution — understands *why* both sides changed |
| Running one model and hoping | Runs **5 models simultaneously**, peer-reviews them against each other, picks the winner |
| Googling "which AI model is best" | Discovers every model on your system — Ollama, Groq, Gemini, GPT-4 — automatically |
| Setting up 6 different AI tools | One install. One terminal. Everything in one TUI. |

---

## The TUI

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ ⚡ K-CLI v1.0 · Bankai  │ 🤖 gemini-2.5-flash  │  main (+3 ~0)  │ 🏎️ 248 tok/s  │ 💰 $0.031 saved │
├──────────────────┬──────────────────────────────────────────┬────────────────────────┤
│ 🚀 LAUNCHER      │ 💬 K-CLI Agentic Workstation              │  📜 LIVE DIFFS         │
│                  │                                          │    auth.py   (+42 −7)  │
│ [ ⚡ 5-Swarm ]   │ > audit my auth module for vulns         │    models.py (+18 −0)  │
│ [ 🤖 Models ]    │                                          │    tests/    (+53 −0)  │
│ [ 📖 Codex ]     │ ╔══ 🧠 Thinking (1.2s)... ▼             │                        │
│ [ 🔑 API Keys ]  │ ║ · Scanning AST context                 │  ⚡ BACKGROUND          │
│ [ 👻 Ghost ]     │ ║ · 5 models generating in parallel      │    Swarm: 5/5 active   │
│ [ ⚔️ Conflicts ] │ ║ · Cross-model peer review running      │    Ghost: monitoring   │
│ [ 🐙 GitHub ]    │ ╚══════════════════════════════════      │    Verifier: AST ✓     │
│ [ 🛡️ Security ]  │                                          │                        │
│ [ 🎯 Bisect ]    │ 🔴 CRITICAL  SQL injection · line 47     │  📊 TELEMETRY          │
│ [ 👁️ PR Watch ]  │ 🟡 WARNING   Weak JWT salt  · line 83   │    Tokens:  2,847      │
│ [ 🌿 Garden ]    │ 🟡 WARNING   No rate limiting             │    Cost:    $0.031     │
│ [ 💬 Explain ]   │                                          │    TTFT:    0.12s      │
│ [ 🏗️ Scaffold ]  │ ✅ Auto-healer patched 3 issues          │                        │
│                  │ ✅ AST verified · 53 tests pass           │                        │
└──────────────────┴──────────────────────────────────────────┴────────────────────────┘
  Ctrl+O Codex · Ctrl+U 5-Swarm · Ctrl+M Models · Ctrl+A Keys · Ctrl+K Conflicts
```

```bash
k              # full-screen TUI workstation
k-cli ui       # same
k-cli codex    # interactive setup wizard (APIs, local models, offline docs)
k "fix the auth bug"   # inline — no TUI needed
```

---

## Features

### 🤖 Use ANY model — no lock-in, ever

K-CLI has **no hardcoded model list.** It queries Ollama's `/api/tags` endpoint live to discover every model on your machine. It hits Groq's `/v1/models` to list high-speed cloud options. You can type any model string, from any provider, that you want — and K-CLI routes it.

```bash
k-cli audit "implement a rate limiter" \
  --models "gemini-2.0-flash,claude-3-7-sonnet,deepseek-reasoner,gpt-4o,qwen2.5-coder:7b"
```

Any format works: `ollama/llama3.2`, `openai/o3-mini`, `groq/llama-3.3-70b-versatile`, `anthropic/claude-3-7-sonnet`, `krishivjoshi/my-fine-tune`. If your backend serves it, K-CLI runs it.

```
✔  gemini-2.0-flash     0.84s  ·  847 tok  ·  AST ✓
✔  claude-3-7-sonnet    1.24s  · 1203 tok  ·  AST ✓
✔  deepseek-reasoner    2.10s  · 2847 tok  ·  AST ✓  ← winner (score: 9.2/10)
✔  gpt-4o               0.97s  ·  934 tok  ·  AST ✓
✔  qwen2.5-coder:7b     3.41s  · 1102 tok  ·  AST ✓
```

---

### ⚡ 5-Model Parallel Swarm Audit

Stop trusting one model's output. K-CLI runs **5+ models simultaneously**, then makes them peer-review each other's code, then runs AST + compiler verification on all candidates. The winner is selected — or synthesized — by consensus.

Press **`Ctrl+U`** in the TUI, or use the CLI:

```bash
k-cli audit "thread-safe connection pool in Python" \
  --models "gemini-2.0-flash,gpt-4o,claude-3-7-sonnet,deepseek-reasoner,qwen2.5-coder:7b"
```

```
⚡ 5-Model Swarm Audit & Consensus
──────────────────────────────────────────────────────────────────────
  Model                Latency   Tokens   AST    Peer Review Score
  ────────────────────────────────────────────────────────────────
  deepseek-reasoner    2.1s      2847     ✓      9.2 / 10  ◀ WINNER
  claude-3-7-sonnet    1.2s      1203     ✓      8.8 / 10
  gemini-2.0-flash     0.8s       847     ✓      8.4 / 10
  gpt-4o               1.0s       934     ✓      8.1 / 10
  qwen2.5-coder:7b     3.4s      1102     ✓      7.9 / 10
──────────────────────────────────────────────────────────────────────
  Consensus achieved · 100% AST pass · Applying winner
```

---

### 👻 Ghost Terminal — heals crashes automatically

Wrap any command in Ghost. The moment it sees a traceback, K-CLI extracts AST context, generates a surgical patch, verifies it compiles and tests pass, and shows you a 1-keypress diff. No copy-pasting. No tab switching.

```bash
k-cli ghost "pytest"        # wrap your test runner
k-cli ghost "npm run dev"   # wrap your dev server
k-cli ghost "cargo build"   # wrap your compiler
```

```
👻  GHOST AUTOPILOT TRIGGERED
────────────────────────────────────────────────────────────
  Intercepted: TypeError at src/auth/middleware.py:42
  Root cause:  jwt.decode() missing algorithms= kwarg
  Confidence:  97.3%  ·  Patch: 1 line

  [ Y  Apply ]  [ D  View diff ]  [ N  Skip ]  [ S  Open in TUI ]
```

---

### ⚔️ AI Merge Conflict Studio

Not "pick ours or theirs." K-CLI does **3-way semantic AST resolution** — it understands the *intent* of both branches and generates a resolution that keeps both.

```bash
k-cli conflict list                               # find all conflicts
k-cli conflict resolve                            # AI resolves everything
k-cli conflict resolve --file src/auth.py --auto-accept
```

```
⚔️  Conflict Studio — src/auth.py
────────────────────────────────────────────────────────────
  Base intent:    IP-based rate limiting (class method)
  HEAD adds:      Redis distributed rate limiter
  Incoming adds:  In-memory LRU fallback
  Resolution:     Redis-primary + LRU fallback (both preserved)  ✓
  AST verified:   ✓   Tests pass: ✓
```

---

### 🐙 Full GitHub PR Lifecycle

```bash
k-cli pr list                          # see open PRs
k-cli pr review 42                     # AI reviews: bugs, security, performance
k-cli pr review 42 --post-comment      # posts the review as a GitHub comment
k-cli pr fix 42                        # checks out, fixes, verifies, pushes
k-cli pr merge 42 --method squash      # merges when CI passes
```

---

### 🛡️ Security Auto-Healer

```bash
k-cli security scan .            # scan the whole codebase
k-cli security heal src/auth.py  # fix all vulnerabilities in one file
```

```
🛡️  Security Scan · src/auth.py
────────────────────────────────────────────────────────────
  🔴 CRITICAL  SQL injection via f-string interpolation  (line 47)
  🟡 WARNING   No rate limiting on /login                (line 83)
  🟡 WARNING   JWT secret hardcoded                      (line 12)
  🟢 INFO      HTTPS enforced

  Healing... [████████████████████] 3/3 patches applied · Tests pass ✓
```

---

### 🎯 AI Git Bisect

K-CLI binary-searches your git history to find the **exact commit** that introduced a regression, then explains what changed and suggests a fix.

```bash
k-cli bisect "pytest tests/ -q"
```

```
🎯  AI Git Bisect — 847 commits searched
────────────────────────────────────────────────────────────
  Bad commit:  a3f9c2d  (2 days ago)
  Author:      @you
  Message:     "refactor: extract auth middleware"
  Culprit:     refresh_token() removed at middleware.py:127
  Fix:         Restore handler — suggested patch ready
```

---

### 🌿 Repo Gardener

```bash
k-cli garden --sweep
```

Sweeps for dead code, stale branches (90+ days inactive), duplicate functions, TODO/FIXME comments with AI-suggested resolutions, and missing docstrings. All actionable with 1-click apply.

---

### 🛡️ Air-Gapped Mode

```bash
k-cli airgap --enable
k "refactor this module"   # runs 100% locally — zero bytes leave your machine
```

Zero telemetry. No cloud calls. Enterprise-ready. Works with any local Ollama model.

---

## Supported providers

| Provider | Discovery method |
|---|---|
| **Ollama** (local, free) | Live `/api/tags` — every model you've pulled, with param size + quant |
| **LM Studio / vLLM** | Auto-detected at `localhost:1234`, `localhost:8000` |
| **Google Gemini** | Dynamic API enumeration |
| **OpenAI** | GPT-4o, o1, o3, custom deployments |
| **Anthropic Claude** | Claude 3.5, 3.7 Sonnet, Opus |
| **Groq** | Live `/v1/models` — LPU inference, fastest available |
| **DeepSeek** | DeepSeek-Coder, DeepSeek-Reasoner |
| **Any custom model** | Type any string. No validation. No restrictions. |

---

## Keyboard shortcuts

| Key | Action |
|---|---|
| `Ctrl+O` | 📖 Codex Hub — setup APIs, local models, offline docs |
| `Ctrl+U` | ⚡ 5-Model Swarm Audit |
| `Ctrl+M` | 🤖 Dynamic Model Hub |
| `Ctrl+A` | 🔑 Universal API Key Vault |
| `Ctrl+K` | ⚔️ 3-Way Merge Conflict Studio |
| `Ctrl+G` | 🐙 GitHub Command Center |
| `Ctrl+S` | 🛡️ Security Auto-Healer |
| `Ctrl+H` | 🏠 Local GitHub Hub |
| `Ctrl+R` | 🔥 Trending Repos |
| `Ctrl+L` | 🧹 Clear canvas |
| `Ctrl+Q` | 💤 Quit |

**Slash commands** (type in the chat canvas):

```
/audit <task>   → 5-model swarm audit
/demo           → live demo — no API key needed
/codex          → open setup hub
/model          → switch active model
/keys           → open API vault
/gh             → GitHub center
/conflict       → conflict studio
/security       → security scanner
/plan           → structured task planner
/clear          → clear canvas
```

---

## Quickstart

### Free — local only (no API key)

```bash
# 1. Get Ollama: https://ollama.com
ollama pull qwen2.5-coder:7b

# 2. Install K-CLI
curl -sSL https://raw.githubusercontent.com/krishivjoshi219-collab/K-Cli/main/install.sh | bash

# 3. Go
k
```

### With Cloud APIs

```bash
curl -sSL https://raw.githubusercontent.com/krishivjoshi219-collab/K-Cli/main/install.sh | bash
k-cli codex   # auto-detects any API keys already in your env

# or set them directly:
k-cli keys set GEMINI_API_KEY=AIza...
k-cli keys set OPENAI_API_KEY=sk-...
k-cli keys set GROQ_API_KEY=gsk_...
```

### pip / git

```bash
git clone https://github.com/krishivjoshi219-collab/K-Cli.git && cd K-Cli
pip install -e . && k-cli codex
```

---

## Why not just use ChatGPT / Copilot / Cursor?

| | ChatGPT | Copilot | Cursor | **K-CLI** |
|---|:---:|:---:|:---:|:---:|
| Lives in your terminal | ✗ | ✓ | ✗ | ✅ |
| Watches crashes & self-heals | ✗ | ✗ | ✗ | ✅ |
| 5+ models simultaneously | ✗ | ✗ | ✗ | ✅ |
| Any model — no lock-in | ✗ | ✗ | ✗ | ✅ |
| Reviews & merges PRs | ✗ | ✗ | ✗ | ✅ |
| AI merge conflict resolution | ✗ | ✗ | ✗ | ✅ |
| Security scanner + auto-healer | ✗ | ✗ | partial | ✅ |
| AI git bisect | ✗ | ✗ | ✗ | ✅ |
| 100% offline / air-gapped | ✗ | ✗ | ✗ | ✅ |
| Free with Ollama | ✗ | ✗ | ✗ | ✅ |
| Open source (MIT) | ✗ | ✗ | ✗ | ✅ |

---

## Architecture

```
k_cli/
├── cli.py                 Typer CLI — k-cli <command>
├── tui/tui_app.py         Full-screen Textual workstation
│
├── core/
│   ├── llm_driver.py      Universal LLM driver (all providers)
│   ├── models_hub.py      Live model discovery — Ollama + Cloud APIs
│   ├── credentials.py     Universal API key vault
│   ├── smart_router.py    Cost-optimised model router
│   └── session.py         Persistent session manager
│
├── agents/
│   ├── adversarial_swarm.py   5+ model parallel audit consensus
│   └── subagents.py           Specialised agent roles
│
├── git/
│   ├── conflict_resolver.py   3-way semantic conflict resolution
│   ├── verifier.py            AST + compiler verification gate
│   ├── patcher.py             Surgical diff patcher
│   ├── ai_bisect.py           AI git bisect regression hunter
│   └── smart_git.py           Git workflow automation
│
├── github/
│   ├── github_client.py       GitHub REST API v3 client
│   ├── github_engine.py       PR review, CI inspector, release manager
│   ├── pr_watcher.py          Autonomous PR watcher daemon
│   ├── local_hub.py           Local GitHub Hub aggregator
│   ├── trending.py            GitHub trending engine
│   └── dedup_engine.py        Request dedup — BM25 + AST similarity
│
└── tools/
    ├── doc_retriever.py       Offline FTS5 docs — Python, Rust, C++, Linux...
    ├── mcp_client.py          MCP (Model Context Protocol) client
    ├── security_healer.py     AST security scanner + auto-patcher
    ├── synapse_graph.py       Code dependency graph
    ├── repo_gardener.py       Dead code + stale branch sweeper
    └── incident_triage.py     Stack trace parser + fix generator
```

---

## Contributing

```bash
git clone https://github.com/krishivjoshi219-collab/K-Cli.git && cd K-Cli
python3 -m venv .venv && source .venv/bin/activate
pip install -e . && pytest tests/ -v   # 114 tests — all green
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for what's open to build, and [ROADMAP.md](ROADMAP.md) for what's coming next.

---

## License

MIT. Build whatever you want.

---

<div align="center">

Made by **[@krishivjoshi219](https://github.com/krishivjoshi219-collab)**

**⭐ If this saves you even one debugging session, star it.**  
That's what keeps this going.

[🐛 Report a bug](https://github.com/krishivjoshi219-collab/K-Cli/issues/new?template=bug_report.md) · [💡 Request a feature](https://github.com/krishivjoshi219-collab/K-Cli/issues/new?template=feature_request.md) · [💬 Discussions](https://github.com/krishivjoshi219-collab/K-Cli/discussions)

</div>
