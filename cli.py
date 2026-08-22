"""
cli.py - Command Line Interface & TUI Entrypoint for K-CLI (Project Bankai Engine)

Features:
1. Live token streaming with dynamic syntax highlighting.
2. Real-time Status Bar (Active Model, Git Branch, Active Persona, RAM, Tokens).
3. Interactive slash commands (/model, /persona, /diff, /rollback, /help, /docs, /clear, /test).
4. Side-by-side and inline surgical diff visualization.
"""

import warnings
warnings.filterwarnings("ignore")

import difflib
import json
import os
import sys
import psutil
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

try:
    from k_cli.llm_driver import LLMDriver
    from k_cli.orchestrator import Orchestrator, Persona
    from k_cli.verifier import Verifier
    from k_cli.doc_retriever import DocRetriever
    from k_cli.repo_map import RepoMap
    from k_cli.session import SessionManager
    from k_cli.model_manager import ModelManager, ModelPullResult, MODEL_CATALOG
    from k_cli.persona import DomainPersona, PersonaProfile, PersonaRegistry
    from k_cli.subagents import (
        SubagentDispatcher,
        SubagentVisualizer,
        SubagentTask,
        SubagentRole,
        SubagentRunResult,
        execute_subagents,
    )
    from k_cli.diff_viewer import DiffVisualizer
    from k_cli.workflow import create_plan
    from k_cli.git_guard import GitGuard
    from k_cli.audit import run_audit
    from k_cli.prompting import enhance_prompt, resolve_profile
    from k_cli.security import scan_workspace
    from k_cli.feature import inspect_feature
    from k_cli.rules import load_project_rules
    from k_cli.model_mesh import (
        APIKeyVault,
        ModelIndexEntry,
        ModelMeshResult,
        ModelTarget,
        fetch_global_model_index,
        parse_model_target,
        run_model_mesh,
        search_model_index,
    )
    from k_cli.tui import (
        StatusBar,
        LiveStreamRenderer,
        InteractiveShell,
        SlashCommandHandler,
        MODEL_PRESETS,
        get_persona_style,
    )
except (ModuleNotFoundError, ImportError):
    from llm_driver import LLMDriver
    from orchestrator import Orchestrator, Persona
    from verifier import Verifier
    from doc_retriever import DocRetriever
    from repo_map import RepoMap
    from session import SessionManager
    try:
        from model_manager import ModelManager, ModelPullResult, MODEL_CATALOG
    except (ModuleNotFoundError, ImportError):
        ModelManager = None  # type: ignore
        ModelPullResult = None  # type: ignore
        MODEL_CATALOG = {}  # type: ignore
    try:
        from persona import DomainPersona, PersonaProfile, PersonaRegistry
    except (ModuleNotFoundError, ImportError):
        PersonaRegistry = None
    from subagents import (
        SubagentDispatcher,
        SubagentVisualizer,
        SubagentTask,
        SubagentRole,
        SubagentRunResult,
        execute_subagents,
    )
    from diff_viewer import DiffVisualizer
    from workflow import create_plan
    from git_guard import GitGuard
    from audit import run_audit
    from prompting import enhance_prompt, resolve_profile
    from security import scan_workspace
    from feature import inspect_feature
    from rules import load_project_rules
    from model_mesh import (
        APIKeyVault,
        ModelIndexEntry,
        ModelMeshResult,
        ModelTarget,
        fetch_global_model_index,
        parse_model_target,
        run_model_mesh,
        search_model_index,
    )
    from tui import (
        StatusBar,
        LiveStreamRenderer,
        InteractiveShell,
        SlashCommandHandler,
        MODEL_PRESETS,
        get_persona_style,
    )

app = typer.Typer(
    name="k-cli",
    help="K-CLI: Local, compiler-grounded AI coding agent (< 1GB RAM budget).",
    add_completion=False,
)
console = Console()

ASCII_BANNER = r"""
[bold cyan]
  ██╗  ██╗   ██████╗██╗     ██╗
  ██║ ██╔╝  ██╔════╝██║     ██║
  █████═╝   ██║     ██║     ██║
  ██╔═██╗   ██║     ██║     ██║
  ██║  ██╗  ╚██████╗███████╗██║
  ╚═╝  ╚═╝   ╚═════╝╚══════╝╚═╝
[/bold cyan]
[bold bright_white]PROJECT BANKAI ENGINE v0.2.0 | Flagship Compiler Guard (< 1GB RAM)[/bold bright_white]
[dim]Commands: /model | /persona | /diff | /rollback | /docs | /clear | /test | /help | /exit[/dim]
"""


def print_banner():
    console.print(ASCII_BANNER)


def _resolve_val(val, default):
    """Safely extracts default values if Typer OptionInfo objects are passed directly."""
    if hasattr(val, "default"):
        return val.default
    return val if val is not None else default


def get_persona_color(persona: str) -> str:
    """Returns Rich color string corresponding to persona string or Enum."""
    p_str = str(persona).upper().strip()
    color_map = {
        "RESEARCHER": "cyan",
        "ARCHITECT": "magenta",
        "CODER": "green",
        "CRITIC": "yellow",
        "DEBUGGER": "red",
        "DEVOPS": "cyan",
        "SYSTEMS": "magenta",
        "SECURITY": "red",
        "APPSEC": "red",
        "FRONTEND": "green",
        "DATABASE": "yellow",
        "DEFAULT": "blue",
    }
    for key, color in color_map.items():
        if key in p_str:
            return color
    return "blue"


def compute_diff(initial_code: str, final_code: str) -> str:
    """Calculates unified diff text between candidate code and repaired code."""
    diff_lines = list(
        difflib.unified_diff(
            initial_code.splitlines(keepends=True),
            final_code.splitlines(keepends=True),
            fromfile="candidate_code.py",
            tofile="repaired_code.py",
        )
    )
    return "".join(diff_lines)


