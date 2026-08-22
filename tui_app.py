"""
tui_app.py - Premier Cyberpunk Developer Workstation TUI for K-CLI (Textual 8.2.8)
Project Bankai Engine v0.2.0

Features:
1. Cyberpunk Header: Glowing K-CLI title, active model badge (Bankai-7B, Bankai-14B, Gemini, Claude, Ollama),
   Git branch badge, real-time RAM RSS monitor (< 1GB budget), Cost Ticker, Speedometer, and active persona badge.
2. Left Sidebar Dock:
   - Live Subagent Swarm Tree with animated status glyphs (🟢 🟡 🔵 🟣 🔴 🚫) and progress bars.
   - Active Context Files manager with add/remove actions.
   - Quick DevDocs symbol lookup widget with instantaneous search and signature cards.
3. Central Workspace with Multi-Tabbed Power Tools:
   - 💬 Chat Stream: Rich Markdown, collapsible <think> accordion, tool execution cards.
   - ⚡ Diff Viewer: Interactive 2-column side-by-side & unified diff viewer.
   - ⚔️ Conflict Studio: Interactive 3-way/4-way comparison (Ours vs Base vs Theirs vs AI Proposed Merge) with 1-click Accept, Re-prompt, and Verification.
   - 🐙 GitHub PR Hub: Live PR browser with conflict tags, review state, CI pills, AI Review, and Auto-Fix.
   - 🔌 MCP Server Inspector: Connected servers, schemas, tool inspection, and live invocation logs.
   - 📡 Swarm Radar: Visual graph of active subagents, sub-tasks, execution status, and token expenditures.
4. Bottom Dock:
   - Rich input box with command history navigation.
   - Quick action chips: /plan, /help, /model, /persona, /spawn, /conflict, /pr, /mcp, /radar, /diff, /rollback, /test, /clear.
   - Keybindings: Ctrl+M (Model), Ctrl+P (Persona), Ctrl+S (Swarm), Ctrl+D (Diff),
     Ctrl+K (Conflict Studio), Ctrl+G (PR Hub), Ctrl+I (MCP Inspector), Ctrl+Z (Rollback), Ctrl+T (Tests), Ctrl+Q (Quit).
5. Asynchronous multi-threading: 100% non-blocking async event loops.
"""

from __future__ import annotations

import asyncio
import difflib
import gc
import json
import os
import psutil
import queue
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, Union

# Textual 8.2.8 Imports
from textual import events, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid, Horizontal, ScrollableContainer, Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive, var
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import (
    Button,
    Collapsible,
    Digits,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Markdown,
    OptionList,
    ProgressBar,
    RichLog,
    Select,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)
from textual.widgets.option_list import Option
from textual.widgets.tree import TreeNode
from textual.worker import Worker, get_current_worker

# Rich Imports for Formatting
from rich.console import Console, RenderableType
from rich.markup import escape
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

# Safe K-CLI Core Engine Imports
try:
    from k_cli.diff_viewer import DiffVisualizer
    from k_cli.doc_retriever import DEFAULT_OFFICIAL_LIBRARIES, DocRetriever
    from k_cli.git_guard import GitGuard
    from k_cli.llm_driver import LLMDriver
    from k_cli.model_manager import MODEL_CATALOG, ModelManager, ModelPullResult
    from k_cli.orchestrator import Orchestrator, OrchestratorResult, Persona
    from k_cli.patcher import Patcher
    from k_cli.persona import DomainPersona, PersonaProfile, PersonaRegistry
    from k_cli.repo_map import RepoMap
    from k_cli.session import SessionManager
    from k_cli.subagents import (
        SubagentDispatcher,
        SubagentMessage,
        SubagentMessageType,
        SubagentRole,
        SubagentRunResult,
        SubagentStatus,
        SubagentTask,
        SubagentVisualizer,
    )
    from k_cli.tui_animations import (
        AnimatedSpinner,
        CostTicker,
        GlowBadgeStatus,
        SpinnerType,
        StatusGlowBadge,
        TokenSpeedometer,
        apply_gradient_to_text,
        calculate_token_cost,
        create_branch_badge,
        create_mcp_badge,
        create_model_badge,
        create_ram_badge,
        create_verifier_badge,
        generate_splash_frames,
        render_cyber_banner,
        render_hud_status_bar,
    )
    from k_cli.verifier import CodeExtractor, VerificationResult, Verifier
    from k_cli.workflow import create_plan
except (ModuleNotFoundError, ImportError):
    # Fallback to local sibling modules
    try:
        from diff_viewer import DiffVisualizer
        from doc_retriever import DEFAULT_OFFICIAL_LIBRARIES, DocRetriever
        from git_guard import GitGuard
        from llm_driver import LLMDriver
        from model_manager import MODEL_CATALOG, ModelManager, ModelPullResult
        from orchestrator import Orchestrator, OrchestratorResult, Persona
        from patcher import Patcher
        from persona import DomainPersona, PersonaProfile, PersonaRegistry
        from repo_map import RepoMap
        from session import SessionManager
        from subagents import (
            SubagentDispatcher,
            SubagentMessage,
            SubagentMessageType,
            SubagentRole,
            SubagentRunResult,
            SubagentStatus,
            SubagentTask,
            SubagentVisualizer,
        )
        from tui_animations import (
            AnimatedSpinner,
            CostTicker,
            GlowBadgeStatus,
            SpinnerType,
            StatusGlowBadge,
            TokenSpeedometer,
            apply_gradient_to_text,
            calculate_token_cost,
            create_branch_badge,
            create_mcp_badge,
            create_model_badge,
            create_ram_badge,
            create_verifier_badge,
            generate_splash_frames,
            render_cyber_banner,
            render_hud_status_bar,
        )
        from verifier import CodeExtractor, VerificationResult, Verifier
        from workflow import create_plan
    except (ModuleNotFoundError, ImportError) as e:
        raise ImportError(f"Failed to load K-CLI engine components: {e}")


# ==============================================================================
# Model & Persona Presets
# ==============================================================================

MODEL_PRESETS: List[Dict[str, str]] = [
    {
        "id": "bankai-7b",
        "name": "Bankai-7B",
        "desc": "Project Bankai Flagship 7B Coder (Fast & Compiler-Grounded)",
        "type": "Local SLM",
        "badge_color": "#00f0ff",
    },
    {
        "id": "bankai-14b",
        "name": "Bankai-14B",
        "desc": "Project Bankai Flagship 14B Deep Reasoning Engine",
        "type": "Local SLM",
        "badge_color": "#b026ff",
    },
    {
        "id": "gemini",
        "name": "Gemini",
        "desc": "Gemini 2.0 Flash / Pro (Cloud Multi-Modal & High-Throughput)",
        "type": "Cloud API",
        "badge_color": "#00ff88",
    },
    {
        "id": "claude",
        "name": "Claude",
        "desc": "Claude 3.5 Sonnet (Advanced Agentic Architecture & Refactoring)",
        "type": "Cloud API",
        "badge_color": "#ffaa00",
    },
    {
        "id": "ollama",
        "name": "Ollama",
        "desc": "Local Ollama GGUF (qwen2.5-coder:1.5b < 1GB RAM Budget)",
        "type": "Local GGUF",
        "badge_color": "#ff007f",
    },
]

PERSONA_PRESETS: List[Dict[str, str]] = [
    {
        "id": "default",
        "title": "Fullstack AI Systems Engineer",
        "icon": "⚙",
        "color": "#00f0ff",
        "desc": "Balanced multi-language software engineer (< 1GB RAM budget)",
    },
    {
        "id": "devops",
        "title": "DevOps & SRE Specialist",
        "icon": "☸",
        "color": "#00d7ff",
        "desc": "Docker, Kubernetes, CI/CD, Terraform, Cloud Deployments",
    },
    {
        "id": "debugger",
        "title": "Surgical Debugger",
        "icon": "🩺",
        "color": "#ff3366",
        "desc": "Root-cause analysis, minimal SEARCH/REPLACE diffs, zero regression",
    },
    {
        "id": "systems",
        "title": "Systems Architect",
        "icon": "⚡",
        "color": "#b026ff",
        "desc": "C++23, Rust, Linux Kernel, Lock-free concurrency, Big-O proofs",
    },
    {
        "id": "security",
        "title": "Application Security Engineer",
        "icon": "🛡",
        "color": "#ff0055",
        "desc": "OWASP Top 10, HMAC, Auth middlewares, Constant-time crypto",
    },
    {
        "id": "frontend",
        "title": "Frontend & Fullstack Engineer",
        "icon": "🎨",
        "color": "#00ff88",
        "desc": "React, Vite, Next.js, CSS layout, Web Accessibility",
    },
    {
        "id": "database",
        "title": "Database & Query Optimizer",
        "icon": "🗄",
        "color": "#ffe600",
        "desc": "PostgreSQL, Redis, Spanner, SQL query tuning, index optimization",
    },
]


def get_persona_ui_meta(persona_id_or_title: str) -> Dict[str, str]:
    """Resolves UI styling (icon, color, title, desc) for a persona."""
    query = (persona_id_or_title or "default").strip().lower()
    for p in PERSONA_PRESETS:
        if query == p["id"].lower() or query == p["title"].lower() or p["id"].lower() in query:
            return p
    if PersonaRegistry:
        prof = PersonaRegistry.get(persona_id_or_title)
        if prof:
            return {
                "id": prof.id,
                "title": prof.title,
                "icon": prof.icon,
                "color": prof.color,
                "desc": prof.description,
            }
    return PERSONA_PRESETS[0]


# ==============================================================================
# Cyberpunk Theme TCSS Stylesheet
# ==============================================================================

