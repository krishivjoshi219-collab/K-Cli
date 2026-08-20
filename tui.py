"""
tui.py - Modern Terminal User Interface Architecture for K-CLI

Features:
1. Live token streaming with syntax highlighting and real-time metrics.
2. Dynamic Status Bar displaying Active Model, Git Branch, Active Persona, RAM, and Tokens.
3. Interactive slash commands (/model, /persona, /diff, /rollback, /help, /docs, /clear, /test).
4. Side-by-side and inline surgical diff visualization.
5. High-speed prompt_toolkit interactive shell with auto-completion and toolbar.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.styles import Style as PTKStyle
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

try:
    import psutil
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import Header, Footer, Input, Static, Button, RichLog, Label
    HAS_TEXTUAL = True
except (ImportError, ModuleNotFoundError):
    HAS_TEXTUAL = False
    App = object  # type: ignore

try:
    from k_cli.diff_viewer import DiffVisualizer
    from k_cli.orchestrator import Persona
    from k_cli.persona import DomainPersona, PersonaProfile, PersonaRegistry
except (ModuleNotFoundError, ImportError):
    try:
        from diff_viewer import DiffVisualizer
        from orchestrator import Persona
        from persona import DomainPersona, PersonaProfile, PersonaRegistry
    except (ModuleNotFoundError, ImportError):
        DiffVisualizer = None
        Persona = None
        PersonaRegistry = None

# Model Presets
MODEL_PRESETS: List[Dict[str, str]] = [
    {"name": "Bankai-7B", "desc": "Project Bankai Flagship 7B Coder (Fast & Compiler-Grounded)", "type": "SLM"},
    {"name": "Bankai-14B", "desc": "Project Bankai Flagship 14B Deep Reasoning Engine", "type": "SLM"},
    {"name": "Gemini", "desc": "Gemini 2.0 Flash / Pro (Cloud Multi-Modal & High-Throughput)", "type": "Cloud"},
    {"name": "Claude", "desc": "Claude 3.5 Sonnet (Advanced Agentic Architecture & Refactoring)", "type": "Cloud"},
    {"name": "Local Ollama", "desc": "Local GGUF SLM (qwen2.5-coder:1.5b < 1GB RAM Budget)", "type": "Local"},
]

PERSONA_METADATA: Dict[str, Dict[str, str]] = {
    "DEVOPS": {"color": "cyan", "icon": "☸", "desc": "Docker, Kubernetes, CI/CD, Terraform, Cloud Deployments"},
    "SURGICAL DEBUGGER": {"color": "red", "icon": "🩺", "desc": "Root-cause analysis, minimal SEARCH/REPLACE diffs, zero regression"},
    "SYSTEMS ARCHITECT": {"color": "magenta", "icon": "⚡", "desc": "C++23, Rust, Linux Kernel, Lock-free concurrency, Big-O proofs"},
    "APPLICATION SECURITY ENGINEER": {"color": "red", "icon": "🛡️", "desc": "OWASP Top 10, HMAC, Auth middlewares, Constant-time crypto"},
    "FRONTEND & FULLSTACK ENGINEER": {"color": "green", "icon": "🎨", "desc": "React, Vite, Next.js, CSS layout, accessibility"},
    "DATABASE & QUERY OPTIMIZER": {"color": "yellow", "icon": "🗄️", "desc": "PostgreSQL, Redis, Spanner, SQL query optimization"},
    "FULLSTACK AI SYSTEMS ENGINEER": {"color": "blue", "icon": "⚙", "desc": "Clean architecture, compiler-grounded verification (< 1GB RAM)"},
    "RESEARCHER": {"color": "cyan", "icon": "🔍", "desc": "Extracts signatures, API dependencies, specifications"},
    "ARCHITECT": {"color": "magenta", "icon": "📐", "desc": "Designs modular architecture & execution plan"},
    "CODER": {"color": "green", "icon": "⚡", "desc": "Generates isolated, verified code implementation"},
    "CRITIC": {"color": "yellow", "icon": "🛡️", "desc": "Audits safety, boundaries, memory & runtime limits"},
    "DEBUGGER": {"color": "red", "icon": "🔧", "desc": "Analyzes compiler traces and applies surgical repairs"},
    "AUTO": {"color": "bright_blue", "icon": "🔄", "desc": "Full sequential multi-persona pipeline"},
}


def get_persona_style(persona_name: str) -> Tuple[str, str, str]:
    """Returns (color, icon, description) for a given persona."""
    if not persona_name:
        return "blue", "🤖", "AI Assistant Persona"

    key = str(persona_name).upper().strip()
    if key in PERSONA_METADATA:
        p_v = PERSONA_METADATA[key]
        return p_v["color"], p_v["icon"], p_v["desc"]

    # Check PersonaRegistry first if available
    if PersonaRegistry:
        prof = PersonaRegistry.get(persona_name)
        if prof is not None:
            return prof.color, prof.icon, prof.description

    for p_k, p_v in PERSONA_METADATA.items():
        if p_k in key or key in p_k:
            return p_v["color"], p_v["icon"], p_v["desc"]
    return "blue", "🤖", "AI Assistant Persona"


# ==============================================================================
# 1. Status Bar Manager
# ==============================================================================

class StatusBar:
    """Manages active session parameters and formats top/bottom status displays."""

    def __init__(
        self,
        active_model: str = "Bankai-7B",
        git_branch: str = "main",
        active_persona: str = "AUTO",
        ram_mb: float = 0.0,
        max_ram_mb: float = 1024.0,
        token_count: int = 0,
        max_tokens: int = 4096,
        context_files: Optional[List[str]] = None,
    ):
        self.active_model = active_model
        self.git_branch = git_branch
        self.active_persona = active_persona
        self.ram_mb = ram_mb
        self.max_ram_mb = max_ram_mb
        self.token_count = token_count
        self.max_tokens = max_tokens
        self.context_files = context_files or []

    def update_from_session(self, session: Any) -> None:
        """Syncs status bar properties from SessionManager status dict."""
        if not session:
            return
        st = session.get_status() if hasattr(session, "get_status") else {}
        self.active_model = st.get("model") or st.get("model_name") or self.active_model
        self.git_branch = st.get("git_branch") or (session.get_git_branch() if hasattr(session, "get_git_branch") else self.git_branch)
        self.active_persona = st.get("persona") or st.get("active_persona") or getattr(session, "active_persona", self.active_persona)
        self.ram_mb = st.get("ram_mb", 0.0)
        self.token_count = st.get("token_count", 0)
        self.max_tokens = st.get("max_tokens", self.max_tokens)
        self.context_files = st.get("context_files", [])

    def get_prompt_toolkit_toolbar(self) -> HTML:
        """Returns stylized HTML for prompt_toolkit bottom toolbar."""
        p_color, p_icon, _ = get_persona_style(self.active_persona)
        ptk_color_map = {
            "cyan": "#00d7ff",
            "magenta": "#ff00d7",
            "green": "#5af78e",
            "yellow": "#f3e430",
            "red": "#ff5c57",
            "bright_blue": "#57c7ff",
            "blue": "#57c7ff",
        }
        hex_p = ptk_color_map.get(p_color, "#57c7ff")
        files_str = f"{len(self.context_files)} files" if self.context_files else "0 files"

        return HTML(
            f' <b>Model:</b> <style color="#00ffff">{self.active_model}</style> │ '
            f'<b>Branch:</b> <style color="#5af78e">{self.git_branch}</style> │ '
            f'<b>Persona:</b> <style color="{hex_p}">{p_icon} {self.active_persona}</style> │ '
            f'<b>RAM:</b> <style color="#ffb86c">{self.ram_mb:.1f}/{self.max_ram_mb:.0f}MB</style> │ '
            f'<b>Context:</b> <style color="#8be9fd">{files_str}</style>'
        )

    def render_rich_panel(self) -> Panel:
        """Renders full diagnostic status panel for Rich terminal display."""
        p_color, p_icon, p_desc = get_persona_style(self.active_persona)

        table = Table(box=None, expand=True, padding=(0, 1))
        table.add_column("Parameter", style="bold cyan", width=22)
        table.add_column("Value", style="bold white")

        table.add_row("⚡ Active Model", f"[bold green]{self.active_model}[/bold green]")
        table.add_row("🌿 Git Branch", f"[bold yellow]{self.git_branch}[/bold yellow]")
        table.add_row(f"{p_icon} Active Persona", f"[{p_color}][bold]{self.active_persona}[/bold] - {p_desc}[/{p_color}]")
        table.add_row("💾 RAM RSS Allocation", f"[bold magenta]{self.ram_mb:.2f} MB[/bold magenta] / {self.max_ram_mb:.0f} MB (Budget Limit)")
        table.add_row("📊 Estimated Tokens", f"{self.token_count} / {self.max_tokens} max")
        files_text = ", ".join(self.context_files) if self.context_files else "[dim]None (use /add <file>)[/dim]"
        table.add_row("📁 Tracked Files", files_text)

        return Panel(table, title="[bold cyan]K-CLI System & Session Status[/bold cyan]", border_style="cyan")


# ==============================================================================
# 2. Live Token Streaming Renderer with Syntax Highlighting
# ==============================================================================

class LiveStreamRenderer:
    """Manages real-time token streaming with automatic code fence syntax highlighting."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def stream_display(
        self,
        token_generator: Generator[str, None, Dict[str, Any]],
        initial_persona: str = "RESEARCHER",
        language: str = "python",
        title: str = "Agent Execution",
    ) -> Dict[str, Any]:
        """
        Consumes tokens from generator, dynamically highlighting syntax and updating Rich Live view.
        """
        current_persona = initial_persona
        accumulated_text = ""
        token_count = 0
        start_time = time.time()

        def make_panel() -> Panel:
            elapsed = max(0.001, time.time() - start_time)
            speed = token_count / elapsed
            p_color, p_icon, _ = get_persona_style(current_persona)

            header = f"[{p_color}][bold]{p_icon} Persona: [{current_persona}][/bold][/{p_color}] │ [dim]{token_count} tokens ({speed:.1f} tok/s)[/dim]"

            if not accumulated_text.strip():
                content = Text(f"Initializing {current_persona} pipeline...", style="dim italic")
            elif "```" in accumulated_text:
                # Detect and highlight code fences
                try:
                    content = Markdown(accumulated_text)
                except Exception:
                    content = Text(accumulated_text)
            elif current_persona in ("CODER", "DEBUGGER"):
                # Pure code output
                try:
                    content = Syntax(accumulated_text, language, theme="monokai", line_numbers=True)
                except Exception:
                    content = Text(accumulated_text, style="green")
            else:
                content = Text(accumulated_text, style="white")

            return Panel(content, title=header, border_style=p_color)

        with Live(make_panel(), console=self.console, refresh_per_second=15, auto_refresh=True) as live:
            for token in token_generator:
                token_count += 1
                accumulated_text += token
                live.update(make_panel())

        return {
            "total_tokens": token_count,
            "elapsed_seconds": time.time() - start_time,
            "final_text": accumulated_text,
        }