def execute_run(
    prompt: str,
    language: str = "python",
    model: str = "qwen2.5-coder:1.5b",
    max_retries: int = 3,
    save_to: Optional[Path] = None,
    mock: bool = False,
    show_banner: bool = True,
    test_file: Optional[Path] = None,
    test_code: Optional[str] = None,
    persona: Optional[str] = None,
    enhance: bool = False,
    rules_file: Optional[Path] = None,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
):
    """Core execution logic for running prompts through persona state machine with live token streaming."""
    language = str(_resolve_val(language, "python"))
    model = str(_resolve_val(model, "qwen2.5-coder:1.5b"))
    max_retries = int(_resolve_val(max_retries, 3))
    mock = bool(_resolve_val(mock, False))
    if not mock and ("PYTEST_CURRENT_TEST" in os.environ and not os.getenv("K_CLI_REAL_LLM")):
        mock = True
    save_to_val = _resolve_val(save_to, None)
    save_to_path = Path(save_to_val) if save_to_val else None
    test_file_val = _resolve_val(test_file, None)
    test_code_val = _resolve_val(test_code, None)
    persona_val = _resolve_val(persona, None)

    resolved_test_code = test_code_val
    if test_file_val is not None:
        tf_path = Path(test_file_val)
        if tf_path.exists():
            resolved_test_code = tf_path.read_text(encoding="utf-8")

    if show_banner:
        print_banner()

    driver = LLMDriver(
        model_name=model,
        mock_mode=mock,
        provider=provider,
        openai_base_url=base_url,
    )
    verifier = Verifier()
    orchestrator = Orchestrator(driver=driver, verifier=verifier, max_retries=max_retries, persona=persona_val)

    initial_ram = orchestrator.get_current_ram_mb()
    driver_type = "ONLINE (Ollama GGUF)" if driver.is_ollama_available() else "LOCAL (llama-cpp-python GGUF)"

    if show_banner:
        table = Table(title="System Environment Status", box=None)
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Active Model", model)
        if orchestrator.active_persona:
            table.add_row("Active Persona", orchestrator.active_persona.title)
        table.add_row("Target Language", language)
        table.add_row("SLM Driver Engine", driver_type)
        table.add_row("Initial RAM Allocation", f"{initial_ram:.2f} MB / 1024 MB")
        console.print(table)
        console.print()

    effective_prompt = enhance_prompt(prompt, model, language) if enhance else prompt
    if rules_file is not None:
        try:
            guidance = load_project_rules(Path.cwd(), rules_file)
        except ValueError as exc:
            console.print(f"[bold red]Invalid project guidance:[/bold red] {exc}")
            raise typer.Exit(code=2)
        if guidance:
            effective_prompt = f"{effective_prompt}\n\n{guidance}"
    console.print(f"[bold yellow]Agent Task:[/bold yellow] [italic]'{prompt}'[/italic]\n")
    if enhance:
        console.print(f"[dim]Prompt adapted for {resolve_profile(model).name}.[/dim]\n")

    current_persona_name = "RESEARCHER"
    current_persona_text = ""

    def make_live_panel() -> Panel:
        ram_mb = orchestrator.get_current_ram_mb()
        color = get_persona_color(current_persona_name)
        title = f"[{color}]Active Persona: [{current_persona_name}][/{color}] | RSS RAM: {ram_mb:.2f} MB / 1024 MB"

        if not current_persona_text:
            content = Text(f"Initializing [{current_persona_name}] persona...", style="dim italic")
        elif current_persona_name in ("CODER", "DEBUGGER") and "```" not in current_persona_text:
            try:
                content = Syntax(current_persona_text, language, theme="monokai", line_numbers=True)
            except Exception:
                content = Text(current_persona_text)
        else:
            content = Text(current_persona_text)

        return Panel(content, title=title, border_style=color)

    with Live(make_live_panel(), console=console, refresh_per_second=15, auto_refresh=True) as live:
        def stream_cb(persona, token: str):
            nonlocal current_persona_name, current_persona_text
            p_name = persona.value if hasattr(persona, "value") else str(persona)
            if p_name != current_persona_name:
                current_persona_name = p_name
                current_persona_text = ""
            current_persona_text += token
            live.update(make_live_panel())

        result = orchestrator.execute_pipeline(
            user_prompt=effective_prompt,
            language=language,
            test_code=resolved_test_code,
            token_stream_callback=stream_cb,
            persona=persona_val,
        )

    # Display Diff Block if retries occurred (Auto-Debug Repair Diff)
    if result.attempts > 1:
        coder_entry = next((h for h in result.history if isinstance(h, dict) and h.get("persona") == Persona.CODER.value), None)
        if coder_entry and coder_entry.get("output"):
            initial_candidate = coder_entry["output"]
            diff_text = compute_diff(initial_candidate, result.final_code)
            if diff_text:
                diff_syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
                diff_panel = Panel(diff_syntax, title=f"[bold yellow]Auto-Debug Repair Diff (Attempt {result.attempts - 1})[/bold yellow]", border_style="yellow")
                console.print(diff_panel)

    # Display Verification Results
    if result.success:
        console.print(f"[bold green]✔ GROUND-TRUTH VERIFIED[/bold green] [dim]({result.verification.verification_type.upper()} guard | Retries: {result.attempts - 1} | RAM: {result.ram_usage_mb:.2f} MB)[/dim]\n")

        if result.architecture_plan:
            plan_panel = Panel(result.architecture_plan.strip(), title="Architecture Plan & Reasoning", border_style="cyan")
            console.print(plan_panel)

        syntax = Syntax(result.final_code, language, theme="monokai", line_numbers=True)
        panel = Panel(syntax, title=f"[bold green]Verified {language.upper()} Implementation[/bold green]", border_style="green")
        console.print(panel)

        if save_to_path:
            save_to_path.write_text(result.final_code, encoding="utf-8")
            console.print(f"\n[bold blue]Saved verified code to:[/bold blue] {save_to_path.resolve()}")

    else:
        console.print(f"[bold red]✘ VERIFICATION FAILED AFTER RETRIES[/bold red] [dim](Line: {result.verification.line_number or 'Unknown'} | RAM: {result.ram_usage_mb:.2f} MB)[/dim]\n")

        err_trace = (result.verification.error_trace if result.verification else None) or "Verification failed."
        err_panel = Panel(err_trace, title="Compiler / Verification Error Trace", border_style="red")
        console.print(err_panel)

        syntax = Syntax(result.final_code, language, theme="monokai", line_numbers=True)
        code_panel = Panel(syntax, title="Unverified Candidate Code", border_style="yellow")
        console.print(code_panel)

        raise typer.Exit(code=1)


@app.command(name="run", help="Generate and verify code for a given prompt.")
def run(
    prompt: str = typer.Argument(..., help="Natural language prompt / coding task description."),
    language: str = typer.Option("python", "--language", "-l", help="Target programming language (python, bash, cpp)."),
    model: str = typer.Option("qwen2.5-coder:1.5b", "--model", "-m", help="Ollama model name."),
    max_retries: int = typer.Option(3, "--retries", "-r", help="Max auto-debug retry attempts."),
    save_to: Optional[Path] = typer.Option(None, "--save-to", "-s", help="File path to save verified code output."),
    mock: bool = typer.Option(False, "--mock", help="Force mock model execution for offline testing."),
    test_file: Optional[Path] = typer.Option(None, "--test-file", "-t", help="Path to test file for verification."),
    test_code: Optional[str] = typer.Option(None, "--test-code", help="Inline test code string for verification."),
    persona: Optional[str] = typer.Option(None, "--persona", "-p", help="Specialized domain persona (devops, debugger, systems, security, frontend, database)."),
    enhance: bool = typer.Option(False, "--enhance", help="Adapt the task to the selected model's strengths."),
    rules_file: Optional[Path] = typer.Option(None, "--rules", help="Optional workspace-contained project guidance file."),
    provider: Optional[str] = typer.Option(None, "--provider", help="Provider name (for example ollama, openai, or openai-compatible)."),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Base URL for an OpenAI-compatible endpoint; use KCLI_API_KEY for its token."),
):
    execute_run(
        prompt=prompt,
        language=language,
        model=model,
        max_retries=max_retries,
        save_to=save_to,
        mock=mock,
        show_banner=True,
        test_file=test_file,
        test_code=test_code,
        persona=persona,
        enhance=enhance,
        rules_file=rules_file,
        provider=provider,
        base_url=base_url,
    )


