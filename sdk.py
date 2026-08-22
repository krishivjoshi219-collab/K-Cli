"""
sdk.py - Universal Python SDK & Agentic Framework for K-CLI
Project Bankai Engine v0.4.0

Provides a clean, unified Python API for programmatic integration:
```python
from k_cli import KCLI

# 1. Initialize K-CLI Agent
with KCLI(model="deepseek-reasoner", local_fallback="qwen2.5-coder:1.5b") as kcli:
    # 2. Multi-Model Inference
    response = kcli.generate("Write a lock-free queue in C++23")

    # 3. Autonomous GitHub Agent
    kcli.github.solve_issue(12, auto_pr=True)
    kcli.github.create_release(tag_name="v1.0.0")

    # 4. Conflict Resolution & Security Healing
    kcli.conflicts.resolve_all()
    kcli.security.heal_all()

    # 5. Visual Architecture Diagrams
    kcli.diagrams.generate_mermaid_architecture(output_file="ARCHITECTURE.md")
```
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from k_cli.llm_driver import LLMDriver, ProviderType
from k_cli.models_hub import ModelBenchmarkResult, ModelHub, ModelSpec
from k_cli.github_engine import GitHubEngine, IssueSolveResult
from k_cli.github_client import GitHubClient, PRLifecycleManager
from k_cli.conflict_resolver import ConflictResolver, ConflictSummary
from k_cli.dedup_engine import DedupEngine, DedupMatch
from k_cli.mcp_client import MCPManager
from k_cli.incident_triage import IncidentHealResult, IncidentReport, IncidentTriageEngine
from k_cli.diagram_generator import DiagramGenerator
from k_cli.smart_git import SmartCommitProposal, SmartGitEngine
from k_cli.security_healer import SecurityHealer, VulnerabilityHealResult, SecurityScanReport
from k_cli.verifier import Verifier
from k_cli.patcher import Patcher
from k_cli.orchestrator import Orchestrator, OrchestratorResult
from k_cli.session import SessionManager
from k_cli.workflow import PlanResult, create_plan

logger = logging.getLogger("k_cli.sdk")


class KCLI:
    """
    Main K-CLI Agentic SDK Client.
    Provides direct programmatic access to all local & cloud AI models,
    autonomous GitHub operations, merge conflict resolvers, and security healers.
    """

    def __init__(
        self,
        model: str = "qwen2.5-coder:1.5b",
        provider: Optional[Union[ProviderType, str]] = None,
        repo_path: str = ".",
        mock_mode: bool = False,
        github_token: Optional[str] = None,
        ram_budget_mb: float = 1024.0,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.active_model_name = model
        self.mock_mode = mock_mode

        # Core Engines
        self.models = ModelHub()
        self.verifier = Verifier()
        self.patcher = Patcher()
        self.driver = LLMDriver(
            model_name=model,
            provider=provider,
            mock_mode=mock_mode,
        )
        self.dedup = DedupEngine(repo_path=str(self.repo_path))
        self.orchestrator = Orchestrator(
            driver=self.driver,
            verifier=self.verifier,
            dedup_engine=self.dedup,
            ram_budget_mb=ram_budget_mb,
        )
        self.session = SessionManager(
            workspace_dir=str(self.repo_path),
            model_name=model,
            mock_mode=mock_mode,
        )

        # Specialized Tooling
        self.github = GitHubEngine(token=github_token, repo_path=str(self.repo_path))
        self.pr_lifecycle = PRLifecycleManager(client=GitHubClient(token=github_token))
        self.conflicts = ConflictResolver()
        self.mcp = MCPManager()
        self.security = SecurityHealer(repo_path=str(self.repo_path), llm_driver=self.driver)
        self.triage = IncidentTriageEngine(repo_path=str(self.repo_path))
        self.diagrams = DiagramGenerator(repo_path=str(self.repo_path))
        self.smart_git = SmartGitEngine(repo_path=str(self.repo_path), llm_driver=self.driver)

    def __enter__(self) -> KCLI:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    # =========================================================================
    # High-Level Agent Methods
    # =========================================================================

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Generates AI response across any local or cloud model."""
        target_driver = self.driver
        if model and model != self.active_model_name:
            target_driver = LLMDriver(model_name=model, mock_mode=self.mock_mode)

        return target_driver.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            stream_callback=stream_callback,
        )

    def run(
        self,
        task: str,
        language: str = "python",
        test_code: Optional[str] = None,
        stream_callback: Optional[Callable[[Any, str], None]] = None,
    ) -> OrchestratorResult:
        """Executes full verified 5-stage persona pipeline."""
        return self.orchestrator.execute_pipeline(
            user_prompt=task,
            language=language,
            test_code=test_code,
            token_stream_callback=stream_callback,
        )

    def plan(self, goal: str, max_files: int = 10) -> PlanResult:
        """Generates a protected, read-only change plan with deduplication check."""
        return create_plan(
            goal=goal,
            workspace_dir=str(self.repo_path),
            max_files=max_files,
        )

    def resolve_conflicts(self, repo_path: Optional[str] = None) -> ConflictSummary:
        """Automatically resolves all git merge conflicts with compiler verification."""
        target_path = repo_path or str(self.repo_path)
        return self.conflicts.resolve_all_conflicts(
            repo_path=target_path,
            llm_driver=self.driver,
            verifier=self.verifier,
        )

    def solve_issue(self, issue_number: int, auto_pr: bool = True) -> IssueSolveResult:
        """Autonomously investigates, fixes, verifies, and PRs a GitHub issue."""
        return self.github.solve_issue(
            issue_number=issue_number,
            llm_driver=self.driver,
            verifier=self.verifier,
            patcher=self.patcher,
            auto_pr=auto_pr,
        )

    def scan_security(self) -> SecurityScanReport:
        """Scans repository for security vulnerabilities."""
        return self.security.scan_repository()

    def heal_security(self) -> List[VulnerabilityHealResult]:
        """Scans and surgically auto-heals security vulnerabilities."""
        return self.security.heal_all_vulnerabilities(
            verifier=self.verifier,
            patcher=self.patcher,
            llm_driver=self.driver,
        )

    def generate_diagram(self, output_file: Optional[str] = None) -> str:
        """Generates visual Mermaid architecture diagrams."""
        return self.diagrams.generate_mermaid_architecture(output_file=output_file)

    def commit(self, push: bool = False) -> SmartCommitProposal:
        """Generates AST Conventional Commit and optionally pushes."""
        proposal = self.smart_git.generate_smart_commit()
        if proposal.subject:
            self.smart_git.auto_stage_and_commit(message=proposal.full_message, push=push)
        return proposal
