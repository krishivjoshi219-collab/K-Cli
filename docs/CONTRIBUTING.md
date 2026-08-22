# Contributing to K-CLI

Thanks for helping improve K-CLI. Contributions should make the verification
loop safer, clearer, faster, or easier to use.

## Before opening a pull request

1. Read `AGENTS.md`, `SECURITY.md`, and the relevant module boundaries.
2. Add or update tests for behavior changes.
3. Run `python -m pytest -q`.
4. Run `python -m compileall -q .`.
5. Build a wheel when changing packaging or entry points.
6. Keep generated artifacts, credentials, model weights, and datasets out of the commit.

## Pull requests

Describe the user problem, the behavioral change, safety implications, and
validation commands. Include before/after terminal output or a short recording
for UX changes. Avoid mixing unrelated refactors with feature work.

## Design expectations

- Failed verification must remain observable and return a non-zero exit status.
- File edits must be transactional and confined to the requested workspace.
- Network downloads must use explicit timeouts and trusted integrity metadata.
- User-controlled and repository-controlled text must not silently become trusted instructions.

## Good First Issues & Starter Contributions

Looking for a great way to contribute? Here are high-impact starter areas:
- **Theme Presets**: Add new terminal theme palettes to `tui_app.py` (e.g. Catppuccin Mocha, Tokyo Night, Dracula, Gruvbox).
- **Language Support**: Expand syntax verification in `verifier.py` and symbol extraction in `repo_map.py` (e.g., Zig, Elixir, Swift, Kotlin).
- **Custom Model Adapters**: Create domain-specific model and media adapters using `register_adapter()` in `llm_driver.py`.
- **Test Frameworks**: Add detection and test runners in `verifier.py` (e.g., `dotnet test`, `mvn test`, `pytest-benchmark`).