@app.command(name="prompt", help="Preview a provider-aware prompt without calling a model.")
def prompt_cmd(
    task: str = typer.Argument(..., help="Task to adapt."),
    model: str = typer.Option("qwen2.5-coder:1.5b", "--model", "-m", help="Target model name."),
    language: str = typer.Option("python", "--language", "-l", help="Target language."),
    rules_file: Optional[Path] = typer.Option(None, "--rules", help="Optional workspace-contained project guidance file."),
):
    preview = enhance_prompt(task, model, language)
    if rules_file is not None:
        try:
            guidance = load_project_rules(Path.cwd(), rules_file)
        except ValueError as exc:
            console.print(f"[bold red]Invalid project guidance:[/bold red] {exc}")
            raise typer.Exit(code=2)
        if guidance:
            preview = f"{preview}\n\n{guidance}"
    console.print(Panel(preview, title=f"Prompt preview · {resolve_profile(model).name}", border_style="cyan"))


@app.command(name="audit", help="Generate candidates with multiple models and verify each locally.")
def audit_cmd(
    task: str = typer.Argument(..., help="Implementation task to audit."),
    models: str = typer.Option(..., "--models", "-m", help="Comma-separated model names; use two or more for consensus."),
    language: str = typer.Option("python", "--language", "-l", help="Target language."),
    mock: bool = typer.Option(False, "--mock", help="Use offline mock drivers."),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable audit results."),
):
    selected_models = [item.strip() for item in models.split(",") if item.strip()]
    if not 2 <= len(selected_models) <= 5:
        raise typer.BadParameter("Provide between 2 and 5 distinct model names.", param_hint="--models")
    if len(set(selected_models)) != len(selected_models):
        raise typer.BadParameter("Model names must be distinct.", param_hint="--models")
    result = run_audit(task, selected_models, language=language, mock=mock)
    if as_json:
        payload = {
            "task": task,
            "language": language,
            "consensus_reached": result.consensus_reached,
            "candidates": [
                {
                    "model": candidate.model,
                    "code": candidate.code,
                    "verification": candidate.verification.to_dict(),
                }
                for candidate in result.candidates
            ],
        }
        console.print(json.dumps(payload, indent=2))
        if not result.consensus_reached:
            raise typer.Exit(code=1)
        return

    table = Table(title="Independent model audit", box=None)
    table.add_column("Model", style="cyan")
    table.add_column("Verification")
    table.add_column("Guard")
    for candidate in result.candidates:
        table.add_row(candidate.model, "[green]passed[/green]" if candidate.verification.success else "[red]failed[/red]", candidate.verification.verification_type)
    console.print(table)
    status = "[green]Consensus threshold reached[/green]" if result.consensus_reached else "[yellow]No verified consensus yet — review candidates before applying.[/yellow]"
    console.print(status)


@app.command(name="model-index", help="Fetch web model index and inferred specialties.")
def model_index_cmd(
    query: str = typer.Option("", "--query", "-q", help="Filter by model name/provider/specialty."),
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum results to return."),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable output."),
):
    entries = fetch_global_model_index()
    rows = search_model_index(entries, query=query, limit=limit)
    if as_json:
        payload = [
            {
                "model_id": item.model_id,
                "name": item.name,
                "provider": item.provider,
                "context_length": item.context_length,
                "pricing_summary": item.pricing_summary,
                "specialty": item.specialty,
                "description": item.description,
            }
            for item in rows
        ]
        console.print(json.dumps(payload, indent=2))
        return
    table = Table(title="Global model index", box=None)
    table.add_column("Model", style="cyan")
    table.add_column("Provider")
    table.add_column("Specialty")
    table.add_column("Context")
    table.add_column("Pricing")
    for item in rows:
        table.add_row(
            item.model_id,
            item.provider,
            item.specialty,
            str(item.context_length or "n/a"),
            item.pricing_summary,
        )
    console.print(table)


@app.command(name="mesh", help="Run one prompt concurrently across many model targets.")
def mesh_cmd(
    task: str = typer.Argument(..., help="Task/prompt to run on all models."),
    targets: str = typer.Option(
        ...,
        "--targets",
        "-t",
        help="Comma-separated targets: model | provider:model | provider:model@base_url",
    ),
    max_workers: int = typer.Option(8, "--max-workers", "-w", help="Parallel workers."),
    mock: bool = typer.Option(False, "--mock", help="Use deterministic mock backend."),
    use_vault: bool = typer.Option(True, "--use-vault/--no-vault", help="Load provider keys from secure vault."),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable output."),
):
    parsed_targets = [parse_model_target(item.strip()) for item in targets.split(",") if item.strip()]
    if not parsed_targets:
        raise typer.BadParameter("Provide at least one model target.", param_hint="--targets")
    if use_vault:
        vault = APIKeyVault()
        for provider in {target.provider for target in parsed_targets if target.provider}:
            try:
                vault.export_to_env(provider)  # best effort; env fallback still supported
            except Exception:
                continue

    results = run_model_mesh(task, parsed_targets, mock=mock, max_workers=max_workers)
    verifier = Verifier()
    audited = []
    for result in results:
        verification = verifier.verify(result.output, language="python") if result.success else None
        audited.append((result, verification))

    if as_json:
        payload = [
            {
                "target": {
                    "provider": item.target.provider,
                    "model": item.target.model,
                    "base_url": item.target.base_url,
                },
                "success": item.success,
                "latency_ms": item.latency_ms,
                "error": item.error,
                "verification": verification.to_dict() if verification else None,
            }
            for item, verification in audited
        ]
        console.print(json.dumps(payload, indent=2))
        if any((verification is not None and not verification.success) for _, verification in audited):
            raise typer.Exit(code=1)
        return

    table = Table(title="Concurrent model mesh results", box=None)
    table.add_column("Target", style="cyan")
    table.add_column("Status")
    table.add_column("Latency")
    table.add_column("Verification")
    for item, verification in audited:
        target_name = f"{item.target.provider or 'auto'}:{item.target.model}"
        status = "[green]ok[/green]" if item.success else "[red]error[/red]"
        verification_status = (
            "[green]passed[/green]"
            if verification and verification.success
            else ("[red]failed[/red]" if verification else "[yellow]n/a[/yellow]")
        )
        table.add_row(target_name, status, f"{item.latency_ms} ms", verification_status)
    console.print(table)