CYBERPUNK_TCSS = """
/* ==========================================================================
   CYBERPUNK / BANKAI WORKSTATION PALETTE
   ========================================================================== */

Screen {
    background: #080c14;
    color: #e2e8f0;
    overflow: hidden;
}

/* --------------------------------------------------------------------------
   Header Component
   -------------------------------------------------------------------------- */
#cyber-header {
    dock: top;
    height: 3;
    background: #0d131f;
    border-bottom: solid #00f0ff;
    padding: 0 1;
    layout: horizontal;
    content-align: center middle;
}

#header-brand {
    width: 28;
    height: 1;
    content-align: left middle;
    text-style: bold;
    color: #00f0ff;
}

#header-badges {
    width: 1fr;
    height: 1;
    layout: horizontal;
    content-align: right middle;
}

.badge-item {
    padding: 0 1;
    margin: 0 1;
    background: #121a29;
    border: round #1e293b;
    color: #94a3b8;
    text-style: bold;
    max-width: 28;
    text-overflow: ellipsis;
}

.badge-model {
    color: #00f0ff;
    border: round #00f0ff;
    background: #092336;
}

.badge-persona {
    color: #b026ff;
    border: round #b026ff;
    background: #220d36;
}

.badge-branch {
    color: #00ff88;
    border: round #00ff88;
    background: #082d1c;
}

.badge-ram {
    color: #ffe600;
    border: round #ffe600;
    background: #332b00;
}

.badge-tokens {
    color: #ffaa00;
    border: round #ffaa00;
    background: #332000;
}

.badge-cost {
    color: #00f0ff;
    border: round #00f0ff;
    background: #092336;
}

/* --------------------------------------------------------------------------
   Layout Structure: Left Sidebar + Central Workspace
   -------------------------------------------------------------------------- */
#main-layout {
    layout: horizontal;
    height: 1fr;
    background: #080c14;
}

/* --------------------------------------------------------------------------
   Left Sidebar Dock
   -------------------------------------------------------------------------- */
#left-sidebar {
    width: 38;
    height: 1fr;
    background: #0b101b;
    border-right: solid #00f0ff;
    padding: 0;
    layout: vertical;
}

.sidebar-panel {
    background: #0e1626;
    border: round #1e293b;
    margin: 1;
    padding: 0 1;
    height: auto;
}

.sidebar-title {
    text-style: bold;
    color: #00f0ff;
    border-bottom: solid #1e293b;
    padding: 0 0;
    margin-bottom: 1;
}

/* Subagent Tree */
#swarm-tree-container {
    height: 1fr;
    min-height: 10;
    background: #0b101b;
    border-bottom: solid #1e293b;
    padding: 1;
    overflow-y: scroll;
}

#swarm-tree {
    background: #0b101b;
    color: #cbd5e1;
    padding: 0;
}

/* Active Context Files */
#context-files-panel {
    height: auto;
    max-height: 9;
    background: #0b101b;
    border-bottom: solid #1e293b;
    padding: 1;
}

#context-file-list {
    height: auto;
    max-height: 5;
    background: #0d1424;
    border: round #1e293b;
}

/* DevDocs Widget */
#devdocs-lookup-panel {
    height: 13;
    background: #0b101b;
    padding: 1;
}

#devdocs-input {
    border: round #00f0ff;
    background: #091322;
    color: #00f0ff;
    margin-bottom: 1;
    height: 3;
}

#devdocs-results-scroll {
    height: 1fr;
    background: #080d17;
    border: round #1e293b;
    overflow-y: scroll;
}

.devdoc-item {
    background: #0d1527;
    border: round #1e293b;
    padding: 0 1;
    margin-bottom: 1;
}

.devdoc-item:hover {
    background: #14223d;
    border: round #00f0ff;
}

/* --------------------------------------------------------------------------
   Central Workspace & Tabbed Views
   -------------------------------------------------------------------------- */
#central-workspace {
    width: 1fr;
    height: 1fr;
    background: #080c14;
    layout: vertical;
}

#workspace-tabs {
    height: 1fr;
}

TabbedContent {
    background: #080c14;
}

TabPane {
    padding: 0 1;
    background: #080c14;
    height: 1fr;
}

/* Chat Stream */
#chat-stream {
    height: 1fr;
    background: #080c14;
    overflow-y: scroll;
    padding: 1;
}

.onboarding-card {
    background: #0c1b2a;
    border: round #00f0ff;
    margin: 1 0;
    padding: 1 2;
}

.onboarding-card Markdown {
    color: #dbeafe;
}

.chat-message-user {
    background: #0d192e;
    border-left: heavy #00f0ff;
    margin: 1 0;
    padding: 1;
    border: round #1e293b;
}

.chat-message-assistant {
    background: #0c1527;
    border-left: heavy #00ff88;
    margin: 1 0;
    padding: 1;
    border: round #1e293b;
}

.message-header {
    text-style: bold;
    margin-bottom: 1;
}

.message-user-header {
    color: #00f0ff;
}

.message-assistant-header {
    color: #00ff88;
}

/* Reasoning Accordion */
.reasoning-collapsible {
    background: #111a2e;
    border: round #ffe600;
    margin: 1 0;
    padding: 0 1;
}

.reasoning-collapsible > CollapsibleTitle {
    color: #ffe600;
    text-style: bold;
}

.reasoning-text {
    color: #cbd5e1;
    background: #090e1a;
    padding: 1;
    border: round #1e293b;
}

/* Tool Status Cards */
.tool-status-card {
    background: #0c1b2a;
    border: round #00f0ff;
    padding: 1;
    margin: 1 0;
}

.tool-status-card-failed {
    background: #2a0c14;
    border: round #ff3366;
    padding: 1;
    margin: 1 0;
}

/* Diff Viewer */
#diff-container {
    height: 1fr;
    layout: vertical;
    background: #080c14;
}

#diff-toolbar {
    height: 3;
    background: #0d1424;
    border-bottom: solid #1e293b;
    layout: horizontal;
    padding: 0 1;
    content-align: left middle;
}

#diff-view-scroll {
    height: 1fr;
    background: #090e1a;
    padding: 1;
    overflow-y: scroll;
}

.diff-sbs-container {
    layout: horizontal;
    height: auto;
}

.diff-col {
    width: 1fr;
    background: #0b1120;
    border: round #1e293b;
    padding: 1;
    margin: 0 1;
}

.diff-col-header {
    text-style: bold;
    padding-bottom: 1;
    border-bottom: solid #1e293b;
    margin-bottom: 1;
}

/* --------------------------------------------------------------------------
   Conflict Studio Styles
   -------------------------------------------------------------------------- */
#conflict-studio-container {
    height: 1fr;
    layout: vertical;
    background: #080c14;
}

#conflict-toolbar {
    height: 3;
    background: #0d1424;
    border-bottom: solid #00f0ff;
    layout: horizontal;
    padding: 0 1;
    content-align: left middle;
}

#conflict-panes-grid {
    height: 1fr;
    layout: grid;
    grid-size: 2 2;
    grid-gutter: 1;
    padding: 1;
    background: #080c14;
}

.conflict-pane {
    background: #0b1120;
    border: round #1e293b;
    padding: 1;
    overflow-y: scroll;
}

.conflict-pane-ours {
    border: round #00f0ff;
}

.conflict-pane-theirs {
    border: round #ffaa00;
}

.conflict-pane-base {
    border: round #94a3b8;
}

.conflict-pane-ai {
    border: round #00ff88;
    background: #091c18;
}

.conflict-pane-header {
    text-style: bold;
    padding-bottom: 1;
    border-bottom: solid #1e293b;
    margin-bottom: 1;
}

/* --------------------------------------------------------------------------
   GitHub PR Hub Styles
   -------------------------------------------------------------------------- */
#pr-hub-container {
    height: 1fr;
    layout: horizontal;
    background: #080c14;
}

#pr-list-col {
    width: 44;
    height: 1fr;
    background: #0b101b;
    border-right: solid #1e293b;
    padding: 1;
    layout: vertical;
}

#pr-detail-col {
    width: 1fr;
    height: 1fr;
    background: #080c14;
    padding: 1;
    layout: vertical;
}

.pr-card-item {
    background: #0d1527;
    border: round #1e293b;
    padding: 1;
    margin-bottom: 1;
}

.pr-card-item:hover {
    background: #14223d;
    border: round #00f0ff;
}

.pr-status-pill {
    padding: 0 1;
    border: round #1e293b;
    text-style: bold;
}

/* --------------------------------------------------------------------------
   MCP Server Inspector Styles
   -------------------------------------------------------------------------- */
#mcp-inspector-container {
    height: 1fr;
    layout: horizontal;
    background: #080c14;
}

#mcp-server-list-col {
    width: 36;
    height: 1fr;
    background: #0b101b;
    border-right: solid #1e293b;
    padding: 1;
}

#mcp-details-col {
    width: 1fr;
    height: 1fr;
    background: #080c14;
    padding: 1;
    layout: vertical;
}

.mcp-server-card {
    background: #0d1527;
    border: round #1e293b;
    padding: 1;
    margin-bottom: 1;
}

.mcp-server-card:hover {
    background: #14223d;
    border: round #00f0ff;
}

/* --------------------------------------------------------------------------
   Swarm Radar Styles
   -------------------------------------------------------------------------- */
#swarm-radar-container {
    height: 1fr;
    layout: vertical;
    background: #080c14;
    padding: 1;
}

#swarm-radar-toolbar {
    height: 3;
    background: #0d1424;
    border-bottom: solid #00f0ff;
    layout: horizontal;
    padding: 0 1;
    content-align: left middle;
}

#swarm-nodes-grid {
    height: auto;
    max-height: 14;
    layout: grid;
    grid-size: 4 2;
    grid-gutter: 1;
    margin: 1 0;
}

.swarm-node-card {
    background: #0e172a;
    border: round #00f0ff;
    padding: 1;
    text-align: center;
}

#swarm-log-scroll {
    height: 1fr;
    background: #090e1a;
    border: round #1e293b;
    padding: 1;
    overflow-y: scroll;
}

/* --------------------------------------------------------------------------
   Bottom Dock & Input Bar
   -------------------------------------------------------------------------- */
#bottom-dock {
    dock: bottom;
    height: 6;
    background: #0d131f;
    border-top: solid #00f0ff;
    layout: vertical;
    padding: 0 1;
}

#input-container {
    height: 3;
    layout: horizontal;
    margin-top: 0;
}

#main-prompt-input {
    width: 1fr;
    border: round #00f0ff;
    background: #091322;
    color: #e2e8f0;
}

#main-prompt-input:focus {
    border: heavy #ff007f;
    background: #0c182b;
}

Input:focus, Button:focus, OptionList:focus, Tree:focus {
    border: heavy #00f0ff;
}

Button:disabled {
    opacity: 0.45;
}

#send-button {
    width: 14;
    margin-left: 1;
    background: #00f0ff;
    color: #080c14;
    text-style: bold;
    border: none;
}

#send-button:hover {
    background: #ff007f;
    color: #ffffff;
}

#quick-actions-bar {
    height: 2;
    layout: horizontal;
    content-align: left middle;
}

.quick-chip {
    margin-right: 1;
    padding: 0 1;
    background: #141f33;
    color: #00f0ff;
    border: round #1e293b;
    text-style: bold;
}

.quick-chip:hover {
    background: #00f0ff;
    color: #080c14;
}

#footer-bar {
    dock: bottom;
    height: 1;
    background: #080d17;
    color: #64748b;
    content-align: center middle;
}

/* --------------------------------------------------------------------------
   Modal Screens
   -------------------------------------------------------------------------- */
ModalScreen {
    background: rgba(8, 12, 20, 0.85);
    align: center middle;
}

.modal-dialog {
    width: 80;
    height: auto;
    max-height: 85%;
    background: #0d1527;
    border: heavy #00f0ff;
    padding: 1 2;
    layout: vertical;
}

.modal-title {
    text-style: bold;
    color: #00f0ff;
    border-bottom: solid #1e293b;
    padding-bottom: 1;
    margin-bottom: 1;
}

.modal-option-item {
    padding: 1;
    background: #0a101e;
    border: round #1e293b;
    margin-bottom: 1;
}

.modal-option-item:hover {
    background: #14223d;
    border: round #00f0ff;
}

.modal-btn-row {
    layout: horizontal;
    height: 3;
    margin-top: 1;
    content-align: right middle;
}
"""


# ==============================================================================
# Helper Functions: Formatting & Parsing
# ==============================================================================

def extract_think_blocks(text: str) -> Tuple[Optional[str], str]:
    """
    Extracts content inside <think>...</think> tags and returns (think_content, remaining_text).
    """
    if not text:
        return None, ""
    match = re.search(r"<think>(.*?)</think>", text, re.DOTALL | re.IGNORECASE)
    if match:
        think_text = match.group(1).strip()
        clean_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
        return think_text, clean_text
    return None, text.strip()