# ==============================================================================
# 3. Prompt Toolkit Slash Command Completer
# ==============================================================================

if HAS_PROMPT_TOOLKIT:
    class SlashCommandCompleter(Completer):
        """Auto-completes slash commands with rich descriptions in prompt_toolkit."""

        COMMANDS = [
            ("/model", "Switch active model (Bankai-7B, Bankai-14B, Gemini, Claude, Local Ollama)"),
            ("/persona", "Switch active persona (RESEARCHER, ARCHITECT, CODER, CRITIC, DEBUGGER, AUTO)"),
            ("/diff", "View surgical / git diff (inline or side-by-side)"),
            ("/rollback", "Roll back last uncommitted edit via Git (alias /undo)"),
            ("/help", "Show all slash commands, shortcuts, and capabilities"),
            ("/docs", "Search DevDocs offline documentation index (alias /doc)"),
            ("/clear", "Reset conversation history and context files"),
            ("/test", "Run ground-truth compiler and pytest verification"),
            ("/add", "Add file to active session context"),
            ("/remove", "Remove file from active session context"),
            ("/undo", "Roll back last uncommitted edit via Git"),
            ("/status", "Display active model, context files, tokens, and RAM"),
            ("/map", "Display workspace AST symbol repository map"),
            ("/exit", "Exit interactive session"),
            ("/quit", "Exit interactive session"),
        ]

        MODEL_OPTIONS = [m["name"] for m in MODEL_PRESETS]
        PERSONA_OPTIONS = ["AUTO", "RESEARCHER", "ARCHITECT", "CODER", "CRITIC", "DEBUGGER"]
        DIFF_OPTIONS = ["inline", "side-by-side", "sbs"]

        def get_completions(self, document, complete_event):
            text = document.text_before_cursor
            if not text.startswith("/"):
                return

            parts = text.split()
            if len(parts) == 1 and not text.endswith(" "):
                # Completing slash command name
                query = parts[0].lower()
                for cmd, desc in self.COMMANDS:
                    if cmd.startswith(query):
                        yield Completion(cmd, start_position=-len(query), display=cmd, display_meta=desc)
            elif len(parts) >= 1:
                cmd = parts[0].lower()
                sub_query = parts[1].lower() if len(parts) > 1 and not text.endswith(" ") else ""
                start_pos = -len(sub_query) if sub_query else 0

                if cmd == "/model":
                    for m in self.MODEL_OPTIONS:
                        if not sub_query or m.lower().startswith(sub_query):
                            yield Completion(m, start_position=start_pos, display=m)
                elif cmd == "/persona":
                    for p in self.PERSONA_OPTIONS:
                        if not sub_query or p.lower().startswith(sub_query):
                            yield Completion(p, start_position=start_pos, display=p)
                elif cmd == "/diff":
                    for d in self.DIFF_OPTIONS:
                        if not sub_query or d.lower().startswith(sub_query):
                            yield Completion(d, start_position=start_pos, display=d)