@app.command(name="key-set", help="Store a provider API key in secure key vault.")
def key_set_cmd(
    provider: str = typer.Option(..., "--provider", "-p", help="Provider: gemini, anthropic, openai, deepseek, openrouter, openai-compatible."),
    key: str = typer.Option(..., "--key", help="Provider API key to store."),
):
    backend = APIKeyVault().set_key(provider, key)
    console.print(f"[green]Stored key for {provider} using {backend} backend.[/green]")


@app.command(name="feature", help="Collect read-only source and test evidence for a feature claim.")
def feature_cmd(
    query: str = typer.Argument(..., help="Feature or capability to look for."),
    root_dir: Path = typer.Option(Path("."), "--dir", "-d", help="Workspace root directory."),
    require_tests: bool = typer.Option(False, "--require-tests", help="Fail unless matching test evidence is found."),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable evidence."),
):
    """Check whether a requested capability has implementation and supporting evidence."""
    evidence = inspect_feature(query, root_dir)
    if as_json:
        console.print(json.dumps(evidence.to_dict(), indent=2))
    else:
        table = Table(title="K-CLI Feature Evidence", box=None)
        table.add_column("Evidence", style="cyan")
        table.add_column("Count", style="bold white")
        table.add_row("Source matches", str(len(evidence.source_matches)))
        table.add_row("Test matches", str(len(evidence.test_matches)))
        table.add_row("Symbol matches", str(len(evidence.symbol_matches)))
        table.add_row("Status", "[green]PROVEN[/green]" if evidence.proven else "[yellow]INCONCLUSIVE[/yellow]")
        console.print(table)
        for match in (evidence.source_matches + evidence.test_matches + evidence.symbol_matches)[:15]:
            console.print(f"[dim]{match.category} {match.path}:{match.line}[/dim] {match.evidence}")
    if not evidence.proven or (require_tests and not evidence.test_matches):
        raise typer.Exit(code=1)