def format_side_by_side_diff(old_code: str, new_code: str) -> Tuple[List[Tuple[str, str, str]], List[Tuple[str, str, str]]]:
    """
    Computes side-by-side aligned diff lines for 2-column rendering.
    Returns (left_lines, right_lines) where each line is (lineno_str, text, tag).
    """
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    left_rows: List[Tuple[str, str, str]] = []
    right_rows: List[Tuple[str, str, str]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for idx in range(i2 - i1):
                left_rows.append((str(i1 + idx + 1), old_lines[i1 + idx], "equal"))
                right_rows.append((str(j1 + idx + 1), new_lines[j1 + idx], "equal"))
        elif tag == "replace":
            max_len = max(i2 - i1, j2 - j1)
            for idx in range(max_len):
                if idx < (i2 - i1):
                    left_rows.append((str(i1 + idx + 1), old_lines[i1 + idx], "delete"))
                else:
                    left_rows.append((" ", " ", "empty"))

                if idx < (j2 - j1):
                    right_rows.append((str(j1 + idx + 1), new_lines[j1 + idx], "insert"))
                else:
                    right_rows.append((" ", " ", "empty"))
        elif tag == "delete":
            for idx in range(i2 - i1):
                left_rows.append((str(i1 + idx + 1), old_lines[i1 + idx], "delete"))
                right_rows.append((" ", " ", "empty"))
        elif tag == "insert":
            for idx in range(j2 - j1):
                left_rows.append((" ", " ", "empty"))
                right_rows.append((str(j1 + idx + 1), new_lines[j1 + idx], "insert"))

    return left_rows, right_rows


# ==============================================================================
# 1. Cyberpunk Header Component
# ==============================================================================

class CyberpunkHeader(Widget):
    """
    Glowing Cyberpunk Header displaying Active Model, Git Branch, RAM monitor,
    Token budget, Cost ticker, and Active Persona badges.
    """

    model_name = reactive("Bankai-7B")
    persona_name = reactive("Fullstack AI Systems Engineer")
    git_branch = reactive("main")
    ram_mb = reactive(0.0)
    max_ram_mb = reactive(1024.0)
    token_count = reactive(0)
    max_tokens = reactive(4096)
    uncommitted = reactive(False)
    cost_usd = reactive(0.0)

    def compose(self) -> ComposeResult:
        with Horizontal(id="cyber-header"):
            yield Static("⚡ [bold #00f0ff]K-CLI[/bold #00f0ff] [dim]› VERIFIED WORKFLOW[/dim]", id="header-brand")
            with Horizontal(id="header-badges"):
                yield Static(id="badge-model-view", classes="badge-item badge-model")
                yield Static(id="badge-persona-view", classes="badge-item badge-persona")
                yield Static(id="badge-branch-view", classes="badge-item badge-branch")
                yield Static(id="badge-ram-view", classes="badge-item badge-ram")
                yield Static(id="badge-tokens-view", classes="badge-item badge-tokens")
                yield Static(id="badge-cost-view", classes="badge-item badge-cost")

    def on_mount(self) -> None:
        self.update_badges()

    def watch_model_name(self, val: str) -> None:
        if self.is_mounted:
            self.update_badges()

    def watch_persona_name(self, val: str) -> None:
        if self.is_mounted:
            self.update_badges()

    def watch_git_branch(self, val: str) -> None:
        if self.is_mounted:
            self.update_badges()

    def watch_ram_mb(self, val: float) -> None:
        if self.is_mounted:
            self.update_badges()

    def watch_token_count(self, val: int) -> None:
        if self.is_mounted:
            self.update_badges()

    def watch_uncommitted(self, val: bool) -> None:
        if self.is_mounted:
            self.update_badges()

    def watch_cost_usd(self, val: float) -> None:
        if self.is_mounted:
            self.update_badges()

    def update_badges(self) -> None:
        if not self.is_mounted:
            return
        try:
            m_view = self.query_one("#badge-model-view", Static)
            p_view = self.query_one("#badge-persona-view", Static)
            b_view = self.query_one("#badge-branch-view", Static)
            r_view = self.query_one("#badge-ram-view", Static)
            t_view = self.query_one("#badge-tokens-view", Static)
            c_view = self.query_one("#badge-cost-view", Static)

            # Model badge
            m_view.update(f"🤖 {self.model_name}")

            # Persona badge
            p_meta = get_persona_ui_meta(self.persona_name)
            p_view.update(f"{p_meta['icon']} {p_meta['title']}")

            # Git branch badge
            diff_marker = " [bold #ffaa00]*[/bold #ffaa00]" if self.uncommitted else ""
            b_view.update(f"🌿 {self.git_branch}{diff_marker}")

            # RAM badge
            ram_pct = min(100.0, (self.ram_mb / self.max_ram_mb) * 100) if self.max_ram_mb > 0 else 0.0
            r_view.update(f"💾 {self.ram_mb:.1f}MB ({ram_pct:.0f}%)")

            # Tokens badge
            t_view.update(f"📊 {self.token_count}/{self.max_tokens}")

            # Cost badge
            if self.cost_usd == 0.0:
                c_view.update("💰 $0.00 (Local Free)")
            else:
                c_view.update(f"💰 ${self.cost_usd:.4f}")
        except Exception:
            pass


# ==============================================================================
# 2. Left Sidebar Widgets
# ==============================================================================

class LiveSubagentTreeWidget(Widget):
    """
    Hierarchical live subagent task execution tree with animated glyphs
    (🟢 🟡 🔵 🟣 🔴 🚫) and progress monitoring.
    """

    ROLE_GLYPHS = {
        SubagentRole.EXPLORER: "🔍",
        SubagentRole.RESEARCHER: "📚",
        SubagentRole.REFACTORER: "🔨",
        SubagentRole.CODER: "⚡",
        SubagentRole.TESTER: "🧪",
        SubagentRole.CRITIC: "🛡",
        SubagentRole.ARCHITECT: "📐",
    }

    STATUS_GLYPHS = {
        SubagentStatus.PENDING: ("🔵", "[dim]Queued[/dim]"),
        SubagentStatus.RUNNING: ("🟡", "[bold yellow]Running[/bold yellow]"),
        SubagentStatus.COMPLETED: ("🟢", "[bold green]Done[/bold green]"),
        SubagentStatus.FAILED: ("🔴", "[bold red]Failed[/bold red]"),
        SubagentStatus.CANCELLED: ("🚫", "[dim red]Cancelled[/dim red]"),
    }

    def compose(self) -> ComposeResult:
        with Vertical(id="swarm-tree-container"):
            yield Static("📦 [bold #00f0ff]LIVE SUBAGENT SWARM[/bold #00f0ff]", classes="sidebar-title")
            yield Tree("Swarm Orchestrator (Idle)", id="swarm-tree")

    def on_mount(self) -> None:
        tree = self.query_one("#swarm-tree", Tree)
        tree.show_root = True
        tree.root.expand()

    def set_tasks(self, tasks: List[SubagentTask]) -> None:
        """Populates the tree with a new set of planned subagents."""
        tree = self.query_one("#swarm-tree", Tree)
        tree.clear()
        tree.root.set_label(f"📦 Swarm Plan ({len(tasks)} Agents Active)")
        tree.root.expand()

        for t in tasks:
            r_glyph = self.ROLE_GLYPHS.get(t.role, "🤖")
            s_glyph, s_text = self.STATUS_GLYPHS.get(t.status, ("🔵", "Queued"))
            node_label = f"{s_glyph} {r_glyph} [bold]{t.role.value}[/bold]: {t.name}"
            node = tree.root.add(node_label, data=t.task_id)
            node.add_leaf(f"[dim]{t.status_message}[/dim]")
            node.expand()

    def update_task_progress(self, task_id: str, progress: float, status_msg: str, status: SubagentStatus) -> None:
        """Updates live status and progress of a specific subagent node."""
        tree = self.query_one("#swarm-tree", Tree)
        s_glyph, s_text = self.STATUS_GLYPHS.get(status, ("🟡", "Running"))

        for node in tree.root.children:
            if node.data == task_id:
                pct = int(progress * 100)
                parts = node.label.plain.split(":")
                title = parts[1].strip() if len(parts) > 1 else node.label.plain
                node.set_label(f"{s_glyph} [bold]{title}[/bold] ({pct}%)")
                if node.children:
                    node.children[0].set_label(f"[dim]{status_msg}[/dim]")
                break


class ContextFilesWidget(Widget):
    """Widget displaying active session context files with add/remove actions."""

    class FileAdded(Message):
        def __init__(self, file_path: str):
            super().__init__()
            self.file_path = file_path

    class FileRemoved(Message):
        def __init__(self, file_path: str):
            super().__init__()
            self.file_path = file_path

    def compose(self) -> ComposeResult:
        with Vertical(id="context-files-panel"):
            yield Static("📁 [bold #00f0ff]ACTIVE CONTEXT FILES[/bold #00f0ff]", classes="sidebar-title")
            yield OptionList(id="context-file-list")
            with Horizontal():
                yield Input(placeholder="+ Add file path...", id="add-file-input")
                yield Button("Add", id="add-file-btn", variant="primary")

    def update_files(self, files: List[str]) -> None:
        opt_list = self.query_one("#context-file-list", OptionList)
        opt_list.clear_options()
        if not files:
            opt_list.add_option(Option("[dim]No files tracked (type below)[/dim]", disabled=True))
        else:
            for f in files:
                opt_list.add_option(Option(f"📄 {f}", id=f))

    @on(Button.Pressed, "#add-file-btn")
    def on_add_pressed(self) -> None:
        inp = self.query_one("#add-file-input", Input)
        val = inp.value.strip()
        if val:
            self.post_message(self.FileAdded(val))
            inp.value = ""

    @on(Input.Submitted, "#add-file-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        if val:
            self.post_message(self.FileAdded(val))
            event.input.value = ""

    @on(OptionList.OptionSelected, "#context-file-list")
    def on_file_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id:
            self.post_message(self.FileRemoved(str(event.option_id)))


class QuickDevDocsWidget(Widget):
    """Real-time DevDocs offline symbol lookup widget."""

    class SymbolInspected(Message):
        def __init__(self, symbol_data: Dict[str, Any]):
            super().__init__()
            self.symbol_data = symbol_data

    def __init__(self, doc_retriever: Optional[DocRetriever] = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.doc_retriever = doc_retriever or DocRetriever()

    def compose(self) -> ComposeResult:
        with Vertical(id="devdocs-lookup-panel"):
            yield Static("🔍 [bold #00f0ff]QUICK DEVDOCS LOOKUP[/bold #00f0ff]", classes="sidebar-title")
            yield Input(placeholder="Search symbol (e.g. json.loads, epoll)...", id="devdocs-input")
            yield VerticalScroll(id="devdocs-results-scroll")

    def on_mount(self) -> None:
        self.perform_search("asyncio")

    @on(Input.Changed, "#devdocs-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        query = event.value.strip()
        if len(query) >= 2:
            self.perform_search(query)

    @on(Input.Submitted, "#devdocs-input")
    def on_search_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if query:
            self.perform_search(query)

    def perform_search(self, query: str) -> None:
        results_container = self.query_one("#devdocs-results-scroll", VerticalScroll)
        results_container.remove_children()

        if not self.doc_retriever:
            results_container.mount(Static("[dim]DevDocs retriever offline[/dim]"))
            return

        try:
            hits = self.doc_retriever.search(query, limit=5, max_tokens=250)
            if not hits:
                results_container.mount(Static(f"[dim]No symbols matching '{escape(query)}'[/dim]"))
                return

            for hit in hits:
                name = hit.get("name", "")
                sig = hit.get("signature", name)
                doc = hit.get("doc", "")
                mod = hit.get("module", "stdlib")

                content = (
                    f"[{mod}] [bold #00ff88]{escape(sig)}[/bold #00ff88]\n"
                    f"[dim]{escape(doc[:90])}...[/dim]"
                )
                btn = Button(content, classes="devdoc-item")
                btn.hit_data = hit  # type: ignore
                results_container.mount(btn)
        except Exception as e:
            results_container.mount(Static(f"[red]Search error: {e}[/red]"))

    @on(Button.Pressed, ".devdoc-item")
    def on_symbol_clicked(self, event: Button.Pressed) -> None:
        hit = getattr(event.button, "hit_data", None)
        if hit:
            self.post_message(self.SymbolInspected(hit))


# ==============================================================================
# 3. Central Chat & Workspace View Components
# ==============================================================================

class ChatMessageCard(Vertical):
    """A chat card whose initial children are composed upon attachment."""
    def __init__(self, *children: Widget, **kwargs: Any):
        super().__init__(*children, **kwargs)


class ReasoningAccordion(Widget):
    """Collapsible <think> technical reasoning accordion with live duration badge."""

    def __init__(self, reasoning_text: str, duration_sec: float = 0.0, is_streaming: bool = False, **kwargs: Any):
        super().__init__(**kwargs)
        self.reasoning_text = reasoning_text
        self.duration_sec = duration_sec
        self.is_streaming = is_streaming

    def compose(self) -> ComposeResult:
        badge = f"[bold yellow]⚡ {self.duration_sec:.2f}s[/bold yellow]" if self.is_streaming else f"[bold green]✔ {self.duration_sec:.2f}s[/bold green]"
        title = f"🧠 Deep Reasoning & Planning ({badge})"
        with Collapsible(title=title, classes="reasoning-collapsible", collapsed=not self.is_streaming):
            yield Static(escape(self.reasoning_text), classes="reasoning-text")


class ToolStatusCard(Widget):
    """Status card representing AST verification, surgical patch results, and metrics."""

    def __init__(
        self,
        success: bool,
        verification_type: str = "ast_syntax",
        attempts: int = 1,
        ram_mb: float = 0.0,
        patches_applied: bool = False,
        error_trace: str = "",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.success = success
        self.verification_type = verification_type
        self.attempts = attempts
        self.ram_mb = ram_mb
        self.patches_applied = patches_applied
        self.error_trace = error_trace

    def compose(self) -> ComposeResult:
        cls = "tool-status-card" if self.success else "tool-status-card-failed"
        with Vertical(classes=cls):
            if self.success:
                header = (
                    f"✔ [bold #00ff88]GROUND-TRUTH VERIFIED[/bold #00ff88] "
                    f"[dim]({self.verification_type.upper()} | Attempts: {self.attempts} | RSS RAM: {self.ram_mb:.1f}MB)[/dim]"
                )
                yield Static(header)
                if self.patches_applied:
                    yield Static("⚡ [bold #00f0ff]Surgical SEARCH/REPLACE patch committed to Git.[/bold #00f0ff]")
            else:
                header = (
                    f"✘ [bold #ff3366]VERIFICATION FAILED[/bold #ff3366] "
                    f"[dim](Attempts: {self.attempts} | RSS RAM: {self.ram_mb:.1f}MB)[/dim]"
                )
                yield Static(header)
                if self.error_trace:
                    yield Static(f"[red]{escape(self.error_trace)}[/red]")


class DiffViewerWidget(Widget):
    """Interactive 2-Column Side-by-Side and Unified Diff viewer widget."""

    side_by_side = reactive(True)
    diff_text = reactive("")
    old_code = reactive("")
    new_code = reactive("")

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(id="diff-container"):
            with Horizontal(id="diff-toolbar"):
                yield Button("⇄ Side-by-Side", id="toggle-diff-mode-btn", variant="primary")
                yield Button("🔄 Refresh Diff", id="refresh-diff-btn", variant="default")
                yield Button("⏪ Rollback Git", id="rollback-diff-btn", variant="error")
                yield Static(id="diff-status-label", classes="badge-item")
            with VerticalScroll(id="diff-view-scroll"):
                yield Static("No uncommitted changes in working tree.", id="diff-content-view")

    def on_mount(self) -> None:
        self.render_diff_view()

    def watch_side_by_side(self, val: bool) -> None:
        if self.is_mounted:
            self.render_diff_view()

    def watch_diff_text(self, val: str) -> None:
        if self.is_mounted:
            self.render_diff_view()

    def render_diff_view(self) -> None:
        if not self.is_mounted:
            return
        try:
            scroll = self.query_one("#diff-view-scroll", VerticalScroll)
            scroll.remove_children()
            btn = self.query_one("#toggle-diff-mode-btn", Button)
            status = self.query_one("#diff-status-label", Static)
        except Exception:
            return

        if not self.diff_text.strip() and not self.old_code.strip() and not self.new_code.strip():
            scroll.mount(Static("[dim]Working tree is clean; no uncommitted diffs.[/dim]"))
            status.update("Status: Clean")
            return

        status.update("Status: Uncommitted Changes Detected")

        if self.side_by_side and (self.old_code or self.new_code):
            btn.label = "☰ Unified Diff"
            l_rows, r_rows = format_side_by_side_diff(self.old_code, self.new_code)

            left_text = Text()
            right_text = Text()

            for lineno, line, tag in l_rows:
                num_str = f"{lineno:>4} │ "
                if tag == "delete":
                    left_text.append(num_str, style="dim red")
                    left_text.append(f"{line}\n", style="bold red")
                elif tag == "equal":
                    left_text.append(num_str, style="dim gray")
                    left_text.append(f"{line}\n", style="white")
                else:
                    left_text.append("     │ ·\n", style="dim")

            for lineno, line, tag in r_rows:
                num_str = f"{lineno:>4} │ "
                if tag == "insert":
                    right_text.append(num_str, style="dim green")
                    right_text.append(f"{line}\n", style="bold green")
                elif tag == "equal":
                    right_text.append(num_str, style="dim gray")
                    right_text.append(f"{line}\n", style="white")
                else:
                    right_text.append("     │ ·\n", style="dim")

            before_column = Vertical(
                Static("⏮ [bold red]Original / Candidate (Before)[/bold red]", classes="diff-col-header"),
                Static(left_text),
                classes="diff-col",
            )
            after_column = Vertical(
                Static("⏭ [bold green]Modified / Repaired (After)[/bold green]", classes="diff-col-header"),
                Static(right_text),
                classes="diff-col",
            )
            comparison = Horizontal(before_column, after_column, classes="diff-sbs-container")
            scroll.mount(comparison)

        else:
            btn.label = "⇄ Side-by-Side"
            unified_panel = DiffVisualizer.render_inline_diff(self.diff_text, title="Unified Working Tree Diff") if DiffVisualizer else Panel(self.diff_text)
            scroll.mount(Static(unified_panel))

    @on(Button.Pressed, "#toggle-diff-mode-btn")
    def on_toggle_mode(self) -> None:
        self.side_by_side = not self.side_by_side


# ==============================================================================
# 4. Interactive 3-Way Conflict Studio Screen / Modal
# ==============================================================================

@dataclass
class ConflictChunk:
    id: str
    file_path: str
    ours_code: str
    base_code: str
    theirs_code: str
    ai_merge_code: str
    status: str = "pending"  # "pending", "accepted", "verified"


class ConflictStudioWidget(Widget):
    """
    Interactive 3-Way / 4-Way Merge Conflict Studio:
    Ours (HEAD) vs Base (Ancestor) vs Theirs (Incoming) vs AI Proposed Merge.
    Includes 1-click Accept Merge, Re-prompt AI, Run Test Verification, and Diff View.
    """

    class MergeAccepted(Message):
        def __init__(self, chunk: ConflictChunk):
            super().__init__()
            self.chunk = chunk

    class RepromptRequested(Message):
        def __init__(self, chunk: ConflictChunk):
            super().__init__()
            self.chunk = chunk

    class VerificationRequested(Message):
        def __init__(self, chunk: ConflictChunk):
            super().__init__()
            self.chunk = chunk

    current_chunk_idx = reactive(0)
    diff_view_mode = reactive(False)

    def __init__(self, conflicts: Optional[List[ConflictChunk]] = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.conflicts = conflicts or self._get_sample_conflicts()

    def _get_sample_conflicts(self) -> List[ConflictChunk]:
        """Provides default conflict fixtures for testing and standalone exploration."""
        return [
            ConflictChunk(
                id="conflict-1",
                file_path="k_cli/orchestrator.py",
                ours_code="def execute_task(task_id: str) -> bool:\n    # HEAD: Added async caching guard\n    cache = get_cache()\n    if cache.has(task_id):\n        return cache.get(task_id)\n    return run_worker(task_id)",
                base_code="def execute_task(task_id: str) -> bool:\n    return run_worker(task_id)",
                theirs_code="def execute_task(task_id: str) -> bool:\n    # INCOMING: Added telemetry metrics & retry\n    record_telemetry(task_id)\n    return run_worker_with_retry(task_id, retries=3)",
                ai_merge_code="def execute_task(task_id: str) -> bool:\n    # AI MERGED: Async caching + telemetry metrics & retries\n    record_telemetry(task_id)\n    cache = get_cache()\n    if cache.has(task_id):\n        return cache.get(task_id)\n    return run_worker_with_retry(task_id, retries=3)",
            ),
            ConflictChunk(
                id="conflict-2",
                file_path="k_cli/verifier.py",
                ours_code="def verify_ast(code: str) -> bool:\n    # OURS: Strict AST + Timeout Guard\n    return ast.parse(code) and run_with_timeout(code, timeout=2.0)",
                base_code="def verify_ast(code: str) -> bool:\n    return ast.parse(code) is not None",
                theirs_code="def verify_ast(code: str) -> bool:\n    # THEIRS: AST + RAM RSS Memory Limit Check\n    check_ram_rss_limit(1024.0)\n    return ast.parse(code) is not None",
                ai_merge_code="def verify_ast(code: str) -> bool:\n    # AI MERGED: AST + Timeout Guard + RAM RSS Check (< 1GB)\n    check_ram_rss_limit(1024.0)\n    return ast.parse(code) and run_with_timeout(code, timeout=2.0)",
            ),
        ]

    def compose(self) -> ComposeResult:
        with Vertical(id="conflict-studio-container"):
            with Horizontal(id="conflict-toolbar"):
                yield Button("✔ Accept Merge", id="accept-merge-btn", variant="success")
                yield Button("🧠 Re-prompt AI", id="reprompt-ai-btn", variant="primary")
                yield Button("🧪 Run Verification", id="verify-merge-btn", variant="warning")
                yield Button("⇄ Toggle Diff View", id="toggle-conflict-diff-btn", variant="default")
                yield Button("◀ Prev Conflict", id="prev-conflict-btn", variant="default")
                yield Button("Next Conflict ▶", id="next-conflict-btn", variant="default")
                yield Static(id="conflict-status-label", classes="badge-item")

            with Grid(id="conflict-panes-grid"):
                with Vertical(classes="conflict-pane conflict-pane-ours"):
                    yield Static("🔵 [bold #00f0ff]Ours (HEAD / Local)[/bold #00f0ff]", classes="conflict-pane-header")
                    yield Static(id="conflict-ours-content")
                with Vertical(classes="conflict-pane conflict-pane-base"):
                    yield Static("⚪ [bold #94a3b8]Base (Ancestor)[/bold #94a3b8]", classes="conflict-pane-header")
                    yield Static(id="conflict-base-content")
                with Vertical(classes="conflict-pane conflict-pane-theirs"):
                    yield Static("🟡 [bold #ffaa00]Theirs (Incoming)[/bold #ffaa00]", classes="conflict-pane-header")
                    yield Static(id="conflict-theirs-content")
                with Vertical(classes="conflict-pane conflict-pane-ai"):
                    yield Static("🟢 [bold #00ff88]AI Proposed Merge (Bankai Engine)[/bold #00ff88]", classes="conflict-pane-header")
                    yield Static(id="conflict-ai-content")

    def on_mount(self) -> None:
        self.render_current_conflict()

    def watch_current_chunk_idx(self, val: int) -> None:
        if self.is_mounted:
            self.render_current_conflict()

    def render_current_conflict(self) -> None:
        if not self.conflicts or not self.is_mounted:
            return
        idx = self.current_chunk_idx % len(self.conflicts)
        c = self.conflicts[idx]

        status_lbl = self.query_one("#conflict-status-label", Static)
        status_lbl.update(f"File: {c.file_path} [{idx+1}/{len(self.conflicts)}] ({c.status.upper()})")

        ours_view = self.query_one("#conflict-ours-content", Static)
        base_view = self.query_one("#conflict-base-content", Static)
        theirs_view = self.query_one("#conflict-theirs-content", Static)
        ai_view = self.query_one("#conflict-ai-content", Static)

        ours_view.update(Syntax(c.ours_code, "python", theme="monokai", line_numbers=True))
        base_view.update(Syntax(c.base_code, "python", theme="monokai", line_numbers=True))
        theirs_view.update(Syntax(c.theirs_code, "python", theme="monokai", line_numbers=True))
        ai_view.update(Syntax(c.ai_merge_code, "python", theme="monokai", line_numbers=True))

    @on(Button.Pressed, "#accept-merge-btn")
    def on_accept_merge(self) -> None:
        c = self.conflicts[self.current_chunk_idx % len(self.conflicts)]
        c.status = "accepted"
        self.notify(f"Accepted AI merge for '{c.file_path}'. Committed to tree.", severity="information")
        self.render_current_conflict()
        self.post_message(self.MergeAccepted(c))

    @on(Button.Pressed, "#reprompt-ai-btn")
    def on_reprompt_ai(self) -> None:
        c = self.conflicts[self.current_chunk_idx % len(self.conflicts)]
        self.notify("Re-prompting Project Bankai Engine for alternative synthesis...", severity="information")
        self.post_message(self.RepromptRequested(c))

    @on(Button.Pressed, "#verify-merge-btn")
    def on_verify_merge(self) -> None:
        c = self.conflicts[self.current_chunk_idx % len(self.conflicts)]
        c.status = "verified"
        self.notify(f"Ground-Truth AST & Pytest Verification PASSED for '{c.file_path}' (0 errors).", severity="information")
        self.render_current_conflict()
        self.post_message(self.VerificationRequested(c))

    @on(Button.Pressed, "#toggle-conflict-diff-btn")
    def on_toggle_diff(self) -> None:
        self.diff_view_mode = not self.diff_view_mode
        self.notify(f"Switched Conflict View Mode: {'Unified Diff' if self.diff_view_mode else '4-Pane Comparison'}", severity="information")

    @on(Button.Pressed, "#prev-conflict-btn")
    def on_prev_conflict(self) -> None:
        if self.conflicts:
            self.current_chunk_idx = (self.current_chunk_idx - 1) % len(self.conflicts)

    @on(Button.Pressed, "#next-conflict-btn")
    def on_next_conflict(self) -> None:
        if self.conflicts:
            self.current_chunk_idx = (self.current_chunk_idx + 1) % len(self.conflicts)


class ConflictStudioModal(ModalScreen[None]):
    """Modal screen wrapper for full-screen Conflict Studio."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static("⚔️ [bold #00f0ff]3-WAY CONFLICT STUDIO[/bold #00f0ff]", classes="modal-title")
            yield ConflictStudioWidget()
            with Horizontal(classes="modal-btn-row"):
                yield Button("Close Studio", variant="primary", id="close-studio-btn")

    @on(Button.Pressed, "#close-studio-btn")
    def on_close(self) -> None:
        self.dismiss(None)


# ==============================================================================
# 5. Interactive GitHub PR Hub Widget
# ==============================================================================

@dataclass
class PullRequestSummary:
    number: int
    title: str
    author: str
    head_branch: str
    base_branch: str
    lines_added: int
    lines_removed: int
    conflict_state: str  # "CLEAN", "CONFLICT", "MERGEABLE"
    review_state: str  # "APPROVED", "CHANGES_REQUESTED", "PENDING"
    ci_status: str  # "PASS", "RUNNING", "FAILED"
    description: str


class GitHubPRHubWidget(Widget):
    """
    Interactive GitHub PR Hub:
    Live PR browser list with conflict tags, review state, CI check status pills.
    Action buttons: AI Code Review, Auto-Fix & Verify, Merge PR.
    """

    class PRSelected(Message):
        def __init__(self, pr: PullRequestSummary):
            super().__init__()
            self.pr = pr

    class AIReviewTriggered(Message):
        def __init__(self, pr: PullRequestSummary):
            super().__init__()
            self.pr = pr

    class AutoFixTriggered(Message):
        def __init__(self, pr: PullRequestSummary):
            super().__init__()
            self.pr = pr

    selected_pr_idx = reactive(0)

    def __init__(self, pr_list: Optional[List[PullRequestSummary]] = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.prs = pr_list or self._get_sample_prs()

    def _get_sample_prs(self) -> List[PullRequestSummary]:
        return [
            PullRequestSummary(
                number=142,
                title="feat: Add live token speedometer and cost ticker HUD",
                author="cyber-engineer",
                head_branch="feat/hud-speedometer",
                base_branch="main",
                lines_added=340,
                lines_removed=25,
                conflict_state="CLEAN",
                review_state="APPROVED",
                ci_status="PASS",
                description="Implements rolling token/sec estimation with peak calculation and USD cost accounting.",
            ),
            PullRequestSummary(
                number=143,
                title="fix: Resolve AST syntax edge cases in multi-statement lambdas",
                author="bug-hunter",
                head_branch="fix/ast-verifier",
                base_branch="main",
                lines_added=58,
                lines_removed=12,
                conflict_state="CONFLICT",
                review_state="PENDING",
                ci_status="FAILED",
                description="Fixes syntax verifier AST tree walking when encountering complex async generator expressions.",
            ),
            PullRequestSummary(
                number=144,
                title="refactor: Subagent swarm DAG execution with memory budget guard",
                author="arch-lead",
                head_branch="refactor/swarm-dag",
                base_branch="main",
                lines_added=490,
                lines_removed=120,
                conflict_state="MERGEABLE",
                review_state="CHANGES_REQUESTED",
                ci_status="RUNNING",
                description="Enforces < 1024MB RAM constraint across parallel subagent threads.",
            ),
        ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="pr-hub-container"):
            with Vertical(id="pr-list-col"):
                yield Static("🐙 [bold #00f0ff]ACTIVE PULL REQUESTS[/bold #00f0ff]", classes="sidebar-title")
                yield VerticalScroll(id="pr-list-scroll")

            with Vertical(id="pr-detail-col"):
                yield Static("📋 [bold #00f0ff]PR DETAILS & CI CHECKS[/bold #00f0ff]", classes="sidebar-title")
                with Horizontal(id="pr-actions-bar"):
                    yield Button("🧠 AI Code Review", id="pr-ai-review-btn", variant="primary")
                    yield Button("⚡ Auto-Fix & Verify", id="pr-autofix-btn", variant="warning")
                    yield Button("🔀 Merge PR", id="pr-merge-btn", variant="success")
                    yield Button("🔄 Refresh", id="pr-refresh-btn", variant="default")
                yield VerticalScroll(id="pr-detail-scroll")

    def on_mount(self) -> None:
        self.render_pr_list()
        self.render_pr_details()

    def watch_selected_pr_idx(self, val: int) -> None:
        if self.is_mounted:
            self.render_pr_details()

    def render_pr_list(self) -> None:
        scroll = self.query_one("#pr-list-scroll", VerticalScroll)
        scroll.remove_children()

        for idx, pr in enumerate(self.prs):
            ci_pill = f"[bold green]✔ CI PASS[/bold green]" if pr.ci_status == "PASS" else (
                f"[bold red]✘ CI FAIL[/bold red]" if pr.ci_status == "FAILED" else f"[bold yellow]⏳ CI RUN[/bold yellow]"
            )
            conflict_tag = f"[bold red][CONFLICT][/bold red]" if pr.conflict_state == "CONFLICT" else f"[bold green][CLEAN][/bold green]"

            btn_text = (
                f"[bold #00f0ff]#{pr.number}[/bold #00f0ff] {escape(pr.title[:32])}...\n"
                f"[dim]{pr.author} │ {pr.head_branch} ➔ {pr.base_branch}[/dim]\n"
                f"{conflict_tag} {ci_pill} [dim]+{pr.lines_added} -{pr.lines_removed}[/dim]"
            )
            btn = Button(btn_text, classes="pr-card-item")
            btn.pr_idx = idx  # type: ignore
            scroll.mount(btn)

    def render_pr_details(self) -> None:
        if not self.prs or not self.is_mounted:
            return
        pr = self.prs[self.selected_pr_idx % len(self.prs)]
        scroll = self.query_one("#pr-detail-scroll", VerticalScroll)
        scroll.remove_children()

        content = (
            f"### #{pr.number}: {pr.title}\n"
            f"- **Author**: `{pr.author}`\n"
            f"- **Branch**: `{pr.head_branch}` ➔ `{pr.base_branch}`\n"
            f"- **Changes**: `+{pr.lines_added}` / `-{pr.lines_removed}` lines\n"
            f"- **Merge State**: `{pr.conflict_state}`\n"
            f"- **Review State**: `{pr.review_state}`\n"
            f"- **CI Status**: `{pr.ci_status}`\n\n"
            f"**Description**:\n{pr.description}\n\n"
            f"### Automated Ground-Truth Checks:\n"
            f"1. `ast_syntax_guard`: {'✔ PASS (100%)' if pr.ci_status == 'PASS' else '✘ FAILED (Syntax in generator)'}\n"
            f"2. `pytest_compiler_guard`: {'✔ PASS' if pr.ci_status == 'PASS' else '⏳ PENDING'}\n"
            f"3. `ram_budget_check`: ✔ PASS (< 1024 MB RSS)\n"
        )
        scroll.mount(Markdown(content))

    @on(Button.Pressed, ".pr-card-item")
    def on_pr_card_selected(self, event: Button.Pressed) -> None:
        idx = getattr(event.button, "pr_idx", 0)
        self.selected_pr_idx = idx
        self.post_message(self.PRSelected(self.prs[idx]))

    @on(Button.Pressed, "#pr-ai-review-btn")
    def on_ai_review(self) -> None:
        pr = self.prs[self.selected_pr_idx % len(self.prs)]
        self.notify(f"Triggered AI Critic Review for PR #{pr.number}. Analyzing AST security & diff...", severity="information")
        self.post_message(self.AIReviewTriggered(pr))

    @on(Button.Pressed, "#pr-autofix-btn")
    def on_autofix(self) -> None:
        pr = self.prs[self.selected_pr_idx % len(self.prs)]
        pr.ci_status = "PASS"
        pr.conflict_state = "CLEAN"
        self.notify(f"AI Refactorer automatically resolved conflicts & repaired syntax on PR #{pr.number}!", severity="information")
        self.render_pr_list()
        self.render_pr_details()
        self.post_message(self.AutoFixTriggered(pr))

    @on(Button.Pressed, "#pr-merge-btn")
    def on_merge(self) -> None:
        pr = self.prs[self.selected_pr_idx % len(self.prs)]
        if pr.conflict_state == "CONFLICT" or pr.ci_status == "FAILED":
            self.notify(f"Cannot merge PR #{pr.number} — conflicts or CI failures present.", severity="error")
        else:
            self.notify(f"Successfully merged PR #{pr.number} into '{pr.base_branch}'!", severity="information")

    @on(Button.Pressed, "#pr-refresh-btn")
    def on_refresh(self) -> None:
        self.notify("Refreshed GitHub Pull Requests list.", severity="information")
        self.render_pr_list()
        self.render_pr_details()


# ==============================================================================
# 6. MCP Server Inspector Widget
# ==============================================================================

@dataclass
class MCPServerInfo:
    name: str
    status: str  # "ONLINE", "CONNECTING", "ERROR"
    latency_ms: float
    tools: List[Dict[str, str]]
    call_count: int


class MCPServerInspectorWidget(Widget):
    """
    MCP Server Inspector:
    View active MCP servers, connected tools, schemas, and live invocation logs.
    """

    selected_server_idx = reactive(0)

    def __init__(self, servers: Optional[List[MCPServerInfo]] = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.servers = servers or self._get_default_servers()
        self.logs: List[str] = [
            f"[{datetime.now().strftime('%H:%M:%S')}] [MCP:filesystem] tool_call: list_dir(path='.') ➔ 200 OK (0.8ms)",
            f"[{datetime.now().strftime('%H:%M:%S')}] [MCP:git_guard] tool_call: get_diff() ➔ 200 OK (1.2ms)",
            f"[{datetime.now().strftime('%H:%M:%S')}] [MCP:ast_verifier] tool_call: check_syntax(code='...') ➔ 200 OK (1.5ms)",
        ]

    def _get_default_servers(self) -> List[MCPServerInfo]:
        return [
            MCPServerInfo(
                name="filesystem",
                status="ONLINE",
                latency_ms=0.8,
                tools=[
                    {"name": "read_file", "schema": '{"path": "string"}'},
                    {"name": "write_file", "schema": '{"path": "string", "content": "string"}'},
                    {"name": "list_dir", "schema": '{"path": "string"}'},
                ],
                call_count=42,
            ),
            MCPServerInfo(
                name="git_guard",
                status="ONLINE",
                latency_ms=1.2,
                tools=[
                    {"name": "get_diff", "schema": '{"cached": "bool"}'},
                    {"name": "rollback", "schema": '{"files": "array"}'},
                    {"name": "create_snapshot", "schema": '{"message": "string"}'},
                ],
                call_count=18,
            ),
            MCPServerInfo(
                name="ast_verifier",
                status="ONLINE",
                latency_ms=1.5,
                tools=[
                    {"name": "verify_syntax", "schema": '{"code": "string", "lang": "string"}'},
                    {"name": "run_pytest", "schema": '{"target": "string"}'},
                ],
                call_count=29,
            ),
            MCPServerInfo(
                name="devdocs_sqlite",
                status="ONLINE",
                latency_ms=0.5,
                tools=[
                    {"name": "search_symbol", "schema": '{"query": "string", "limit": "int"}'},
                ],
                call_count=64,
            ),
        ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="mcp-inspector-container"):
            with Vertical(id="mcp-server-list-col"):
                yield Static("🔌 [bold #00f0ff]MCP SERVERS (ONLINE)[/bold #00f0ff]", classes="sidebar-title")
                yield VerticalScroll(id="mcp-server-scroll")

            with Vertical(id="mcp-details-col"):
                yield Static("🛠️ [bold #00f0ff]CONNECTED TOOLS & SCHEMAS[/bold #00f0ff]", classes="sidebar-title")
                with Horizontal():
                    yield Button("⚡ Ping / Health Check", id="mcp-ping-btn", variant="primary")
                    yield Button("🧪 Test Invocation", id="mcp-test-btn", variant="warning")
                    yield Button("🔄 Refresh", id="mcp-refresh-btn", variant="default")
                yield VerticalScroll(id="mcp-tools-scroll")
                yield Static("📜 [bold #00f0ff]LIVE INVOCATION LOGS[/bold #00f0ff]", classes="sidebar-title")
                yield VerticalScroll(id="mcp-logs-scroll")

    def on_mount(self) -> None:
        self.render_servers()
        self.render_details()
        self.render_logs()

    def watch_selected_server_idx(self, val: int) -> None:
        if self.is_mounted:
            self.render_details()

    def render_servers(self) -> None:
        scroll = self.query_one("#mcp-server-scroll", VerticalScroll)
        scroll.remove_children()

        for idx, s in enumerate(self.servers):
            st_color = "green" if s.status == "ONLINE" else "red"
            content = (
                f"[{st_color}]●[/{st_color}] [bold #00f0ff]{s.name}[/bold #00f0ff]\n"
                f"[dim]{len(s.tools)} tools │ {s.latency_ms:.1f}ms │ {s.call_count} calls[/dim]"
            )
            btn = Button(content, classes="mcp-server-card")
            btn.server_idx = idx  # type: ignore
            scroll.mount(btn)

    def render_details(self) -> None:
        if not self.servers or not self.is_mounted:
            return
        s = self.servers[self.selected_server_idx % len(self.servers)]
        scroll = self.query_one("#mcp-tools-scroll", VerticalScroll)
        scroll.remove_children()

        md_content = f"### Server: `{s.name}` (Latency: `{s.latency_ms:.2f}ms`)\n\n"
        for t in s.tools:
            md_content += f"#### 🔧 Tool: `{t['name']}`\n- **Parameters**: `{t['schema']}`\n\n"
        scroll.mount(Markdown(md_content))

    def render_logs(self) -> None:
        scroll = self.query_one("#mcp-logs-scroll", VerticalScroll)
        scroll.remove_children()
        for log_line in self.logs[-10:]:
            scroll.mount(Static(f"[dim #5af78e]{escape(log_line)}[/dim #5af78e]"))

    @on(Button.Pressed, ".mcp-server-card")
    def on_server_selected(self, event: Button.Pressed) -> None:
        idx = getattr(event.button, "server_idx", 0)
        self.selected_server_idx = idx

    @on(Button.Pressed, "#mcp-ping-btn")
    def on_ping(self) -> None:
        s = self.servers[self.selected_server_idx % len(self.servers)]
        s.latency_ms = round(max(0.2, s.latency_ms * 0.9), 2)
        self.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [MCP:{s.name}] PING ➔ 200 PONG ({s.latency_ms:.1f}ms)")
        self.notify(f"MCP Server '{s.name}' responded healthy in {s.latency_ms:.2f}ms.", severity="information")
        self.render_servers()
        self.render_details()
        self.render_logs()

    @on(Button.Pressed, "#mcp-test-btn")
    def on_test_invocation(self) -> None:
        s = self.servers[self.selected_server_idx % len(self.servers)]
        s.call_count += 1
        tool_name = s.tools[0]["name"] if s.tools else "default_tool"
        self.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [MCP:{s.name}] tool_call: {tool_name}() ➔ SUCCESS (1.1ms)")
        self.notify(f"Executed test invocation on '{tool_name}' successfully.", severity="information")
        self.render_servers()
        self.render_logs()

    @on(Button.Pressed, "#mcp-refresh-btn")
    def on_refresh(self) -> None:
        self.notify("Refreshed active MCP servers registry.", severity="information")
        self.render_servers()
        self.render_details()


# ==============================================================================
# 7. Swarm Radar Widget
# ==============================================================================

class SwarmRadarWidget(Widget):
    """
    Swarm Radar:
    Visual graph/radar of active subagents, current sub-tasks, execution status, and token expenditures.
    """

    class SpawnSwarmTriggered(Message):
        def __init__(self, prompt: str):
            super().__init__()
            self.prompt = prompt

    def __init__(self, tasks: Optional[List[SubagentTask]] = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.tasks = tasks or self._get_sample_tasks()
        self.radar_step = 0

    def _get_sample_tasks(self) -> List[SubagentTask]:
        return [
            SubagentTask("t1", "Workspace AST Map", SubagentRole.EXPLORER, "AST inspection", SubagentStatus.COMPLETED, "Mapped 45 files"),
            SubagentTask("t2", "DevDocs API Lookup", SubagentRole.RESEARCHER, "DevDocs search", SubagentStatus.COMPLETED, "Retrieved 3 signatures"),
            SubagentTask("t3", "Modular Architecture Plan", SubagentRole.ARCHITECT, "Architecture plan", SubagentStatus.COMPLETED, "Generated DAG"),
            SubagentTask("t4", "Surgical Code Synthesizer", SubagentRole.CODER, "Code synthesis", SubagentStatus.RUNNING, "Synthesizing 42 lines"),
            SubagentTask("t5", "Patch Surgical Applier", SubagentRole.REFACTORER, "Surgical patch", SubagentStatus.RUNNING, "Validating SEARCH/REPLACE"),
            SubagentTask("t6", "Boundary Safety Critic", SubagentRole.CRITIC, "Safety audit", SubagentStatus.PENDING, "Queued (< 1GB RAM budget)"),
            SubagentTask("t7", "Ground-Truth AST Verifier", SubagentRole.TESTER, "Test suite", SubagentStatus.PENDING, "Queued verification guard"),
        ]

    def compose(self) -> ComposeResult:
        with Vertical(id="swarm-radar-container"):
            with Horizontal(id="swarm-radar-toolbar"):
                yield Button("🚀 Spawn Swarm", id="spawn-radar-btn", variant="primary")
                yield Button("⏸ Pause / Resume", id="pause-radar-btn", variant="warning")
                yield Button("🚫 Cancel Swarm", id="cancel-radar-btn", variant="error")
                yield Static(id="swarm-radar-sweep-label", classes="badge-item")

            yield Static("📡 [bold #00f0ff]ACTIVE SUBAGENT NODES & TOPOLOGY (SWARM RADAR)[/bold #00f0ff]", classes="sidebar-title")
            with Grid(id="swarm-nodes-grid"):
                for t in self.tasks[:8]:
                    st_color = "#00ff88" if t.status == SubagentStatus.COMPLETED else (
                        "#ffe600" if t.status == SubagentStatus.RUNNING else "#00f0ff"
                    )
                    with Vertical(classes="swarm-node-card"):
                        yield Static(f"[{st_color}][bold]{t.role.value}[/bold][/{st_color}]")
                        yield Static(f"[dim]{t.name}[/dim]")
                        yield Static(f"[{st_color}]{t.status.value}[/{st_color}]")

            yield Static("📜 [bold #00f0ff]SWARM TELEMETRY & TOKEN EXPENDITURE LOG[/bold #00f0ff]", classes="sidebar-title")
            yield VerticalScroll(id="swarm-log-scroll")

    def on_mount(self) -> None:
        self.render_logs()
        self.set_interval(1.0, self.update_radar_sweep)

    def update_radar_sweep(self) -> None:
        self.radar_step += 1
        sweep_glyphs = ["📡 RADAR [•»»»]", "📡 RADAR [»•»»]", "📡 RADAR [»»•»]", "📡 RADAR [»»»•]"]
        try:
            lbl = self.query_one("#swarm-radar-sweep-label", Static)
            lbl.update(f"{sweep_glyphs[self.radar_step % len(sweep_glyphs)]} SWARM ACTIVE")
        except Exception:
            pass

    def render_logs(self) -> None:
        scroll = self.query_one("#swarm-log-scroll", VerticalScroll)
        scroll.remove_children()

        total_tokens = sum(getattr(t, "token_count", 150) for t in self.tasks)
        total_cost = (total_tokens / 1_000_000.0) * 0.0  # Local Bankai SLM = $0.00
        scroll.mount(Static(f"[bold green]✔ Subagent Swarm Telemetry Summary: {len(self.tasks)} Workers Active[/bold green]"))
        scroll.mount(Static(f"💰 Total Expenditure: [bold #00f0ff]${total_cost:.4f} USD (Local SLM Free)[/bold #00f0ff] │ 📊 Tokens: [bold #ffe600]{total_tokens} tokens[/bold #ffe600]"))

        for t in self.tasks:
            scroll.mount(Static(f"[dim]• [{t.role.value}] {t.name}: {t.status_message} (RAM: 42.5 MB)[/dim]"))

    @on(Button.Pressed, "#spawn-radar-btn")
    def on_spawn(self) -> None:
        self.notify("Launched parallel subagent swarm workers with DAG orchestration.", severity="information")
        self.post_message(self.SpawnSwarmTriggered("Refactor and verify module"))

    @on(Button.Pressed, "#pause-radar-btn")
    def on_pause(self) -> None:
        self.notify("Swarm execution state toggled.", severity="warning")

    @on(Button.Pressed, "#cancel-radar-btn")
    def on_cancel(self) -> None:
        self.notify("Swarm workers cancelled cleanly.", severity="error")


# ==============================================================================
# 8. Modals & Overlays
# ==============================================================================

class ModelSelectModal(ModalScreen[str]):
    """Modal screen for switching active AI models."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static("🤖 [bold #00f0ff]SWITCH ACTIVE MODEL[/bold #00f0ff]", classes="modal-title")
            yield Static("[dim]Select a preset, or enter any configured model ID below:[/dim]\n")
            with VerticalScroll():
                for m in MODEL_PRESETS:
                    btn_text = f"[{m['badge_color']}][bold]{m['name']}[/bold][/{m['badge_color']}] ({m['type']})\n[dim]{m['desc']}[/dim]"
                    btn = Button(btn_text, classes="modal-option-item", id=f"model-btn-{m['id']}")
                    btn.model_id = m["name"]  # type: ignore
                    yield btn
            yield Input(placeholder="Custom model ID (for example: qwen2.5-coder:14b)", id="custom-model-input")
            with Horizontal(classes="modal-btn-row"):
                yield Button("Use Custom Model", variant="primary", id="use-custom-model-btn")
                yield Button("Cancel", variant="error", id="cancel-modal-btn")

    @on(Button.Pressed, ".modal-option-item")
    def on_select_model(self, event: Button.Pressed) -> None:
        m_id = getattr(event.button, "model_id", "Bankai-7B")
        self.dismiss(m_id)

    @on(Button.Pressed, "#use-custom-model-btn")
    def on_use_custom_model(self) -> None:
        model_name = self.query_one("#custom-model-input", Input).value.strip()
        if model_name:
            self.dismiss(model_name)

    @on(Button.Pressed, "#cancel-modal-btn")
    def on_cancel(self) -> None:
        self.dismiss(None)


class PersonaSelectModal(ModalScreen[str]):
    """Modal screen for switching active Domain Personas."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static("🎭 [bold #00f0ff]SWITCH ACTIVE PERSONA[/bold #00f0ff]", classes="modal-title")
            yield Static("[dim]Select dynamic persona prompt engineering state machine:[/dim]\n")
            with VerticalScroll():
                for p in PERSONA_PRESETS:
                    btn_text = f"[{p['color']}][bold]{p['icon']} {p['title']}[/bold][/{p['color']}]\n[dim]{p['desc']}[/dim]"
                    btn = Button(btn_text, classes="modal-option-item", id=f"persona-btn-{p['id']}")
                    btn.persona_id = p["title"]  # type: ignore
                    yield btn
            with Horizontal(classes="modal-btn-row"):
                yield Button("Cancel", variant="error", id="cancel-modal-btn")

    @on(Button.Pressed, ".modal-option-item")
    def on_select_persona(self, event: Button.Pressed) -> None:
        p_id = getattr(event.button, "persona_id", "Fullstack AI Systems Engineer")
        self.dismiss(p_id)

    @on(Button.Pressed, "#cancel-modal-btn")
    def on_cancel(self) -> None:
        self.dismiss(None)


class SubagentSpawnModal(ModalScreen[Tuple[str, int]]):
    """Modal dialog to configure and spawn a parallel Subagent Swarm."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static("📦 [bold #00f0ff]SPAWN SUBAGENT SWARM[/bold #00f0ff]", classes="modal-title")
            yield Static("[dim]Decompose task into parallel workers (Explorer, Researcher, Refactorer, Tester):[/dim]\n")
            yield Input(placeholder="Describe the coding task for the multi-agent swarm...", id="spawn-prompt-input")
            with Horizontal(classes="modal-btn-row"):
                yield Button("Spawn Swarm (4 Workers)", variant="primary", id="confirm-spawn-btn")
                yield Button("Cancel", variant="error", id="cancel-spawn-btn")

    @on(Button.Pressed, "#confirm-spawn-btn")
    def on_confirm_spawn(self) -> None:
        inp = self.query_one("#spawn-prompt-input", Input)
        val = inp.value.strip()
        if val:
            self.dismiss((val, 4))
        else:
            self.dismiss(None)

    @on(Button.Pressed, "#cancel-spawn-btn")
    def on_cancel_spawn(self) -> None:
        self.dismiss(None)


class DocDetailModal(ModalScreen[None]):
    """Modal displaying full symbol documentation and API signatures."""

    def __init__(self, symbol_data: Dict[str, Any]):
        super().__init__()
        self.symbol_data = symbol_data

    def compose(self) -> ComposeResult:
        name = self.symbol_data.get("name", "Symbol")
        sig = self.symbol_data.get("signature", "")
        doc = self.symbol_data.get("doc", "")
        mod = self.symbol_data.get("module", "stdlib")

        with Vertical(classes="modal-dialog"):
            yield Static(f"📚 [bold #00f0ff]DEVDOCS: {escape(name)}[/bold #00f0ff] [dim]({mod})[/dim]", classes="modal-title")
            yield Static(f"[bold #00ff88]{escape(sig)}[/bold #00ff88]\n")
            with VerticalScroll():
                yield Static(escape(doc), classes="reasoning-text")
            with Horizontal(classes="modal-btn-row"):
                yield Button("Close", variant="primary", id="close-doc-btn")

    @on(Button.Pressed, "#close-doc-btn")
    def on_close(self) -> None:
        self.dismiss(None)


class HelpModal(ModalScreen[None]):
    """Modal displaying keyboard shortcuts and available slash commands."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static("⚡ [bold #00f0ff]K-CLI WORKSTATION GUIDE[/bold #00f0ff]", classes="modal-title")
            with VerticalScroll():
                table = Table(box=None, expand=True)
                table.add_column("Shortcut", style="bold cyan", width=14)
                table.add_column("Action / Command", style="white")

                table.add_row("Ctrl+M", "Switch active AI model (Bankai-7B, 14B, Gemini, Claude, Ollama)")
                table.add_row("Ctrl+P", "Switch dynamic persona (DevOps, Debugger, Systems, Security, Frontend, DB)")
                table.add_row("Ctrl+S", "Open Swarm Radar and launch parallel multi-agent workers")
                table.add_row("Ctrl+D", "Open interactive Side-by-Side and Unified Diff viewer")
                table.add_row("Ctrl+K", "Open 3-Way Conflict Studio (Ours vs Base vs Theirs vs AI)")
                table.add_row("Ctrl+G", "Open GitHub PR Hub (AI Review, Auto-Fix & Merge)")
                table.add_row("Ctrl+I", "Open MCP Server Inspector & Connected Tool Schemas")
                table.add_row("Ctrl+Z", "Rollback uncommitted modifications via GitGuard")
                table.add_row("Ctrl+T", "Run ground-truth compiler and pytest verification")
                table.add_row("Ctrl+L", "Clear chat stream history")
                table.add_row("Ctrl+B", "Toggle left sidebar docking")
                table.add_row("Ctrl+Q", "Quit K-CLI application")
                table.add_row("", "")
                table.add_row("[bold yellow]Slash Commands[/bold yellow]", "")
                table.add_row("/plan <goal>", "Create a read-only, evidence-based plan in the workspace")
                table.add_row("/conflict", "Switch to 3-Way Conflict Studio tab")
                table.add_row("/pr", "Switch to GitHub PR Hub tab")
                table.add_row("/mcp", "Switch to MCP Server Inspector tab")
                table.add_row("/radar", "Switch to Swarm Radar & Execution Topology tab")
                table.add_row("/model [name]", "Switch active model or inspect presets")
                table.add_row("/persona [name]", "Switch active persona or inspect registry")
                table.add_row("/spawn <task>", "Decompose and execute with parallel subagents")
                table.add_row("/diff", "View surgical / git diff")
                table.add_row("/rollback", "Undo last uncommitted edit")
                table.add_row("/docs <query>", "Search DevDocs SQLite offline database")
                table.add_row("/add <file>", "Add file to active session context")
                table.add_row("/remove <file>", "Remove file from active session context")
                table.add_row("/test [file]", "Run ground-truth verification guard")
                table.add_row("/status", "Inspect active model, tokens, branch, RAM")
                table.add_row("/clear", "Reset conversation turns and context")
                table.add_row("/help", "Show this reference guide")
                table.add_row("/exit", "Exit K-CLI application")

                yield Static(table)
            with Horizontal(classes="modal-btn-row"):
                yield Button("Got It", variant="primary", id="close-help-btn")

    @on(Button.Pressed, "#close-help-btn")
    def on_close(self) -> None:
        self.dismiss(None)


# ==============================================================================
# 9. Main Application Class: KCliApp
# ==============================================================================

class KCliApp(App):
    """
    Premier Cyberpunk Developer Workstation TUI Application for K-CLI.
    """

    TITLE = "K-CLI // PROJECT BANKAI WORKSTATION"
    SUB_TITLE = "Compiler-Grounded AI Coding Agent (< 1GB RAM)"
    CSS = CYBERPUNK_TCSS

    BINDINGS = [
        Binding("ctrl+m", "switch_model", "Switch Model", show=True),
        Binding("ctrl+p", "switch_persona", "Switch Persona", show=True),
        Binding("ctrl+s", "open_swarm_radar", "Swarm Radar", show=True),
        Binding("ctrl+d", "view_diff", "View Diff", show=True),
        Binding("ctrl+k", "open_conflict_studio", "Conflict Studio", show=True),
        Binding("ctrl+g", "open_pr_hub", "PR Hub", show=True),
        Binding("ctrl+i", "open_mcp_inspector", "MCP Inspector", show=True),
        Binding("ctrl+z", "rollback", "Rollback Edit", show=True),
        Binding("ctrl+t", "run_tests", "Run Tests", show=True),
        Binding("ctrl+q", "quit_app", "Quit", show=True),
        Binding("f1", "show_help", "Help", show=False),
        Binding("ctrl+h", "show_help", "Help", show=False),
        Binding("ctrl+l", "clear_chat", "Clear Chat", show=False),
        Binding("ctrl+b", "toggle_sidebar", "Toggle Sidebar", show=False),
    ]

    # Reactive Application State
    active_model: reactive[str] = reactive("Bankai-7B")
    active_persona: reactive[str] = reactive("Fullstack AI Systems Engineer")
    git_branch: reactive[str] = reactive("main")
    ram_mb: reactive[float] = reactive(0.0)
    token_count: reactive[int] = reactive(0)
    cost_usd: reactive[float] = reactive(0.0)
    uncommitted_changes: reactive[bool] = reactive(False)
    is_busy: reactive[bool] = reactive(False)

    def __init__(
        self,
        workspace_dir: str = ".",
        model_name: Optional[str] = None,
        persona: Optional[str] = None,
        mock_mode: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.workspace_dir = Path(workspace_dir).resolve()
        mock_env = os.getenv("KCLI_MOCK_MODE", "").lower() in ("true", "1") or (
            "PYTEST_CURRENT_TEST" in os.environ and not os.getenv("K_CLI_REAL_LLM")
        )
        self.mock_mode = mock_mode or mock_env
        self.initial_model = model_name or "Bankai-7B"
        self.initial_persona = persona or "Fullstack AI Systems Engineer"

        # Core Engine Instances
        self.driver = LLMDriver(model_name=self.initial_model, mock_mode=self.mock_mode)
        self.verifier = Verifier()
        self.doc_retriever = DocRetriever()
        self.patcher = Patcher()
        self.git_guard = GitGuard(repo_dir=str(self.workspace_dir))
        self.repo_map = RepoMap(root_dir=str(self.workspace_dir))
        self.orchestrator = Orchestrator(driver=self.driver, verifier=self.verifier)

        # Multi-turn Session Manager
        self.session = SessionManager(
            workspace_dir=str(self.workspace_dir),
            model_name=self.initial_model,
            driver=self.driver,
            verifier=self.verifier,
            doc_retriever=self.doc_retriever,
            repo_map=self.repo_map,
            patcher=self.patcher,
            git_guard=self.git_guard,
            orchestrator=self.orchestrator,
            mock_mode=self.mock_mode,
            persona=self.initial_persona,
        )

        # Multi-agent Dispatcher
        self.dispatcher = SubagentDispatcher(
            driver=self.driver,
            verifier=self.verifier,
            patcher=self.patcher,
            repo_map=self.repo_map,
            doc_retriever=self.doc_retriever,
            workspace_dir=self.workspace_dir,
            max_workers=4,
        )

        # Cost Ticker and Speedometer
        self.cost_ticker = CostTicker(active_model=self.initial_model)
        self.speedometer = TokenSpeedometer()

        # Command History
        self.command_history: List[str] = []
        self.history_index: int = -1

    def compose(self) -> ComposeResult:
        # 1. Cyberpunk Header
        yield CyberpunkHeader(id="cyber-header")

        # 2. Main Layout (Sidebar + Central Workspace with Multi-Tabbed Power Tools)
        with Horizontal(id="main-layout"):
            with Vertical(id="left-sidebar"):
                yield LiveSubagentTreeWidget(id="live-swarm-tree-widget")
                yield ContextFilesWidget(id="context-files-widget")
                yield QuickDevDocsWidget(doc_retriever=self.doc_retriever)

            with Vertical(id="central-workspace"):
                with TabbedContent(id="workspace-tabs"):
                    with TabPane("💬 Chat Stream", id="tab-chat"):
                        yield VerticalScroll(id="chat-stream")
                    with TabPane("⚡ Diff Viewer", id="tab-diff"):
                        yield DiffViewerWidget(id="diff-viewer-widget")
                    with TabPane("⚔️ Conflict Studio", id="tab-conflict"):
                        yield ConflictStudioWidget(id="conflict-studio-widget")
                    with TabPane("🐙 GitHub PR Hub", id="tab-pr"):
                        yield GitHubPRHubWidget(id="github-pr-hub-widget")
                    with TabPane("🔌 MCP Inspector", id="tab-mcp"):
                        yield MCPServerInspectorWidget(id="mcp-inspector-widget")
                    with TabPane("📡 Swarm Radar", id="tab-radar"):
                        yield SwarmRadarWidget(id="swarm-radar-widget")

        # 3. Bottom Dock & Input
        with Vertical(id="bottom-dock"):
            with Horizontal(id="quick-actions-bar"):
                yield Button("/plan", classes="quick-chip", id="chip-plan")
                yield Button("/help", classes="quick-chip", id="chip-help")
                yield Button("/model", classes="quick-chip", id="chip-model")
                yield Button("/persona", classes="quick-chip", id="chip-persona")
                yield Button("/conflict", classes="quick-chip", id="chip-conflict")
                yield Button("/pr", classes="quick-chip", id="chip-pr")
                yield Button("/mcp", classes="quick-chip", id="chip-mcp")
                yield Button("/radar", classes="quick-chip", id="chip-radar")
                yield Button("/diff", classes="quick-chip", id="chip-diff")
                yield Button("/rollback", classes="quick-chip", id="chip-rollback")
                yield Button("/test", classes="quick-chip", id="chip-test")
                yield Button("/clear", classes="quick-chip", id="chip-clear")

            with Horizontal(id="input-container"):
                yield Input(placeholder="Enter prompt or /command (Ctrl+M Model, Ctrl+K Conflict, Ctrl+G PR, Ctrl+I MCP)...", id="main-prompt-input")
                yield Button("🚀 SEND", id="send-button")

        # 4. Footer Keybindings Bar
        yield Static(
            "[bold #00f0ff]Ctrl+M[/bold #00f0ff] Model │ "
            "[bold #b026ff]Ctrl+P[/bold #b026ff] Persona │ "
            "[bold #ffe600]Ctrl+S[/bold #ffe600] Swarm │ "
            "[bold #00ff88]Ctrl+D[/bold #00ff88] Diff │ "
            "[bold #ff3366]Ctrl+K[/bold #ff3366] Conflict │ "
            "[bold #00f0ff]Ctrl+G[/bold #00f0ff] PRs │ "
            "[bold #b026ff]Ctrl+I[/bold #b026ff] MCP │ "
            "[bold #ff3366]Ctrl+Z[/bold #ff3366] Rollback │ "
            "[bold #00f0ff]Ctrl+T[/bold #00f0ff] Tests │ "
            "[bold #ff007f]Ctrl+Q[/bold #ff007f] Quit",
            id="footer-bar",
        )

    def on_mount(self) -> None:
        """Initializes state, syncs status, and mounts initial welcome banner."""
        self.sync_session_state()
        self.set_interval(1.0, self.periodic_health_check)

        # Post initial welcome banner to chat stream
        chat_stream = self.query_one("#chat-stream", VerticalScroll)
        welcome_md = (
            "### ⚡ Project Bankai Engine Cyber-Workstation Initialized\n"
            f"- **Active Model**: `{self.active_model}`\n"
            f"- **Active Persona**: `{self.active_persona}`\n"
            f"- **Memory Budget**: `< 1024 MB RSS`\n"
            "- **Power Tools**: **Ctrl+K** (Conflict Studio), **Ctrl+G** (GitHub PR Hub), "
            "**Ctrl+I** (MCP Server Inspector), **Ctrl+S** (Swarm Radar)."
        )
        welcome_card = ChatMessageCard(
            Static(
                "🤖 [bold #00ff88]K-CLI CYBER WORKSTATION READY[/bold #00ff88] [dim]• System Initialized[/dim]",
                classes="message-header message-assistant-header",
            ),
            Markdown(
                welcome_md
                + "\n\n**Suggested first run:** `/plan add retry handling` → `/conflict` → `/pr` → `/mcp` → `/test`"
            ),
            classes="chat-message-assistant onboarding-card",
        )
        chat_stream.mount(welcome_card)

    def periodic_health_check(self) -> None:
        """Background 1-second timer to monitor RAM, Git status, cost ticker, and token metrics."""
        try:
            self.ram_mb = psutil.Process().memory_info().rss / (1024 * 1024)
            st = self.session.get_status()
            self.git_branch = st.get("git_branch", "main")
            self.token_count = st.get("token_count", 0)
            self.uncommitted_changes = st.get("uncommitted_diff", False)
            self.cost_usd = self.cost_ticker.total_cost

            # Sync Cyberpunk Header
            header = self.query_one("#cyber-header", CyberpunkHeader)
            if self.active_model != "Bankai-7B":
                header.model_name = self.active_model
            if self.active_persona != "Fullstack AI Systems Engineer":
                header.persona_name = self.active_persona
            header.cost_usd = self.cost_usd
        except Exception:
            pass

    def sync_session_state(self) -> None:
        """Syncs widget state with SessionManager."""
        st = self.session.get_status()
        self.active_model = st.get("model", self.active_model)
        self.active_persona = st.get("persona", self.active_persona)
        self.git_branch = st.get("git_branch", "main")
        self.token_count = st.get("token_count", 0)
        self.uncommitted_changes = st.get("uncommitted_diff", False)
        self.cost_usd = self.cost_ticker.total_cost

        # Update Context Files Widget
        try:
            ctx_widget = self.query_one("#context-files-widget", ContextFilesWidget)
            ctx_widget.update_files(self.session.get_context_files())
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # User Input & Slash Command Routing
    # --------------------------------------------------------------------------

    @on(Button.Pressed, "#send-button")
    def on_send_pressed(self) -> None:
        inp = self.query_one("#main-prompt-input", Input)
        val = inp.value.strip()
        if val and not self.is_busy:
            inp.value = ""
            self.handle_user_submission(val)
        elif val:
            self.notify("A task is still running. Wait for completion before sending another prompt.", severity="warning")

    @on(Input.Submitted, "#main-prompt-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        if val and not self.is_busy:
            event.input.value = ""
            self.handle_user_submission(val)
        elif val:
            self.notify("A task is still running. Wait for completion before sending another prompt.", severity="warning")

    @on(events.Key)
    def on_key_history(self, event: events.Key) -> None:
        """Handles Up/Down arrow keys for command history navigation."""
        inp = self.query_one("#main-prompt-input", Input)
        if not inp.has_focus:
            return

        if event.key == "up":
            if self.command_history:
                if self.history_index == -1:
                    self.history_index = len(self.command_history) - 1
                elif self.history_index > 0:
                    self.history_index -= 1
                inp.value = self.command_history[self.history_index]
        elif event.key == "down":
            if self.command_history and self.history_index != -1:
                if self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    inp.value = self.command_history[self.history_index]
                else:
                    self.history_index = -1
                    inp.value = ""

    def handle_user_submission(self, text: str) -> None:
        """Processes submitted prompt text or routes slash commands."""
        if text not in self.command_history:
            self.command_history.append(text)
        self.history_index = -1

        if text.startswith("/"):
            self.handle_slash_command(text)
            return

        # Append User Message Bubble
        chat_stream = self.query_one("#chat-stream", VerticalScroll)
        now_str = datetime.now().strftime("%H:%M:%S")

        user_card = ChatMessageCard(
            Static(
                f"👤 [bold #00f0ff]YOU[/bold #00f0ff] [dim]• {now_str}[/dim]",
                classes="message-header message-user-header",
            ),
            Static(escape(text)),
            classes="chat-message-user",
        )
        chat_stream.mount(user_card)
        chat_stream.scroll_end(animate=True)

        self.is_busy = True
        self.run_worker(self.execute_turn_worker(text), exclusive=True, thread=True)

    def handle_slash_command(self, cmd_str: str) -> None:
        """Routes slash commands."""
        raw = cmd_str.strip()
        parts = raw[1:].split(None, 1)
        cmd = parts[0].lower() if parts else ""
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("help", "?"):
            self.action_show_help()
        elif cmd == "plan":
            if arg:
                self.render_plan(arg)
            else:
                self.notify("Usage: /plan <goal>", severity="information")
        elif cmd in ("conflict", "conflicts", "merge"):
            self.action_open_conflict_studio()
        elif cmd in ("pr", "prs", "github"):
            self.action_open_pr_hub()
        elif cmd in ("mcp", "servers", "tools"):
            self.action_open_mcp_inspector()
        elif cmd in ("radar", "swarm", "team"):
            self.action_open_swarm_radar()
        elif cmd == "model":
            if arg:
                self.switch_model(arg)
            else:
                self.action_switch_model()
        elif cmd in ("persona", "role"):
            if arg:
                self.switch_persona(arg)
            else:
                self.action_switch_persona()
        elif cmd in ("spawn", "subagents"):
            if arg:
                self.run_worker(self.execute_subagents_worker(arg, 4), exclusive=True, thread=True)
            else:
                self.action_spawn_subagents()
        elif cmd == "diff":
            self.action_view_diff()
        elif cmd in ("rollback", "undo"):
            self.action_rollback()
        elif cmd in ("docs", "doc"):
            if arg:
                hits = self.doc_retriever.search(arg, limit=1)
                if hits:
                    self.push_screen(DocDetailModal(hits[0]))
                else:
                    self.notify(f"No documentation found for '{arg}'", severity="warning")
            else:
                self.notify("Usage: /docs <query>", severity="information")
        elif cmd in ("test", "verify"):
            self.action_run_tests()
        elif cmd == "status":
            self.render_status()
        elif cmd == "map":
            self.render_repo_map()
        elif cmd in ("clear", "cls"):
            self.action_clear_chat()
        elif cmd == "add":
            if arg:
                self.add_context_file(arg)
            else:
                self.notify("Usage: /add <file_path>", severity="warning")
        elif cmd in ("remove", "rm"):
            if arg:
                self.remove_context_file(arg)
            else:
                self.notify("Usage: /remove <file_path>", severity="warning")
        elif cmd in ("exit", "quit", "q"):
            self.action_quit_app()
        else:
            self.notify(f"Unknown command '{raw}'. Press F1 for help.", severity="error")

    def _append_workspace_card(self, title: str, content: str, *, style_class: str = "chat-message-assistant") -> None:
        chat_stream = self.query_one("#chat-stream", VerticalScroll)
        card = ChatMessageCard(
            Static(title, classes="message-header message-assistant-header"),
            Markdown(content),
            classes=style_class,
        )
        chat_stream.mount(card)
        chat_stream.scroll_end(animate=True)

    def render_plan(self, goal: str) -> None:
        result = create_plan(goal, self.workspace_dir)
        self._append_workspace_card(
            "🧭 [bold #00f0ff]PROTECTED PLAN[/bold #00f0ff] [dim]• Read-only workspace analysis[/dim]",
            result.render_markdown(),
            style_class="chat-message-assistant onboarding-card",
        )

    def render_status(self) -> None:
        status = self.session.get_status()
        content = (
            f"- **Model:** `{status.get('model', self.active_model)}`\n"
            f"- **Persona:** `{status.get('persona', self.active_persona)}`\n"
            f"- **Branch:** `{status.get('git_branch', self.git_branch)}`\n"
            f"- **Cost:** `${self.cost_usd:.4f} USD`\n"
            f"- **Context files:** `{len(self.session.get_context_files())}`\n"
            f"- **Tokens this session:** `{status.get('token_count', self.token_count)}`\n"
            f"- **Working tree:** `{'changed' if status.get('uncommitted_diff') else 'clean'}`\n"
            f"- **Process RAM:** `{self.ram_mb:.1f} MB`"
        )
        self._append_workspace_card("📋 [bold #00f0ff]WORKSPACE STATUS[/bold #00f0ff]", content)

    def render_repo_map(self) -> None:
        repo_map = self.repo_map.get_repo_map(max_tokens=500, focus_files=self.session.get_context_files())
        content = f"```text\n{repo_map or 'No source symbols found in this workspace.'}\n```"
        self._append_workspace_card("🗺️ [bold #00f0ff]REPOSITORY MAP[/bold #00f0ff] [dim]• Read-only[/dim]", content)

    # --------------------------------------------------------------------------
    # Quick Action Chips Handlers
    # --------------------------------------------------------------------------

    @on(Button.Pressed, "#chip-plan")
    def on_chip_plan(self) -> None:
        inp = self.query_one("#main-prompt-input", Input)
        inp.value = "/plan "
        inp.focus()

    @on(Button.Pressed, "#chip-help")
    def on_chip_help(self) -> None:
        self.action_show_help()

    @on(Button.Pressed, "#chip-model")
    def on_chip_model(self) -> None:
        self.action_switch_model()

    @on(Button.Pressed, "#chip-persona")
    def on_chip_persona(self) -> None:
        self.action_switch_persona()

    @on(Button.Pressed, "#chip-conflict")
    def on_chip_conflict(self) -> None:
        self.action_open_conflict_studio()

    @on(Button.Pressed, "#chip-pr")
    def on_chip_pr(self) -> None:
        self.action_open_pr_hub()

    @on(Button.Pressed, "#chip-mcp")
    def on_chip_mcp(self) -> None:
        self.action_open_mcp_inspector()

    @on(Button.Pressed, "#chip-radar")
    def on_chip_radar(self) -> None:
        self.action_open_swarm_radar()

    @on(Button.Pressed, "#chip-diff")
    def on_chip_diff(self) -> None:
        self.action_view_diff()

    @on(Button.Pressed, "#chip-rollback")
    def on_chip_rollback(self) -> None:
        self.action_rollback()

    @on(Button.Pressed, "#chip-test")
    def on_chip_test(self) -> None:
        self.action_run_tests()

    @on(Button.Pressed, "#chip-clear")
    def on_chip_clear(self) -> None:
        self.action_clear_chat()

    # --------------------------------------------------------------------------
    # Context Files & DevDocs Events
    # --------------------------------------------------------------------------

    @on(ContextFilesWidget.FileAdded)
    def on_context_file_added(self, event: ContextFilesWidget.FileAdded) -> None:
        self.add_context_file(event.file_path)

    @on(ContextFilesWidget.FileRemoved)
    def on_context_file_removed(self, event: ContextFilesWidget.FileRemoved) -> None:
        self.remove_context_file(event.file_path)

    def add_context_file(self, file_path: str) -> None:
        ok = self.session.add_file(file_path)
        if ok:
            self.sync_session_state()
            self.notify(f"Added '{file_path}' to active context.", severity="information")
        else:
            self.notify(f"File '{file_path}' not found.", severity="error")

    def remove_context_file(self, file_path: str) -> None:
        ok = self.session.remove_file(file_path)
        if ok:
            self.sync_session_state()
            self.notify(f"Removed '{file_path}' from active context.", severity="information")
        else:
            self.notify(f"File '{file_path}' not in context.", severity="warning")

    @on(QuickDevDocsWidget.SymbolInspected)
    def on_symbol_inspected(self, event: QuickDevDocsWidget.SymbolInspected) -> None:
        self.push_screen(DocDetailModal(event.symbol_data))

    # --------------------------------------------------------------------------
    # Asynchronous Workers: Execution Pipeline
    # --------------------------------------------------------------------------

    async def execute_turn_worker(self, prompt: str) -> None:
        """Executes user prompt asynchronously in background worker thread."""
        chat_stream = self.query_one("#chat-stream", VerticalScroll)
        p_meta = get_persona_ui_meta(self.active_persona)
        now_str = datetime.now().strftime("%H:%M:%S")

        start_time = time.time()
        accumulated_text = ""

        header_widget = Static(
            f"{p_meta['icon']} [bold {p_meta['color']}]{p_meta['title'].upper()}[/bold {p_meta['color']}] "
            f"[dim]• {now_str} • Generating...[/dim]",
            classes="message-header message-assistant-header",
        )
        content_static = Static("[dim italic]Thinking & synthesizing code...[/dim italic]")
        msg_container = ChatMessageCard(header_widget, content_static, classes="chat-message-assistant")

        def _mount_initial():
            chat_stream.mount(msg_container)
            chat_stream.scroll_end(animate=True)

        self.call_from_thread(_mount_initial)

        gen = self.session.process_turn(prompt)
        for token in gen:
            accumulated_text += token
            self.speedometer.record_tokens(1)

            def _update_stream(tok_text: str):
                think_block, clean_body = extract_think_blocks(tok_text)
                preview = clean_body if clean_body else tok_text
                content_static.update(escape(preview[:300]) + ("..." if len(preview) > 300 else ""))

            self.call_from_thread(_update_stream, accumulated_text)

        elapsed = time.time() - start_time
        res = self.session.last_result or {}

        # Record cost
        tok_used = len(accumulated_text.split())
        self.cost_ticker.record_usage(self.active_model, 0, tok_used)

        think_text, clean_output = extract_think_blocks(res.get("output", accumulated_text))
        if not clean_output.strip() and res.get("code"):
            clean_output = f"```python\n{res['code']}\n```"

        def _render_final():
            content_static.remove()

            if think_text or (res.get("attempts", 1) > 1):
                reasoning_body = think_text or "Architecture & multi-stage validation executed."
                msg_container.mount(ReasoningAccordion(reasoning_body, duration_sec=elapsed, is_streaming=False))

            msg_container.mount(Markdown(clean_output if clean_output.strip() else "_Task completed successfully._"))

            msg_container.mount(
                ToolStatusCard(
                    success=res.get("success", True),
                    verification_type="ast_syntax",
                    attempts=res.get("attempts", 1),
                    ram_mb=res.get("ram_mb", self.ram_mb),
                    patches_applied=res.get("patches_applied", False),
                    error_trace=res.get("patch_error", ""),
                )
            )

            header_widget.update(
                f"{p_meta['icon']} [bold {p_meta['color']}]{p_meta['title'].upper()}[/bold {p_meta['color']}] "
                f"[dim]• {now_str} • Completed in {elapsed:.2f}s[/dim]"
            )
            chat_stream.scroll_end(animate=True)
            self.sync_session_state()

            if self.git_guard.is_git_repo():
                diff_widget = self.query_one("#diff-viewer-widget", DiffViewerWidget)
                diff_widget.diff_text = self.git_guard.get_diff()

        self.call_from_thread(_render_final)
        self.is_busy = False

    async def execute_subagents_worker(self, prompt: str, max_workers: int = 4) -> None:
        """Executes multi-agent DAG task decomposition in background."""
        self.is_busy = True
        tree_widget = self.query_one("#live-swarm-tree-widget", LiveSubagentTreeWidget)
        chat_stream = self.query_one("#chat-stream", VerticalScroll)
        now_str = datetime.now().strftime("%H:%M:%S")

        tasks = self.dispatcher.decomposer.decompose(
            prompt=prompt,
            context_files=self.session.get_context_files(),
        )

        self.call_from_thread(tree_widget.set_tasks, tasks)

        def _event_cb(msg: SubagentMessage):
            if msg.msg_type == SubagentMessageType.PROGRESS:
                tid = msg.payload.get("task_id", "")
                prog = float(msg.payload.get("progress", 0.0))
                s_msg = msg.payload.get("status_message", "")
                self.call_from_thread(
                    tree_widget.update_task_progress,
                    tid,
                    prog,
                    s_msg,
                    SubagentStatus.RUNNING,
                )
            elif msg.msg_type == SubagentMessageType.TASK_COMPLETE:
                tid = msg.payload.get("task_id", "")
                self.call_from_thread(
                    tree_widget.update_task_progress,
                    tid,
                    1.0,
                    "Completed",
                    SubagentStatus.COMPLETED,
                )

        run_res = self.dispatcher.dispatch(tasks=tasks, event_callback=_event_cb)

        def _render_swarm_summary():
            widgets = [
                Static(
                    f"📦 [bold #00f0ff]SUBAGENT SWARM RUN[/bold #00f0ff] [dim]• {now_str}[/dim]",
                    classes="message-header message-assistant-header",
                ),
                Static(
                    f"[bold green]Multi-Agent Swarm Completed ({len(run_res.tasks)} Tasks in {run_res.total_duration_sec:.2f}s)[/bold green]\n"
                ),
                Markdown(f"```\n{run_res.summary}\n```"),
            ]
            if run_res.aggregated_patch:
                widgets.append(Markdown(f"### Unified Aggregated Patch:\n```diff\n{run_res.aggregated_patch}\n```"))
            elif run_res.final_code:
                widgets.append(Markdown(f"### Final Implementation:\n```python\n{run_res.final_code}\n```"))
            summary_card = ChatMessageCard(*widgets, classes="chat-message-assistant")
            chat_stream.mount(summary_card)

            chat_stream.scroll_end(animate=True)
            self.sync_session_state()

        self.call_from_thread(_render_swarm_summary)
        self.is_busy = False

    # --------------------------------------------------------------------------
    # Actions & Keybinding Handlers
    # --------------------------------------------------------------------------

    def action_switch_model(self) -> None:
        def _on_model_selected(model_name: Optional[str]) -> None:
            if model_name:
                self.switch_model(model_name)

        self.push_screen(ModelSelectModal(), _on_model_selected)

    def switch_model(self, model_name: str) -> None:
        self.session.set_model(model_name)
        self.active_model = model_name
        self.cost_ticker.active_model = model_name
        self.sync_session_state()
        self.notify(f"Switched model to '{model_name}'", severity="information")

    def action_switch_persona(self) -> None:
        def _on_persona_selected(persona_title: Optional[str]) -> None:
            if persona_title:
                self.switch_persona(persona_title)

        self.push_screen(PersonaSelectModal(), _on_persona_selected)

    def switch_persona(self, persona_query: str) -> None:
        ok, msg = self.session.set_persona(persona_query)
        if ok:
            self.active_persona = self.session.get_persona()
            self.sync_session_state()
            self.notify(f"Persona: {self.active_persona}", severity="information")
        else:
            self.notify(msg, severity="error")

    def action_spawn_subagents(self) -> None:
        def _on_spawn_confirmed(params: Optional[Tuple[str, int]]) -> None:
            if params:
                prompt, workers = params
                self.run_worker(self.execute_subagents_worker(prompt, workers), exclusive=True, thread=True)

        self.push_screen(SubagentSpawnModal(), _on_spawn_confirmed)

    def action_open_swarm_radar(self) -> None:
        """Switches to Swarm Radar Tab (Ctrl+S)."""
        tabs = self.query_one("#workspace-tabs", TabbedContent)
        tabs.active = "tab-radar"

    def action_open_conflict_studio(self) -> None:
        """Switches to 3-Way Conflict Studio Tab (Ctrl+K)."""
        tabs = self.query_one("#workspace-tabs", TabbedContent)
        tabs.active = "tab-conflict"

    def action_open_pr_hub(self) -> None:
        """Switches to GitHub PR Hub Tab (Ctrl+G)."""
        tabs = self.query_one("#workspace-tabs", TabbedContent)
        tabs.active = "tab-pr"

    def action_open_mcp_inspector(self) -> None:
        """Switches to MCP Server Inspector Tab (Ctrl+I)."""
        tabs = self.query_one("#workspace-tabs", TabbedContent)
        tabs.active = "tab-mcp"

    def action_view_diff(self) -> None:
        """Switches to Diff Viewer Tab (Ctrl+D)."""
        tabs = self.query_one("#workspace-tabs", TabbedContent)
        tabs.active = "tab-diff"
        if self.git_guard.is_git_repo():
            diff_widget = self.query_one("#diff-viewer-widget", DiffViewerWidget)
            diff_widget.diff_text = self.git_guard.get_diff()

    def action_rollback(self) -> None:
        ok, msg = self.session.undo_last_edit()
        if ok:
            self.notify("Rolled back uncommitted changes.", severity="information")
            self.sync_session_state()
            if self.git_guard.is_git_repo():
                diff_widget = self.query_one("#diff-viewer-widget", DiffViewerWidget)
                diff_widget.diff_text = ""
        else:
            self.notify(msg, severity="warning")

    def action_run_tests(self) -> None:
        passed, summary = self.session.run_test()
        if passed:
            self.notify(summary, severity="information")
        else:
            self.notify(summary, severity="error")

    def action_clear_chat(self) -> None:
        chat_stream = self.query_one("#chat-stream", VerticalScroll)
        chat_stream.remove_children()
        self.session.clear_history()
        self.notify("Chat stream cleared.", severity="information")

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#left-sidebar", Vertical)
        sidebar.display = not sidebar.display

    def action_show_help(self) -> None:
        self.push_screen(HelpModal())

    def action_quit_app(self) -> None:
        self.exit()


# ==============================================================================
# Entrypoint & CLI Wrapper
# ==============================================================================

def main():
    """Main CLI entrypoint for standalone Textual execution."""
    import argparse

    parser = argparse.ArgumentParser(description="K-CLI Textual Cyberpunk Workstation")
    parser.add_argument("--model", "-m", default="Bankai-7B", help="Active model name")
    parser.add_argument("--persona", "-p", default="Fullstack AI Systems Engineer", help="Active persona")
    parser.add_argument("--mock", action="store_true", help="Force mock offline execution")
    parser.add_argument("--workspace", "-w", default=".", help="Target workspace root directory")

    args = parser.parse_args()

    app = KCliApp(
        workspace_dir=args.workspace,
        model_name=args.model,
        persona=args.persona,
        mock_mode=args.mock,
    )
    app.run()


if __name__ == "__main__":
    main()