# ==============================================================================
# 4. Interactive Slash Commands Handler
# ==============================================================================

class SlashCommandHandler:
    """Handles and visually formats interactive slash commands."""

    def __init__(self, session: Any, console: Optional[Console] = None):
        self.session = session
        self.console = console or Console()
        self.diff_visualizer = DiffVisualizer(console=self.console)

    def handle(self, command_line: str) -> Tuple[bool, str]:
        """
        Routes slash command and renders rich terminal output.

        Returns:
            Tuple[bool, str]: (should_continue, exit_signal_or_status)
        """
        raw = command_line.strip()
        if not raw.startswith("/"):
            return True, ""

        parts = raw[1:].split(None, 1)
        cmd = parts[0].lower() if parts else ""
        arg = parts[1].strip() if len(parts) > 1 else ""

        # /exit, /quit
        if cmd in ("exit", "quit", "q"):
            self.console.print("[bold dim]Exiting K-CLI. Goodbye![/bold dim]")
            return False, "EXIT"

        # /help
        if cmd in ("help", "?"):
            self._render_help()
            return True, "HELP_RENDERED"

        # /model
        if cmd == "model":
            self._handle_model(arg)
            return True, "MODEL_HANDLED"

        # /persona
        if cmd in ("persona", "role"):
            self._handle_persona(arg)
            return True, "PERSONA_HANDLED"

        # /diff
        if cmd == "diff":
            self._handle_diff(arg)
            return True, "DIFF_HANDLED"

        # /rollback or /undo
        if cmd in ("rollback", "undo"):
            self._handle_rollback(arg)
            return True, "ROLLBACK_HANDLED"

        # /docs or /doc
        if cmd in ("docs", "doc"):
            self._handle_docs(arg)
            return True, "DOCS_HANDLED"

        # /clear
        if cmd in ("clear", "cls"):
            self.console.clear()
            self.session.reset_context()
            self.console.print("[bold green]✔ Screen, conversation history, and context files cleared.[/bold green]\n")
            return True, "CLEARED"

        # /test or /verify
        if cmd in ("test", "verify"):
            self._handle_test(arg)
            return True, "TEST_HANDLED"

        # Delegate /add, /remove, /map, /status to SessionManager
        handled, msg = self.session.handle_slash_command(raw)
        if handled:
            if cmd == "status":
                status_bar = StatusBar()
                status_bar.update_from_session(self.session)
                self.console.print(status_bar.render_rich_panel())
            elif cmd == "map" and self.session.repo_map:
                map_str = self.session.repo_map.get_repo_map(max_tokens=400, focus_files=self.session.get_context_files())
                if map_str.strip():
                    map_syn = Syntax(map_str, "python", theme="monokai", line_numbers=False)
                    self.console.print(Panel(map_syn, title="[bold magenta]AST Repository Codebase Map[/bold magenta]", border_style="magenta"))
                else:
                    self.console.print("[yellow]Repository map is empty.[/yellow]")
            else:
                self.console.print(f"[bold cyan]{msg}[/bold cyan]")
            return True, msg

        self.console.print(f"[bold red]Unknown command:[/bold red] {raw}. Type [bold yellow]/help[/bold yellow] for available commands.")
        return True, "UNKNOWN_COMMAND"

    def _render_help(self) -> None:
        table = Table(title="K-CLI Interactive Slash Commands", box=None, expand=True)
        table.add_column("Command", style="bold cyan", width=18)
        table.add_column("Arguments", style="bold yellow", width=16)
        table.add_column("Description", style="white")

        commands_info = [
            ("/model", "[name]", "Switch active model (Bankai-7B, Bankai-14B, Gemini, Claude, Local Ollama)"),
            ("/persona", "[name]", "Switch active persona (RESEARCHER, ARCHITECT, CODER, CRITIC, DEBUGGER, AUTO)"),
            ("/diff", "[mode]", "View surgical git diff (options: inline, side-by-side / sbs)"),
            ("/rollback", "[file]", "Roll back last uncommitted edit via Git (alias /undo)"),
            ("/docs", "<query>", "Search offline DevDocs SQLite database for API signatures"),
            ("/clear", "", "Clear terminal screen, conversation history, and context"),
            ("/test", "[file/code]", "Run ground-truth compiler / pytest verification"),
            ("/add", "<file>", "Add file to active session context"),
            ("/remove", "<file>", "Remove file from active session context"),
            ("/map", "", "Display AST codebase repository map"),
            ("/status", "", "Inspect model, token usage, and RAM budget diagnostics"),
            ("/help", "", "Show this help table"),
            ("/exit", "", "Exit interactive session (alias /quit)"),
        ]

        for cmd, args, desc in commands_info:
            table.add_row(cmd, args, desc)

        self.console.print(Panel(table, title="[bold cyan]Command Reference[/bold cyan]", border_style="cyan"))

    def _handle_model(self, model_arg: str) -> None:
        if not model_arg:
            table = Table(title="Available AI Models", box=None, expand=True)
            table.add_column("Preset", style="bold cyan", width=18)
            table.add_column("Engine", style="bold magenta", width=10)
            table.add_column("Description", style="white")
            table.add_column("Active", style="bold green", width=8)

            current = getattr(self.session, "model_name", "")
            for p in MODEL_PRESETS:
                is_active = "✔ YES" if p["name"].lower() == current.lower() or current.lower().startswith(p["name"].lower().split()[0]) else ""
                table.add_row(p["name"], p["type"], p["desc"], is_active)

            self.console.print(Panel(table, title="[bold cyan]Active & Available Models[/bold cyan]", border_style="cyan"))
            self.console.print(f"[dim]Use [/dim][bold yellow]/model <name>[/bold yellow][dim] to switch models (e.g. [/dim][bold cyan]/model Bankai-14B[/bold cyan][dim]).[/dim]\n")
        else:
            self.session.set_model(model_arg)
            self.console.print(f"[bold green]✔ Switched active model to:[/bold green] [bold cyan]{model_arg}[/bold cyan]")

    def _handle_persona(self, persona_arg: str) -> None:
        if not persona_arg:
            table = Table(title="Dynamic Persona & Architecture State Machine", box=None, expand=True)
            table.add_column("Persona", style="bold cyan", width=32)
            table.add_column("Command", style="bold yellow", width=14)
            table.add_column("Description", style="white")
            table.add_column("Active", style="bold green", width=8)

            current = getattr(self.session, "active_persona", "AUTO")
            active_id = getattr(self.session.active_persona_profile, "id", "") if hasattr(self.session, "active_persona_profile") and self.session.active_persona_profile else ""

            if PersonaRegistry:
                for p in PersonaRegistry.list_personas():
                    is_active = "✔ YES" if (p.id == active_id or p.title.lower() == str(current).lower()) else ""
                    table.add_row(f"[{p.color}][bold]{p.icon} {p.title}[/bold][/{p.color}]", f"/{p.id}", p.description, is_active)
            else:
                valid_personas = ["AUTO", "RESEARCHER", "ARCHITECT", "CODER", "CRITIC", "DEBUGGER"]
                for p in valid_personas:
                    color, icon, desc = get_persona_style(p)
                    is_active = "✔ YES" if p == current else ""
                    table.add_row(f"[{color}][bold]{icon} {p}[/bold][/{color}]", f"/{p.lower()}", desc, is_active)

            self.console.print(Panel(table, title="[bold cyan]Dynamic Persona Profiles[/bold cyan]", border_style="cyan"))
            self.console.print(f"[dim]Use [/dim][bold yellow]/persona <name>[/bold yellow][dim] to switch (e.g. [/dim][bold cyan]/persona devops[/bold cyan][dim] or [/dim][bold cyan]/persona debugger[/bold cyan][dim]).[/dim]\n")
        else:
            success, msg = self.session.set_persona(persona_arg)
            if success:
                p_color, p_icon, _ = get_persona_style(self.session.active_persona)
                self.console.print(f"[bold green]✔ {msg}[/bold green]")
            else:
                self.console.print(f"[bold red]{msg}[/bold red]")

    def _handle_diff(self, mode_arg: str) -> None:
        if not self.session.git_guard.is_git_repo():
            self.console.print("[yellow]Not inside a Git repository. No diff available.[/yellow]")
            return

        diff_text = self.session.git_guard.get_diff()
        if not diff_text.strip():
            self.console.print("[dim]Working tree is clean; no uncommitted changes.[/dim]")
            return

        mode = (mode_arg or "").lower().strip()
        is_side_by_side = mode in ("sbs", "side-by-side", "2col", "side")

        if is_side_by_side:
            # Render side-by-side diff if we have candidate vs repaired or file diff
            self.console.print(DiffVisualizer.render_inline_diff(diff_text, title="Git Working Tree Diff (Inline)"))
        else:
            self.console.print(DiffVisualizer.render_inline_diff(diff_text, title="Git Working Tree Diff"))

    def _handle_rollback(self, file_arg: str) -> None:
        files = [file_arg] if file_arg else None
        if not self.session.git_guard.is_git_repo():
            self.console.print("[yellow]Not inside a Git repository; cannot rollback.[/yellow]")
            return

        success = self.session.git_guard.rollback(files=files)
        if success:
            target_str = f" for '{file_arg}'" if file_arg else ""
            self.console.print(f"[bold green]✔ Successfully rolled back uncommitted changes{target_str}.[/bold green]")
        else:
            self.console.print("[bold red]✘ Rollback failed or no changes to revert.[/bold red]")

    def _handle_docs(self, query: str) -> None:
        if not query:
            self.console.print("[yellow]Usage: /docs <query> (e.g. /docs json.loads)[/yellow]")
            return

        if not self.session.doc_retriever:
            self.console.print("[yellow]DevDocs retriever not available.[/yellow]")
            return

        results = self.session.doc_retriever.search(query, limit=3, max_tokens=250)
        if not results:
            self.console.print(f"[yellow]No documentation found for '{query}'.[/yellow]")
            return

        self.console.print(f"[bold cyan]DevDocs search results for '{query}':[/bold cyan]\n")
        for r in results:
            name = r.get("name", "")
            sig = r.get("signature", "")
            doc_str = r.get("doc", "")
            module = r.get("module", "")
            content = f"[bold green]{sig}[/bold green]\n\n[dim]{doc_str}[/dim]"
            self.console.print(Panel(content, title=f"Module: {module} | Symbol: {name}", border_style="cyan"))

    def _handle_test(self, target_arg: str) -> None:
        passed, summary = self.session.run_test(target_arg if target_arg else None)
        if passed:
            self.console.print(f"[bold green]{summary}[/bold green]")
        else:
            self.console.print(f"[bold red]{summary}[/bold red]")