def execute_subagents_run(
    prompt: str,
    model: str = "qwen2.5-coder:1.5b",
    max_workers: int = 4,
    save_to: Optional[Path] = None,
    mock: bool = False,
    show_banner: bool = True,
    no_ui: bool = False,
    context_files: Optional[List[str]] = None,
):
    """Core execution logic for decomposing prompts into parallel subagent workers."""
    model = str(_resolve_val(model, "qwen2.5-coder:1.5b"))
    max_workers = int(_resolve_val(max_workers, 4))
    mock = bool(_resolve_val(mock, False))
    if not mock and ("PYTEST_CURRENT_TEST" in os.environ and not os.getenv("K_CLI_REAL_LLM")):
        mock = True
    save_to_val = _resolve_val(save_to, None)
    save_to_path = Path(save_to_val) if save_to_val else None

    if show_banner:
        print_banner()

    driver = LLMDriver(model_name=model, mock_mode=mock)
    verifier = Verifier()
    dispatcher = SubagentDispatcher(
        driver=driver,
        verifier=verifier,
        max_workers=max_workers,
    )

    initial_ram = psutil.Process().memory_info().rss / (1024 * 1024)
    driver_type = "ONLINE (Ollama GGUF)" if driver.is_ollama_available() else "LOCAL (llama-cpp-python GGUF)"

    if show_banner:
        table = Table(title="Multi-Agent System Environment", box=None)
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Active Model", model)
        table.add_row("Max Parallel Workers", str(max_workers))
        table.add_row("SLM Driver Engine", driver_type)
        table.add_row("Initial RAM Allocation", f"{initial_ram:.2f} MB / 1024 MB")
        console.print(table)
        console.print()

    console.print(f"[bold yellow]Multi-Agent Task:[/bold yellow] [italic]'{prompt}'[/italic]\n")

    tasks = dispatcher.decomposer.decompose(
        prompt=prompt,
        context_files=context_files,
    )

    # Display planned task hierarchy
    tree = SubagentVisualizer.render_tree(tasks, title=f"Planned Subagent Tree ({len(tasks)} tasks)")
    console.print(tree)
    console.print()

    if no_ui:
        result = dispatcher.dispatch(tasks=tasks)
    else:
        result = SubagentVisualizer.execute_with_live_cli(
            dispatcher=dispatcher,
            tasks=tasks,
            console=console,
        )

    console.print()
    if result.success:
        console.print(f"[bold green]✔ MULTI-AGENT TASK COMPLETED SUCCESSFULLY[/bold green] [dim](Tasks: {len(result.tasks)} | Duration: {result.total_duration_sec:.2f}s | RAM: {result.total_ram_mb:.2f} MB)[/dim]\n")

        # Display Final Patch or Code
        if result.aggregated_patch:
            syntax = Syntax(result.aggregated_patch, "diff", theme="monokai", line_numbers=False)
            panel = Panel(syntax, title="[bold green]Unified Aggregated Patch[/bold green]", border_style="green")
            console.print(panel)
        elif result.final_code:
            syntax = Syntax(result.final_code, "python", theme="monokai", line_numbers=True)
            panel = Panel(syntax, title="[bold green]Verified Implementation Code[/bold green]", border_style="green")
            console.print(panel)

        if save_to_path:
            out_content = result.aggregated_patch if result.aggregated_patch else result.final_code
            save_to_path.write_text(out_content, encoding="utf-8")
            console.print(f"\n[bold blue]Saved output to:[/bold blue] {save_to_path.resolve()}")

        return result

    else:
        console.print(f"[bold red]✘ SUBAGENTS PIPELINE FAILED[/bold red] [dim](Duration: {result.total_duration_sec:.2f}s | RAM: {result.total_ram_mb:.2f} MB)[/dim]\n")
        if result.verification and not result.verification.success:
            err_trace = result.verification.error_trace or "Verification failed."
            console.print(Panel(err_trace, title="Compiler / Verification Error Trace", border_style="red"))

        if result.final_code:
            syntax = Syntax(result.final_code, "python", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Unverified Candidate Output", border_style="yellow"))

        raise typer.Exit(code=1)


@app.command(name="subagents", help="Decompose complex prompt into parallel subagents (Explorer, Researcher, Refactorer, Tester).")
def subagents_cmd(
    prompt: str = typer.Argument(..., help="Complex user prompt or coding task."),
    model: str = typer.Option("qwen2.5-coder:1.5b", "--model", "-m", help="Ollama model name."),
    max_workers: int = typer.Option(4, "--workers", "-w", help="Max parallel subagent workers."),
    save_to: Optional[Path] = typer.Option(None, "--save-to", "-s", help="File path to save verified patch or code."),
    mock: bool = typer.Option(False, "--mock", help="Force mock model execution for offline testing."),
    no_ui: bool = typer.Option(False, "--no-ui", help="Disable live Rich CLI visualization."),
):
    execute_subagents_run(
        prompt=prompt,
        model=model,
        max_workers=max_workers,
        save_to=save_to,
        mock=mock,
        show_banner=True,
        no_ui=no_ui,
    )


@app.command(name="spawn", help="Alias for subagents: Decompose and execute prompt with parallel subagents.")
def spawn_cmd(
    prompt: str = typer.Argument(..., help="Complex user prompt or coding task."),
    model: str = typer.Option("qwen2.5-coder:1.5b", "--model", "-m", help="Ollama model name."),
    max_workers: int = typer.Option(4, "--workers", "-w", help="Max parallel subagent workers."),
    save_to: Optional[Path] = typer.Option(None, "--save-to", "-s", help="File path to save verified patch or code."),
    mock: bool = typer.Option(False, "--mock", help="Force mock model execution for offline testing."),
    no_ui: bool = typer.Option(False, "--no-ui", help="Disable live Rich CLI visualization."),
):
    execute_subagents_run(
        prompt=prompt,
        model=model,
        max_workers=max_workers,
        save_to=save_to,
        mock=mock,
        show_banner=True,
        no_ui=no_ui,
    )


@app.command(name="verify", help="Run standalone ground-truth verification on a local code file or inline code string.")
def verify(
    file_path: Optional[Path] = typer.Argument(None, help="Path to code file to verify."),
    code: Optional[str] = typer.Option(None, "--code", "-c", help="Inline code string to verify."),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Language override."),
    test_file: Optional[Path] = typer.Option(None, "--test-file", "-t", help="Path to test file for pytest verification."),
    test_code: Optional[str] = typer.Option(None, "--test-code", help="Inline test code string for pytest verification."),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable verification results."),
):
    if not as_json:
        print_banner()

    file_path_val = _resolve_val(file_path, None)
    code_val = _resolve_val(code, None)
    lang_val = _resolve_val(language, None)
    test_file_val = _resolve_val(test_file, None)
    test_code_val = _resolve_val(test_code, None)

    if file_path_val is None and not code_val:
        console.print("[bold red]Error:[/bold red] Must specify a file path or code string to verify.")
        raise typer.Exit(code=1)

    resolved_code = ""
    display_target = ""
    default_lang = "python"

    if file_path_val is not None:
        fp = Path(file_path_val)
        if not fp.exists():
            console.print(f"[bold red]Error:[/bold red] File '{fp}' does not exist.")
            raise typer.Exit(code=1)
        resolved_code = fp.read_text(encoding="utf-8")
        display_target = fp.name
        ext = fp.suffix.lstrip(".").lower()
        default_lang = "python" if ext in ("py", "python") else "bash" if ext in ("sh", "bash") else "cpp" if ext in ("cpp", "cxx", "cc") else "python"
    else:
        resolved_code = code_val
        display_target = "inline code"

    lang = lang_val or default_lang

    resolved_test_code = test_code_val
    if test_file_val is not None:
        tf_path = Path(test_file_val)
        if tf_path.exists():
            resolved_test_code = tf_path.read_text(encoding="utf-8")

    verifier = Verifier()
    result = verifier.verify(resolved_code, language=lang, test_code=resolved_test_code)

    if as_json:
        payload = result.to_dict()
        payload["target"] = display_target
        console.print(json.dumps(payload, indent=2))
        if not result.success:
            raise typer.Exit(code=1)
        return

    if result.success:
        console.print(f"[bold green]✔ File '{display_target}' passed ground-truth {result.verification_type} verification![/bold green]")
    else:
        console.print(f"[bold red]✘ File '{display_target}' failed verification at line {result.line_number or 'unknown'}.[/bold red]\n")
        err_trace = result.error_trace or "Verification failed."
        console.print(Panel(err_trace, title="Compiler / Verification Error Trace", border_style="red"))
        raise typer.Exit(code=1)


@app.command(name="status", help="Check K-CLI active system RAM budget, model diagnostics, and git branch.")
def status():
    print_banner()
    driver = LLMDriver()
    orchestrator = Orchestrator(driver=driver)
    session = SessionManager(model_name=driver.model_name)

    ram_mb = orchestrator.get_current_ram_mb()
    ollama_ok = driver.is_ollama_available()

    table = Table(title="K-CLI System Diagnostics", box=None)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="bold white")
    table.add_row("Active Model", driver.model_name)
    table.add_row("Git Branch", session.get_git_branch())
    table.add_row("Active Persona", session.active_persona)
    table.add_row("Memory RSS Allocation", f"{ram_mb:.2f} MB / 1024 MB (Budget Limit)")
    table.add_row("SLM Driver Engine", "[green]ONLINE (Ollama GGUF)[/green]" if ollama_ok else "[yellow]LOCAL (llama-cpp-python GGUF)[/yellow]")
    table.add_row("Default Model", driver.model_name)
    table.add_row("Python Environment", sys.version.split()[0])
    console.print(table)


@app.command(name="plan", help="Create a protected, read-only implementation plan for a workspace.")
def plan_cmd(
    goal: str = typer.Argument(..., help="Outcome to plan; no project files are changed."),
    root_dir: Path = typer.Option(Path("."), "--dir", "-d", help="Workspace to inspect."),
    rules_file: Optional[Path] = typer.Option(None, "--rules", help="Optional workspace-contained project guidance file."),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable plan data."),
):
    """Inspect a workspace and print an implementation plan without editing anything."""
    result = create_plan(goal, root_dir)
    if rules_file is not None:
        try:
            result.project_guidance = load_project_rules(root_dir, rules_file)
        except ValueError as exc:
            console.print(f"[bold red]Invalid project guidance:[/bold red] {exc}")
            raise typer.Exit(code=2)
    if as_json:
        sys.stdout.write(json.dumps({
            "goal": result.goal,
            "workspace": str(result.workspace),
            "relevant_files": result.relevant_files,
            "detected_tools": result.detected_tools,
            "repo_map": result.repo_map,
            "project_guidance": result.project_guidance,
            "read_only": True,
        }, indent=2) + "\n")
    else:
        console.print(result.render_markdown())


