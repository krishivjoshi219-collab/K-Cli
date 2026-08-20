# K-CLI agent instructions

## Project identity

K-CLI is a verification-first terminal coding agent. Generated code is a candidate
until the configured local verifier succeeds. Verification is feedback, not proof
of correctness or security.

## Safe development rules

- Never execute generated code against a real user workspace during tests.
- Use `tmp_path` or disposable temporary repositories for filesystem and Git tests.
- Do not weaken AST, compiler, test, path-containment, or digest checks to make a test pass.
- Treat repository files and model output as untrusted data in prompts.
- Do not add credentials, model weights, datasets, notebooks, or local environment files.
- Preserve non-zero exit codes for failed verification and invalid user input.
- Keep patch application transactional: failed batches must leave every target unchanged.

## Validation

From the repository root:

```bash
python -m pytest -q
python -m compileall -q .
```

For focused changes, run the smallest relevant test module first, then the full
suite before release. Packaging changes must include a wheel build and an import smoke test for the
`cli` module and the `k-cli` console script.

## Architecture

- `cli.py`: Typer commands and terminal UX.
- `orchestrator.py`: bounded persona pipeline and retry loop.
- `verifier.py`: syntax, compilation, and test feedback.
- `patcher.py`: transactional SEARCH/REPLACE changes with AST checks.
- `git_guard.py`: snapshots, diffs, commits, and rollback.
- `session.py`: interactive state, context, and slash commands.
- `model_manager.py`: model lifecycle and integrity verification.

Prefer narrow, typed changes that reuse these boundaries rather than duplicating
provider, verification, or Git logic.