# ==============================================================================
# 5. Interactive Shell Engine
# ==============================================================================

class InteractiveShell:
    """Prompt-toolkit powered high-speed interactive shell for K-CLI."""

    def __init__(
        self,
        session: Any,
        console: Optional[Console] = None,
    ):
        self.session = session
        self.console = console or Console()
        self.status_bar = StatusBar()
        self.status_bar.update_from_session(self.session)
        self.command_handler = SlashCommandHandler(session=self.session, console=self.console)
        self.stream_renderer = LiveStreamRenderer(console=self.console)

    def run(self) -> None:
        """Starts the interactive multi-turn REPL loop."""
        self.status_bar.update_from_session(self.session)

        # Setup prompt_toolkit if available and interactive terminal
        prompt_session = None
        if HAS_PROMPT_TOOLKIT and sys.stdin.isatty():
            try:
                style = PTKStyle.from_dict({
                    "prompt": "bold #00ffff",
                    "arrow": "bold #5af78e",
                })
                prompt_session = PromptSession(
                    completer=SlashCommandCompleter(),
                    history=InMemoryHistory(),
                    style=style,
                )
            except Exception:
                prompt_session = None

        while True:
            try:
                self.status_bar.update_from_session(self.session)

                if prompt_session:
                    prompt_input = prompt_session.prompt(
                        [("class:prompt", "K-CLI "), ("class:arrow", "❯ ")],
                        bottom_toolbar=self.status_bar.get_prompt_toolkit_toolbar,
                    ).strip()
                else:
                    prompt_input = self.console.input("[bold cyan]K-CLI [/bold cyan][bold green]❯ [/bold green]").strip()

                if not prompt_input:
                    continue

                # 1. Handle Slash Commands
                if prompt_input.startswith("/"):
                    cont, signal = self.command_handler.handle(prompt_input)
                    if not cont or signal == "EXIT":
                        break
                    self.console.print()
                    continue

                # 2. Conversational greetings
                clean_lower = prompt_input.lower().strip()
                if clean_lower in ("yo", "hi", "hello", "hey", "sup", "howdy", "greetings"):
                    self.console.print(Panel(
                        "[bold green]Yo! I'm K-CLI — your local, compiler-grounded AI coding assistant (< 1GB RAM).[/bold green]\n\n"
                        "[bold cyan]What you can do right now:[/bold cyan]\n"
                        "• [bold]Write & Refactor Code[/bold]: Enter a coding task (e.g. [italic]write a function to parse jwt tokens[/italic]).\n"
                        "• [bold]/model[/bold]: Switch active model (Bankai-7B, Bankai-14B, Gemini, Claude, Local Ollama).\n"
                        "• [bold]/persona[/bold]: Switch active persona (RESEARCHER, ARCHITECT, CODER, CRITIC, DEBUGGER).\n"
                        "• [bold]/add <file>[/bold]: Scope a file to active context for surgical edits.\n"
                        "• [bold]/diff[/bold] & [bold]/rollback[/bold]: Review git diff or undo any modification instantly.\n"
                        "• [bold]/docs <symbol>[/bold]: Instant SQLite FTS5 DevDocs lookup (e.g. [italic]/docs json.loads[/italic]).\n"
                        "• [bold]/test [file][/bold]: Run ground-truth verification on file or tests.\n"
                        "• [bold]/status[/bold]: Inspect active model, tokens, branch, and RAM diagnostics.",
                        title="[bold cyan]K-CLI Assistant[/bold cyan]",
                        border_style="cyan",
                    ))
                    self.console.print("\n" + "─" * 60 + "\n")
                    continue

                # 3. Live Token Streaming & Pipeline Turn Execution
                self.console.print(f"\n[bold yellow]Agent Task:[/bold yellow] [italic]'{prompt_input}'[/italic]\n")

                gen = self.session.process_turn(prompt_input)
                self.stream_renderer.stream_display(
                    token_generator=gen,
                    initial_persona=self.session.active_persona if self.session.active_persona != "AUTO" else "RESEARCHER",
                    language="python",
                )

                # 4. Result & Diff Presentation
                res = self.session.last_result or {}
                if res.get("success"):
                    self.console.print(f"\n[bold green]✔ GROUND-TRUTH VERIFIED[/bold green] [dim](Attempts: {res.get('attempts', 1)} | RAM: {res.get('ram_mb', 0):.2f} MB)[/dim]\n")
                    if res.get("code"):
                        syntax = Syntax(res["code"], "python", theme="monokai", line_numbers=True)
                        self.console.print(Panel(syntax, title="[bold green]Verified Implementation[/bold green]", border_style="green"))
                else:
                    self.console.print(f"\n[bold red]✘ VERIFICATION FAILED[/bold red] [dim](RAM: {res.get('ram_mb', 0):.2f} MB)[/dim]\n")
                    if res.get("patch_error"):
                        self.console.print(Panel(res["patch_error"], title="Patch Application Error", border_style="red"))
                    elif res.get("code"):
                        syntax = Syntax(res["code"], "python", theme="monokai", line_numbers=True)
                        self.console.print(Panel(syntax, title="Unverified Candidate Code", border_style="yellow"))

                self.console.print("\n" + "─" * 60 + "\n")

            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[bold dim]Exiting K-CLI. Goodbye![/bold dim]")
                break
            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")