@app.command(name="doctor", help="Check install, workspace, model, and safety prerequisites.")
def doctor_cmd(
    root_dir: Path = typer.Option(Path("."), "--dir", "-d", help="Workspace to diagnose."),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable diagnostics."),
):
    """Print actionable diagnostics without downloading models or changing project files."""
    root = root_dir.resolve()
    driver = LLMDriver()
    findings = scan_workspace(root)
    checks = [
        ("Workspace", str(root), root.exists()),
        ("Python", sys.version.split()[0], sys.version_info >= (3, 11)),
        ("Git repository", "detected" if GitGuard(root).is_git_repo() else "not detected", GitGuard(root).is_git_repo()),
        ("Ollama", "reachable" if driver.is_ollama_available() else "not reachable (mock mode still works)", driver.is_ollama_available()),
        ("KCLI_MOCK_MODE", os.getenv("KCLI_MOCK_MODE", "not set"), True),
        ("Secret hygiene", "no obvious committed credentials" if not findings else f"{len(findings)} potential credential(s) found", not findings),
    ]
    if as_json:
        payload = {
            "workspace": str(root),
            "checks": [
                {"name": label, "detail": detail, "passed": passed}
                for label, detail, passed in checks
            ],
            "findings": [
                {"rule": finding.rule, "path": str(finding.path), "line": finding.line}
                for finding in findings
            ],
            "ready": all(passed for _, _, passed in checks),
        }
        console.print(json.dumps(payload, indent=2))
        if not payload["ready"]:
            raise typer.Exit(code=1)
        return

    table = Table(title="K-CLI Doctor", box=None)
    table.add_column("Check", style="cyan")
    table.add_column("Result")
    table.add_column("Status")
    for label, detail, passed in checks:
        table.add_row(label, detail, "[green]ready[/green]" if passed else "[yellow]attention[/yellow]")
    console.print(table)
    for finding in findings:
        console.print(f"[yellow]Potential {finding.rule}: {finding.path}:{finding.line} (value intentionally hidden)[/yellow]")


@app.command(name="ui", help="Launch the full-screen K-CLI Textual workstation.")
def ui_cmd(
    model: str = typer.Option("Bankai-7B", "--model", "-m", help="Active model label."),
    persona: str = typer.Option("Fullstack AI Systems Engineer", "--persona", "-p", help="Active persona label."),
    mock: bool = typer.Option(False, "--mock", help="Use the offline mock driver."),
    workspace: Path = typer.Option(Path("."), "--workspace", "-w", help="Workspace root."),
):
    """Launch the polished Textual UI without changing the caller's workspace."""
    try:
        from k_cli.tui_app import KCliApp
    except ModuleNotFoundError:
        from tui_app import KCliApp
    KCliApp(workspace_dir=str(workspace), model_name=model, persona=persona, mock_mode=mock).run()


@app.command(name="tui", help="Alias for launching the full-screen K-CLI Textual workstation.")
def tui_cmd(
    model: str = typer.Option("Bankai-7B", "--model", "-m", help="Active model label."),
    persona: str = typer.Option("Fullstack AI Systems Engineer", "--persona", "-p", help="Active persona label."),
    mock: bool = typer.Option(False, "--mock", help="Use the offline mock driver."),
    workspace: Path = typer.Option(Path("."), "--workspace", "-w", help="Workspace root."),
):
    """Launch the polished Textual UI workstation."""
    ui_cmd(model=model, persona=persona, mock=mock, workspace=workspace)


@app.command(name="diff", help="View active uncommitted git diff or side-by-side diff.")
def diff_cmd(
    side_by_side: bool = typer.Option(False, "--side-by-side", "--sbs", "-s", help="Render side-by-side 2-column diff."),
):
    """Renders workspace git diff in inline or side-by-side format."""
    session = SessionManager()
    if not session.git_guard.is_git_repo():
        console.print("[yellow]Not inside a Git repository.[/yellow]")
        return

    diff_text = session.git_guard.get_diff()
    if not diff_text.strip():
        console.print("[dim]Working tree is clean; no uncommitted changes.[/dim]")
        return

    panel = DiffVisualizer.render_inline_diff(diff_text, title="Git Working Tree Diff")
    console.print(panel)


@app.command(name="review", help="Review changed source files without modifying the workspace.")
def review_cmd(
    root_dir: Path = typer.Option(Path("."), "--dir", "-d", help="Workspace or Git repository root."),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable review results."),
):
    """Run read-only syntax checks over changed Python files and summarize the diff."""
    root = root_dir.resolve()
    guard = GitGuard(root)
    if not guard.is_git_repo():
        payload = {
            "workspace": str(root),
            "git_repository": False,
            "changed_files": [],
            "syntax_failures": [],
            "status": "not-a-git-repository",
        }
        if as_json:
            console.print(json.dumps(payload, indent=2))
        else:
            console.print("[yellow]Review requires a Git repository; no files were inspected.[/yellow]")
        raise typer.Exit(code=2)

    status = guard._run_git(["status", "--porcelain"])
    changed_files: List[str] = []
    if status.returncode == 0:
        for line in status.stdout.splitlines():
            if len(line) >= 4:
                changed_files.append(line[3:].strip().strip('"'))

    verifier = Verifier()
    failures = []
    checked = []
    for relative in changed_files:
        path = root / relative
        if path.suffix.lower() != ".py" or not path.is_file():
            continue
        try:
            code = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            failures.append({"file": relative, "error": str(error)})
            continue
        checked.append(relative)
        result = verifier.verify_python_ast(code)
        if not result.success:
            failures.append({"file": relative, "line": result.line_number, "error": result.error_trace})

    payload = {
        "workspace": str(root),
        "git_repository": True,
        "changed_files": changed_files,
        "python_files_checked": checked,
        "syntax_failures": failures,
        "status": "failed" if failures else "passed",
    }
    if as_json:
        console.print(json.dumps(payload, indent=2))
    else:
        table = Table(title="K-CLI Read-Only Review", box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold white")
        table.add_row("Changed files", str(len(changed_files)))
        table.add_row("Python files checked", str(len(checked)))
        table.add_row("Syntax failures", str(len(failures)))
        console.print(table)
        for failure in failures:
            console.print(
                f"[red]✘ {failure['file']}:{failure.get('line') or 'unknown'} "
                f"{failure['error']}[/red]"
            )
        if not failures:
            console.print("[green]✔ Changed Python files passed AST review.[/green]")
    if failures:
        raise typer.Exit(code=1)


@app.command(name="test", help="Run ground-truth compiler and pytest verification.")
def test_cmd(
    target: Optional[str] = typer.Argument(None, help="Target file or test code to verify."),
):
    """Runs ground-truth verification on target file or workspace."""
    session = SessionManager()
    passed, summary = session.run_test(target)
    if passed:
        console.print(f"[bold green]{summary}[/bold green]")
    else:
        console.print(f"[bold red]{summary}[/bold red]")
        raise typer.Exit(code=1)


@app.command(name="doc", help="Search offline DevDocs SQLite database for API signatures.")
def doc(
    query: str = typer.Argument(..., help="Query string or API symbol name."),
    limit: int = typer.Option(3, "--limit", "-n", help="Max number of results to return."),
    max_tokens: int = typer.Option(250, "--max-tokens", "-t", help="Max tokens budget for context."),
    db_path: Optional[Path] = typer.Option(None, "--db", help="Path to SQLite docs database."),
):
    """Searches DevDocs FTS5 offline database for function and class signatures."""
    retriever = DocRetriever(db_path=str(db_path) if db_path else None)
    results = retriever.search(query, limit=limit, max_tokens=max_tokens)
    if not results:
        console.print(f"[yellow]No documentation found for '{query}'.[/yellow]")
        raise typer.Exit(code=2)

    console.print(f"[bold cyan]DevDocs search results for '{query}':[/bold cyan]\n")
    for r in results:
        name = r.get("name", "")
        sig = r.get("signature", "")
        doc_str = r.get("doc", "")
        module = r.get("module", "")
        panel_content = f"[bold green]{sig}[/bold green]\n\n[dim]{doc_str}[/dim]"
        console.print(Panel(panel_content, title=f"Module: {module} | Symbol: {name}", border_style="cyan"))


@app.command(name="map", help="Display AST codebase repository map for the workspace.")
def map_cmd(
    root_dir: Path = typer.Option(Path("."), "--dir", "-d", help="Workspace root directory."),
    max_tokens: int = typer.Option(400, "--max-tokens", "-t", help="Max tokens budget for map."),
    focus: Optional[List[str]] = typer.Option(None, "--focus", "-f", help="Files to prioritize."),
):
    """Generates and displays AST symbol tree for the workspace."""
    repo_map = RepoMap(root_dir=str(root_dir))
    tree_text = repo_map.get_repo_map(max_tokens=max_tokens, focus_files=focus)
    if not tree_text.strip():
        console.print("[yellow]Repository map is empty (no valid Python files found).[/yellow]")
        return

    syntax = Syntax(tree_text, "python", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title="AST Codebase Repository Map", border_style="magenta"))


