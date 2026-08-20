"""Read-only repository evidence checks for requested feature claims."""

from __future__ import annotations

import ast
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, List

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "k_cli_env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "data",
    "build",
    "dist",
}
SOURCE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".go", ".rs", ".java", ".cpp", ".h", ".md"}
TEST_MARKERS = ("test", "spec", "qa", "e2e", "benchmark")


@dataclass(frozen=True)
class FeatureMatch:
    path: str
    line: int
    evidence: str
    category: str


@dataclass(frozen=True)
class FeatureEvidence:
    query: str
    workspace: str
    source_matches: List[FeatureMatch]
    test_matches: List[FeatureMatch]
    symbol_matches: List[FeatureMatch]

    @property
    def proven(self) -> bool:
        return bool(self.source_matches) and bool(self.test_matches or self.symbol_matches)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["proven"] = self.proven
        return payload


def _iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if (
            path.is_file()
            and path.suffix.lower() in SOURCE_SUFFIXES
            and not any(part in IGNORED_DIRS for part in path.parts)
        ):
            yield path


def _terms(query: str) -> List[str]:
    return [term for term in re.findall(r"[a-zA-Z0-9_]+", query.lower()) if len(term) > 2]


def _matches_for_file(path: Path, root: Path, terms: List[str], category: str) -> List[FeatureMatch]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    relative = path.relative_to(root).as_posix()
    matches: List[FeatureMatch] = []
    for number, line in enumerate(lines, start=1):
        haystack = f"{relative} {line}".lower()
        if all(term in haystack for term in terms):
            matches.append(FeatureMatch(relative, number, line.strip()[:240], category))
    return matches[:10]


def _python_symbols(path: Path, root: Path, query_terms: List[str]) -> List[FeatureMatch]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []
    relative = path.relative_to(root).as_posix()
    matches: List[FeatureMatch] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name.lower()
            if all(term in name for term in query_terms):
                matches.append(FeatureMatch(relative, node.lineno, node.name, "symbol"))
    return matches[:10]


def inspect_feature(query: str, workspace_dir: str | Path = ".") -> FeatureEvidence:
    """Collect bounded source, test, and symbol evidence for a feature claim."""
    root = Path(workspace_dir).resolve()
    terms = _terms(query)
    if not terms or not root.exists():
        return FeatureEvidence(query=query, workspace=str(root), source_matches=[], test_matches=[], symbol_matches=[])

    source_matches: List[FeatureMatch] = []
    test_matches: List[FeatureMatch] = []
    symbol_matches: List[FeatureMatch] = []
    for path in _iter_files(root):
        relative = path.relative_to(root).as_posix().lower()
        category = test_matches if any(marker in relative for marker in TEST_MARKERS) else source_matches
        category.extend(_matches_for_file(path, root, terms, "test" if category is test_matches else "source"))
        if path.suffix.lower() == ".py":
            symbol_matches.extend(_python_symbols(path, root, terms))
        if len(source_matches) + len(test_matches) + len(symbol_matches) >= 30:
            break

    return FeatureEvidence(
        query=query,
        workspace=str(root),
        source_matches=source_matches[:10],
        test_matches=test_matches[:10],
        symbol_matches=symbol_matches[:10],
    )
