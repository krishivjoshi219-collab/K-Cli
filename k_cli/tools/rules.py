"""rules.py - Project rules stub (rules.py was removed in cleanup)."""
MAX_RULE_BYTES = 32_768

def load_project_rules(path: str = ".") -> str:
    """Load project-level coding rules from .kcli/rules.md if present."""
    import pathlib
    rule_file = pathlib.Path(path) / ".kcli" / "rules.md"
    if rule_file.exists():
        return rule_file.read_text(encoding="utf-8")[:MAX_RULE_BYTES]
    return ""