@app.command(name="init", help="Initialize K-CLI environment, verify Ollama health, and bootstrap Bankai models.")
def init_cmd(
    model: str = typer.Option("bankai-7b", "--model", "-m", help="Target Bankai model identifier (e.g. bankai-7b, bankai-10b)."),
    ollama_url: str = typer.Option("http://localhost:11434", "--ollama-url", help="Ollama daemon URL."),
    no_pull: bool = typer.Option(False, "--no-pull", help="Skip downloading/pulling model weights from Hugging Face Hub."),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-download and re-creation even if cached."),
    mock: bool = typer.Option(False, "--mock", help="Force mock execution for offline testing."),
):
    """Initializes local K-CLI directory layout, checks Ollama status, and provisions default Bankai models."""
    print_banner()
    console.print("[bold cyan]⚡ Initializing K-CLI Environment & Bootstrapping Bankai Models...[/bold cyan]\n")

    mock_mode = bool(_resolve_val(mock, False))
    if not mock_mode and ("PYTEST_CURRENT_TEST" in os.environ and not os.getenv("K_CLI_REAL_LLM")):
        mock_mode = True

    model_val = str(_resolve_val(model, "bankai-7b"))
    ollama_url_val = str(_resolve_val(ollama_url, "http://localhost:11434"))
    no_pull_val = bool(_resolve_val(no_pull, False))
    force_val = bool(_resolve_val(force, False))

    manager = ModelManager(ollama_url=ollama_url_val, mock_mode=mock_mode) if ModelManager else None
    if manager is None:
        console.print("[bold red]Error:[/bold red] ModelManager module could not be loaded.")
        raise typer.Exit(code=1)

    init_res = manager.init_environment(
        default_model=model_val,
        sync_model=not no_pull_val,
        force=force_val,
    )

    # 1. Directory Hierarchy
    table = Table(title="K-CLI Environment Directory Layout", box=None)
    table.add_column("Directory", style="cyan")
    table.add_column("Status", style="green")
    for d in init_res.get("directories", []):
        table.add_row(d, "✔ Ready")
    console.print(table)
    console.print()

    # 2. Ollama Diagnostics
    ollama_stat = init_res.get("ollama", {})
    ollama_ok = ollama_stat.get("healthy", False)
    ollama_table = Table(title="Local Ollama Inference Diagnostics", box=None)
    ollama_table.add_column("Property", style="cyan")
    ollama_table.add_column("Value", style="magenta")
    ollama_table.add_row("Ollama Host", ollama_stat.get("url", ollama_url_val))
    ollama_table.add_row("Daemon Status", "[bold green]ONLINE (Healthy)[/bold green]" if ollama_ok else "[bold yellow]OFFLINE / Unreachable[/bold yellow]")
    ollama_table.add_row("Ollama Version", str(ollama_stat.get("version", "unknown")))
    models_list = ", ".join(ollama_stat.get("models", [])) or "None loaded"
    ollama_table.add_row("Loaded Models", models_list)
    console.print(ollama_table)
    console.print()

    # 3. Model Pull & Ollama Registration Status
    pull_info = init_res.get("model_pull")
    if pull_info:
        p_table = Table(title="Bankai Model Bootstrapper Status", box=None)
        p_table.add_column("Attribute", style="cyan")
        p_table.add_column("Details", style="bold white")
        p_table.add_row("Target Model", pull_info.get("model_name", model_val))
        p_table.add_row("Ollama Tag", pull_info.get("ollama_tag", model_val))
        p_table.add_row("Local GGUF Path", str(pull_info.get("gguf_path") or "None"))
        p_table.add_row("Modelfile Path", str(pull_info.get("modelfile_path") or "None"))
        sha_str = pull_info.get("sha256") or "N/A"
        sha_status = "[bold green]✔ Verified[/bold green]" if pull_info.get("sha256_verified") else "[yellow]Unverified[/yellow]"
        p_table.add_row("SHA256 Integrity", f"{sha_str[:20]}... ({sha_status})")
        ollama_created = "[bold green]✔ Registered in Ollama[/bold green]" if pull_info.get("ollama_created") else "[yellow]Pending (Ollama offline)[/yellow]"
        p_table.add_row("Ollama Deployment", ollama_created)
        console.print(p_table)
        console.print()

    if init_res.get("ready"):
        console.print(Panel(
            f"[bold green]✔ Project Bankai Engine initialized successfully![/bold green]\n\n"
            f"• Active Model: [bold cyan]{model_val}[/bold cyan]\n"
            f"• Quick Run: [italic]k run 'write a binary search in python'[/italic]\n"
            f"• Interactive Shell: [italic]k[/italic]",
            title="[bold green]K-CLI Ready[/bold green]",
            border_style="green",
        ))
    else:
        console.print(Panel(
            "[yellow]⚠ K-CLI directories initialized. To run with local Ollama, start the Ollama daemon and run [bold]k pull-model[/bold].[/yellow]",
            title="[bold yellow]Setup Notice[/bold yellow]",
            border_style="yellow",
        ))