# ==============================================================================
# 6. Full-Screen Textual TUI (KCliApp)
# ==============================================================================

TUI_ASCII_BANNER = r"""[bold cyan]
  ██╗  ██╗   ██████╗██╗     ██╗
  ██║ ██╔╝  ██╔════╝██║     ██║
  █████═╝   ██║     ██║     ██║
  ██╔═██╗   ██║     ██║     ██║
  ██║  ██╗  ╚██████╗███████╗██║
  ╚═╝  ╚═╝   ╚═════╝╚══════╝╚═╝
[/bold cyan][bold bright_white]PROJECT BANKAI ENGINE v0.2.0 | Compiler Guard (< 1GB RAM)[/bold bright_white]"""

if HAS_TEXTUAL:
    class KCliApp(App):
        """
        Full-Screen Textual TUI for K-CLI (Project Bankai Engine).
        Provides real-time system diagnostics, chat stream log, interactive slash commands,
        and compiler-grounded verification previews.
        """

        CSS = """
        Screen {
            background: #0d1117;
            color: #f0f6fc;
        }

        #app-container {
            width: 100%;
            height: 100%;
        }

        #main-layout {
            width: 100%;
            height: 1fr;
        }

        #sidebar {
            width: 32;
            background: #161b22;
            border-right: heavy #30363d;
            padding: 1 1;
        }

        .sidebar-header {
            text-style: bold;
            color: #58a6ff;
            margin-bottom: 1;
        }

        .sidebar-info {
            color: #8b949e;
            margin-bottom: 1;
        }

        #chat-container {
            width: 1fr;
            height: 100%;
            padding: 0 1;
        }

        #log-view {
            width: 100%;
            height: 1fr;
            background: #0d1117;
            border: solid #21262d;
            padding: 0 1;
        }

        #input-bar {
            dock: bottom;
            height: 3;
            background: #161b22;
            border-top: heavy #30363d;
            padding: 0 1;
        }

        #prompt-input {
            width: 1fr;
            border: none;
            background: #0d1117;
            color: #f0f6fc;
        }

        #btn-send {
            width: 10;
            margin-left: 1;
            background: #238636;
            color: white;
            border: none;
        }

        #btn-clear {
            width: 8;
            margin-left: 1;
            background: #30363d;
            color: white;
            border: none;
        }

        #btn-exit {
            width: 8;
            margin-left: 1;
            background: #da3633;
            color: white;
            border: none;
        }
        """

        BINDINGS = [
            Binding("ctrl+c", "quit", "Quit", priority=True),
            Binding("ctrl+l", "clear_screen", "Clear", show=True),
            Binding("f1", "help", "Help", show=True),
            Binding("f2", "switch_model", "Model", show=True),
            Binding("f3", "switch_persona", "Persona", show=True),
            Binding("f4", "view_diff", "Diff", show=True),
            Binding("f5", "run_tests", "Test", show=True),
        ]

        def __init__(
            self,
            session: Optional[Any] = None,
            model: str = "qwen2.5-coder:1.5b",
            mock: bool = False,
            workspace_dir: str = ".",
            **kwargs,
        ):
            super().__init__(**kwargs)
            self.workspace_dir = workspace_dir
            self.mock = mock
            self.model_name = model
            if session is not None:
                self.session = session
            else:
                try:
                    from k_cli.session import SessionManager
                except ModuleNotFoundError:
                    from session import SessionManager
                self.session = SessionManager(workspace_dir=workspace_dir, model_name=model, mock_mode=mock)
            self.command_handler = SlashCommandHandler(session=self.session)

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            with Container(id="app-container"):
                with Horizontal(id="main-layout"):
                    with Vertical(id="sidebar"):
                        yield Label("⚡ [bold cyan]K-CLI ENGINE[/bold cyan]", classes="sidebar-header")
                        yield Static(id="system-status", classes="sidebar-info")
                        yield Label("🔧 [bold yellow]QUICK COMMANDS[/bold yellow]", classes="sidebar-header")
                        yield Static(
                            "• [bold cyan]/model[/bold cyan] : Switch LLM\n"
                            "• [bold magenta]/persona[/bold magenta] : Switch role\n"
                            "• [bold green]/diff[/bold green] : Git diff\n"
                            "• [bold red]/rollback[/bold red] : Undo change\n"
                            "• [bold blue]/docs[/bold blue] : DevDocs\n"
                            "• [bold yellow]/test[/bold yellow] : Verify\n"
                            "• [bold white]/map[/bold white] : Codebase map\n"
                            "• [dim]/help | /clear | /exit[/dim]",
                            classes="sidebar-info"
                        )
                    with Vertical(id="chat-container"):
                        yield RichLog(id="log-view", wrap=True, highlight=True, markup=True)
                with Horizontal(id="input-bar"):
                    yield Input(placeholder="Type coding task or /command (e.g. /model, /diff, /test)...", id="prompt-input")
                    yield Button("Send ❯", variant="primary", id="btn-send")
                    yield Button("Clear", id="btn-clear")
                    yield Button("Exit", id="btn-exit")
            yield Footer()

        def on_mount(self) -> None:
            self.title = "K-CLI Bankai Engine v0.2.0"
            self.sub_title = f"Model: {self.session.model_name} | Persona: {self.session.active_persona}"
            self.update_sidebar()
            log = self.query_one("#log-view", RichLog)
            log.write(TUI_ASCII_BANNER)
            log.write(
                "\n[bold green]✔ Full-screen Textual TUI active.[/bold green] "
                "Type a coding task or slash command below, or press [bold yellow]F1[/bold yellow] for help.\n"
            )
            try:
                self.query_one("#prompt-input", Input).focus()
            except Exception:
                pass

        def update_sidebar(self) -> None:
            ram_mb = 0.0
            if psutil:
                try:
                    ram_mb = psutil.Process().memory_info().rss / (1024 * 1024)
                except Exception:
                    pass
            branch = self.session.get_git_branch() if hasattr(self.session, "get_git_branch") else "main"
            ctx_len = len(self.session.get_context_files()) if hasattr(self.session, "get_context_files") else 0
            status_text = (
                f"🤖 [bold]Model:[/bold] {self.session.model_name}\n"
                f"🎭 [bold]Persona:[/bold] {self.session.active_persona}\n"
                f"🌿 [bold]Branch:[/bold] {branch}\n"
                f"💾 [bold]RAM RSS:[/bold] {ram_mb:.1f} MB / 1024 MB\n"
                f"📁 [bold]Context:[/bold] {ctx_len} files"
            )
            try:
                status_widget = self.query_one("#system-status", Static)
                status_widget.update(status_text)
            except Exception:
                pass

        def on_button_pressed(self, event: Button.Pressed) -> None:
            btn_id = event.button.id
            if btn_id == "btn-send":
                self.submit_prompt()
            elif btn_id == "btn-clear":
                self.action_clear_screen()
            elif btn_id == "btn-exit":
                self.action_quit()

        def on_input_submitted(self, event: Input.Submitted) -> None:
            self.submit_prompt()

        def submit_prompt(self) -> None:
            inp = self.query_one("#prompt-input", Input)
            val = inp.value.strip()
            if not val:
                return
            inp.value = ""
            log = self.query_one("#log-view", RichLog)

            if val.startswith("/"):
                # Handle slash command
                cont, signal = self.command_handler.handle(val)
                if not cont or signal == "EXIT":
                    self.exit()
                    return
                if signal == "CLEARED":
                    log.clear()
                self.update_sidebar()
                return

            # Handle user prompt turn
            log.write(f"\n[bold cyan]User ❯[/bold cyan] {val}\n")

            # Execute turn
            try:
                gen = self.session.process_turn(val)
                accumulated = ""
                for token in gen:
                    accumulated += token

                res = self.session.last_result or {}
                if res.get("success"):
                    log.write(f"[bold green]✔ GROUND-TRUTH VERIFIED[/bold green] [dim](RAM: {res.get('ram_mb', 0):.2f} MB)[/dim]")
                    if res.get("code"):
                        log.write(Syntax(res["code"], "python", theme="monokai", line_numbers=True))
                else:
                    log.write(f"[bold red]✘ VERIFICATION FAILED[/bold red]")
                    if res.get("patch_error"):
                        log.write(Panel(res["patch_error"], title="Patch Error", border_style="red"))
                    elif res.get("code"):
                        log.write(Syntax(res["code"], "python", theme="monokai", line_numbers=True))
            except Exception as exc:
                log.write(f"[bold red]Execution Error:[/bold red] {exc}")

            self.update_sidebar()

        def action_clear_screen(self) -> None:
            log = self.query_one("#log-view", RichLog)
            log.clear()
            self.session.reset_context()
            log.write("[bold green]✔ Screen & history cleared.[/bold green]\n")
            self.update_sidebar()

        def action_help(self) -> None:
            log = self.query_one("#log-view", RichLog)
            self.command_handler.handle("/help")

        def action_switch_model(self) -> None:
            log = self.query_one("#log-view", RichLog)
            self.command_handler.handle("/model")

        def action_switch_persona(self) -> None:
            log = self.query_one("#log-view", RichLog)
            self.command_handler.handle("/persona")

        def action_view_diff(self) -> None:
            log = self.query_one("#log-view", RichLog)
            self.command_handler.handle("/diff")

        def action_run_tests(self) -> None:
            log = self.query_one("#log-view", RichLog)
            self.command_handler.handle("/test")

        def action_quit(self) -> None:
            self.exit()
else:
    class KCliApp:
        """Fallback when Textual is unavailable."""
        def __init__(self, *args, **kwargs):
            pass

        def run(self):
            print("Textual is not installed. Please install textual or use classic mode.")

