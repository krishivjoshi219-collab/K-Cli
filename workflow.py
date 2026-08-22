"""Read-only planning helpers for K-CLI's protected plan workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

try:
    from k_cli.repo_map import RepoMap
except ModuleNotFoundError:
    from repo_map import RepoMap

try:
    from k_cli.dedup_engine import DedupEngine, DedupMatch
except ModuleNotFoundError:
    try:
        from dedup_engine import DedupEngine, DedupMatch
    except ModuleNotFoundError:
        DedupEngine = None  # type: ignore
        DedupMatch = None  # type: ignore


IGNORED_DIRS = {".git", ".venv", "venv", "k_cli_env", "node_modules", "__pycache__", ".pytest_cache", "data"}


@dataclass
class PlanResult:
    goal: str
    workspace: Path
    relevant_files: List[str]
    detected_tools: List[str]
    repo_map: str
    project_guidance: str = ""
    dedup_warning: Optional[str] = None
    dedup_match: Optional[Any] = None

    def render_markdown(self) -> str:
        files = "\n".join(f"- `{path}`" for path in self.relevant_files) or "- No source files matched yet."
        tools = ", ".join(self.detected_tools) or "No project test command detected"
        steps = [
            "Inspect the listed files and existing tests before changing behaviour.",
            "Make the smallest coherent implementation, keeping generated changes reviewable.",
            "Run the detected verification command and show the resulting diff for review.",
        ]
        step_text = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1))
        guidance = (
            f"```text\n{self.project_guidance}\n```"
            if self.project_guidance
            else "No project guidance file was supplied."
        )
        warning_section = ""
        if self.dedup_warning:
            warning_section = f"## Deduplication warning\n> [!WARNING]\n> {self.dedup_warning}\n\n"
        return (
            f"# K-CLI protected plan\n\n"
            f"**Goal:** {self.goal}\n\n"
            f"**Workspace:** `{self.workspace}`\n\n"
            f"{warning_section}"
            f"## Relevant files\n{files}\n\n"
            f"## Detected verification\n{tools}\n\n"
            f"## Proposed steps\n{step_text}\n\n"
            f"## Project guidance\n{guidance}\n\n"
            f"## Repository map\n```text\n{self.repo_map or 'No Python symbols discovered.'}\n```\n\n"
            "Plan mode is read-only: it never edits project files or runs mutating commands."
        )


def _detected_tools(workspace: Path) -> List[str]:
    tools: List[str] = []
    if (workspace / "pyproject.toml").exists() or (workspace / "pytest.ini").exists():
        tools.append("pytest")
    if (workspace / "package.json").exists():
        tools.append("npm test")
    if (workspace / "Cargo.toml").exists():
        tools.append("cargo test")
    if (workspace / "go.mod").exists():
        tools.append("go test ./...")
    return tools


def create_plan(goal: str, workspace_dir: str | Path = ".", max_files: int = 10) -> PlanResult:
    """Create a concise, read-only implementation plan from local workspace evidence."""
    workspace = Path(workspace_dir).resolve()
    candidates: List[str] = []
    query_terms = {term.lower() for term in goal.replace("/", " ").replace("_", " ").split() if len(term) > 2}
    for path in workspace.rglob("*"):
        if len(candidates) >= max_files:
            break
        if not path.is_file() or any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix not in {".py", ".md", ".toml", ".json", ".yml", ".yaml"}:
            continue
        relative = path.relative_to(workspace).as_posix()
        if not query_terms or any(term in relative.lower() for term in query_terms):
            candidates.append(relative)
    if not candidates:
        candidates = [p.relative_to(workspace).as_posix() for p in workspace.glob("*.py")][:max_files]
    repo_map = RepoMap(root_dir=str(workspace)).get_repo_map(max_tokens=260, focus_files=candidates)

    dedup_warning = None
    dedup_match = None
    if DedupEngine is not None:
        try:
            engine = DedupEngine(repo_path=str(workspace))
            d_match = engine.scan_for_duplicate(query=goal)
            if d_match and d_match.is_duplicate:
                dedup_match = d_match
                dedup_warning = f"Task may already be completed: {d_match.explanation}"
        except Exception:
            pass

    return PlanResult(
        goal=goal,
        workspace=workspace,
        relevant_files=candidates,
        detected_tools=_detected_tools(workspace),
        repo_map=repo_map,
        dedup_warning=dedup_warning,
        dedup_match=dedup_match,
    )