@app.command(name="pull-model", help="Pull Bankai model from Hugging Face Hub into Ollama or local GGUF cache.")
def pull_model_cmd(
    model: str = typer.Argument("bankai-7b", help="Model identifier (e.g. bankai-7b, bankai-10b, krishivjoshi/bankai-7b)."),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Ollama model tag to register (e.g. bankai:7b, bankai-7b)."),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Hugging Face repository ID override."),
    quant: str = typer.Option("q4_k_m", "--quant", "-q", help="Quantization format to target (default: q4_k_m)."),
    verify_sha: bool = typer.Option(True, "--verify-sha/--no-verify-sha", help="Cryptographically verify SHA256 integrity."),
    sha256: Optional[str] = typer.Option(None, "--sha256", help="Expected SHA256 checksum string."),
    ollama_url: str = typer.Option("http://localhost:11434", "--ollama-url", help="Ollama host URL."),
    no_ollama: bool = typer.Option(False, "--no-ollama", help="Skip Ollama model creation (cache GGUF only)."),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-download even if cached."),
    mock: bool = typer.Option(False, "--mock", help="Force mock execution for offline testing."),
):
    """Pulls Bankai GGUF model directly from Hugging Face Hub, verifies SHA256 integrity, and registers in Ollama."""
    print_banner()

    mock_mode = bool(_resolve_val(mock, False))
    if not mock_mode and ("PYTEST_CURRENT_TEST" in os.environ and not os.getenv("K_CLI_REAL_LLM")):
        mock_mode = True

    model_val = str(_resolve_val(model, "bankai-7b"))
    tag_val = _resolve_val(tag, None)
    repo_val = _resolve_val(repo, None)
    quant_val = str(_resolve_val(quant, "q4_k_m"))
    verify_sha_val = bool(_resolve_val(verify_sha, True))
    sha256_val = _resolve_val(sha256, None)
    ollama_url_val = str(_resolve_val(ollama_url, "http://localhost:11434"))
    no_ollama_val = bool(_resolve_val(no_ollama, False))
    force_val = bool(_resolve_val(force, False))

    console.print(f"[bold cyan]🚀 Project Bankai Auto-Sync Engine: Pulling model '{model_val}'...[/bold cyan]\n")

    manager = ModelManager(ollama_url=ollama_url_val, mock_mode=mock_mode) if ModelManager else None
    if manager is None:
        console.print("[bold red]Error:[/bold red] ModelManager module could not be loaded.")
        raise typer.Exit(code=1)

    result = manager.pull_model(
        model_identifier=model_val,
        ollama_tag=tag_val,
        hf_repo=repo_val,
        force=force_val,
        verify_sha=verify_sha_val,
        create_in_ollama=not no_ollama_val,
        expected_sha256=sha256_val,
        quant=quant_val,
    )

    # Render Result Table
    table = Table(title=f"Model Pull & Ollama Deployment Report: {model_val}", box=None)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="bold white")
    table.add_row("Model Identifier", result.model_name)
    table.add_row("Target Ollama Tag", result.ollama_tag)
    table.add_row("Hugging Face Source", result.details.get("repo_id", f"krishivjoshi/{model_val}"))
    table.add_row("Local GGUF Path", str(result.gguf_path) if result.gguf_path else "[red]None[/red]")
    table.add_row("Modelfile Generated", str(result.modelfile_path) if result.modelfile_path else "[yellow]None[/yellow]")

    sha_text = result.sha256 or "N/A"
    if result.sha256_verified:
        sha_display = f"{sha_text[:20]}... [bold green]✔ SHA256 Verified[/bold green]"
    else:
        sha_display = f"{sha_text[:20]}... [bold red]✘ Verification Failed[/bold red]"
    table.add_row("SHA256 Integrity", sha_display)

    if not no_ollama_val:
        if result.ollama_created:
            table.add_row("Ollama Registration", f"[bold green]✔ Created '{result.ollama_tag}'[/bold green]")
        elif not result.ollama_healthy:
            table.add_row("Ollama Registration", f"[yellow]⚠ Ollama daemon offline at {ollama_url_val}[/yellow]")
        else:
            table.add_row("Ollama Registration", f"[red]✘ Failed to create model in Ollama[/red]")
    else:
        table.add_row("Ollama Registration", "[dim]Skipped (--no-ollama)[/dim]")

    console.print(table)
    console.print()

    if result.success:
        console.print(f"[bold green]✔ SUCCESS: Model '{model_val}' is ready for local compiler-grounded inference.[/bold green]\n")
    else:
        console.print(f"[bold red]✘ PULL FAILED: {result.message}[/bold red]\n")
        raise typer.Exit(code=1)


@app.command(name="pull", help="Alias for pull-model command.")
def pull_cmd(
    model: str = typer.Argument("bankai-7b", help="Model identifier (e.g. bankai-7b, bankai-10b, krishivjoshi/bankai-7b)."),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Ollama model tag to register (e.g. bankai:7b, bankai-7b)."),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Hugging Face repository ID override."),
    quant: str = typer.Option("q4_k_m", "--quant", "-q", help="Quantization format to target (default: q4_k_m)."),
    verify_sha: bool = typer.Option(True, "--verify-sha/--no-verify-sha", help="Cryptographically verify SHA256 integrity."),
    sha256: Optional[str] = typer.Option(None, "--sha256", help="Expected SHA256 checksum string."),
    ollama_url: str = typer.Option("http://localhost:11434", "--ollama-url", help="Ollama host URL."),
    no_ollama: bool = typer.Option(False, "--no-ollama", help="Skip Ollama model creation (cache GGUF only)."),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-download even if cached."),
    mock: bool = typer.Option(False, "--mock", help="Force mock execution for offline testing."),
):
    """Alias for pull-model command."""
    pull_model_cmd(
        model=model,
        tag=tag,
        repo=repo,
        quant=quant,
        verify_sha=verify_sha,
        sha256=sha256,
        ollama_url=ollama_url,
        no_ollama=no_ollama,
        force=force,
        mock=mock,
    )


def interactive_mode(model: str = "qwen2.5-coder:1.5b", mock: bool = False):
    """Interactive multi-turn prompt shell when typing 'k' without arguments."""
    session = SessionManager(workspace_dir=".", model_name=model, mock_mode=mock)
    print_banner()
    console.print("[bold cyan]K-CLI Interactive Shell ready. Type /help for slash commands or /exit to quit.[/bold cyan]\n")

    shell = InteractiveShell(session=session, console=console)
    shell.run()


@app.callback(
    invoke_without_command=True,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
def main(
    ctx: typer.Context,
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Prompt text if running main entrypoint directly."),
):
    if ctx.invoked_subcommand is None:
        if prompt:
            execute_run(prompt=prompt, show_banner=True)
            raise typer.Exit()
        elif ctx.args:
            prompt_arg = " ".join(ctx.args)
            execute_run(prompt=prompt_arg, show_banner=True)
            raise typer.Exit()
        else:
            interactive_mode()


if __name__ == "__main__":
    app()
