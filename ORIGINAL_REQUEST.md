# Original User Request

## 2026-08-14T14:33:29Z

Refactor and evolve K-CLI into a flagship-tier local AI coding CLI (comparable in architecture and polish to Aider and Copilot CLI) while strictly preserving its core philosophy: < 1GB RAM budget, offline privacy, compiler-grounded verification, and zero bloat.

Working directory: /home/k/k_cli
Integrity mode: development

## Requirements

### R1. Flagship Modular Architecture & Clean Separation of Concerns
Refactor the codebase into clean, decoupled domain modules:
- Core Engine (verifier.py, orchestrator.py, llm_driver.py)
- Knowledge & Context Layer (doc_retriever.py, repo_map.py)
- Modification & Version Control Layer (patcher.py, git_guard.py)
- User Interface & Session Management (session.py, cli.py)

### R2. Offline DevDocs SQLite Indexer & Precision Retriever (doc_retriever.py)
Build an embedded SQLite FTS5 database indexing standard library and common framework API documentation. Implement BM25 search to inject pinpoint (< 250 token) exact signature snippets into the SLM planning context, eliminating API hallucination with < 5ms query latency and < 5 MB RAM.

### R3. AST Codebase Repository Map (repo_map.py)
Implement an AST-driven repository symbol extractor and ranker that builds a concise architectural snapshot (< 400 tokens) of classes, functions, and call signatures across the workspace for context-aware code generation.

### R4. SEARCH/REPLACE Surgical Patch Engine (patcher.py) & Git Safety Net (git_guard.py)
Support unified search/replace block patching for surgical edits to existing files. Automatically create atomic Git commits with semantic commit messages on verified success, and trigger instant git restore rollbacks if the compiler/test verifier fails.

### R5. Interactive Multi-Turn Session & Command Hub (session.py, cli.py)
Elevate the interactive terminal REPL with session context history, token budgeting, and slash commands (/add, /undo, /diff, /clear, /status, /model, /help).

## Acceptance Criteria

### Verification & Test Suite
- [ ] 100% of existing 33 unit and integration tests pass without regression (pytest tests/ -v).
- [ ] Comprehensive new test suites for doc_retriever, repo_map, patcher, git_guard, and session pass cleanly with full coverage.
- [ ] All code modifications pass static AST validation (ast.parse) and compiler checks.

### Performance & Memory Budget
- [ ] Peak system RSS memory consumption remains strictly under 1024 MB across all operations and model loads.
- [ ] SQLite FTS5 search executes in < 5ms with < 10 MB database overhead.
- [ ] Repo map generation takes < 250ms on standard repositories.

### End-to-End Workflow Validation
- [ ] Single command k "prompt" and interactive REPL mode k work seamlessly out of the box.
- [ ] Failed verifications trigger automated multi-attempt repair diffs and roll back cleanly if unresolved.
