"""K-CLI: AI-powered agentic developer workstation for the terminal."""

import warnings
warnings.filterwarnings("ignore")

__version__ = "0.4.0"

# ── Core AI & SDK ──────────────────────────────────────────────────────────
from k_cli.core.sdk import KCLI
from k_cli.core.models_hub import ModelBenchmarkResult, ModelHub, ModelProvider, ModelSpec
from k_cli.core.llm_driver import LLMDriver
from k_cli.core.session import SessionManager

# ── GitHub & Deduplication ─────────────────────────────────────────────────
from k_cli.github.github_engine import GitHubEngine, GitHubIssue, GitHubRelease, IssueSolveResult, WorkflowRun
from k_cli.github.github_client import CIStatus, GitHubAPIError, GitHubClient, PRFixResult, PRLifecycleManager, PRReviewResult, PullRequest
from k_cli.github.dedup_engine import CommitRecord, DedupEngine, DedupMatch, SimilarityScorer, SymbolRecord

# ── Git & Code Patching ────────────────────────────────────────────────────
from k_cli.git.conflict_resolver import ConflictBlock, ConflictResolution, ConflictResolver, ConflictSummary, FileResolutionResult
from k_cli.git.smart_git import AtomicCommitGroup, CommitType, FileChangeAnalysis, PRDescriptionProposal, SmartCommitProposal, SmartGitEngine
from k_cli.git.verifier import Verifier
from k_cli.git.patcher import Patcher

# ── Agents & Orchestration ─────────────────────────────────────────────────
from k_cli.agents.orchestrator import Orchestrator
from k_cli.agents.subagents import SubagentDispatcher

# ── Tools & Diagnostics ───────────────────────────────────────────────────
from k_cli.tools.security_healer import SecurityHealer, SecurityScanReport, VulnerabilityFinding, VulnerabilityHealResult, VulnerabilitySeverity, VulnerabilityType
from k_cli.tools.incident_triage import IncidentHealResult, IncidentReport, IncidentTriageEngine, LogType, StackFrame
from k_cli.tools.diagram_generator import DiagramGenerator, DiagramType
from k_cli.tools.mcp_client import MCPClient, MCPManager, MCPPrompt, MCPResource, MCPServerConfig, MCPTool, MCPToolResult

__all__ = [
    # Core
    "KCLI", "ModelHub", "ModelSpec", "ModelProvider", "ModelBenchmarkResult", "LLMDriver", "SessionManager",
    # GitHub
    "GitHubEngine", "GitHubIssue", "GitHubRelease", "WorkflowRun", "IssueSolveResult",
    "GitHubClient", "PRLifecycleManager", "PullRequest", "CIStatus", "PRReviewResult", "PRFixResult", "GitHubAPIError",
    "DedupEngine", "DedupMatch", "CommitRecord", "SimilarityScorer", "SymbolRecord",
    # Git
    "ConflictBlock", "ConflictResolution", "ConflictResolver", "ConflictSummary", "FileResolutionResult",
    "SmartGitEngine", "SmartCommitProposal", "PRDescriptionProposal", "AtomicCommitGroup", "FileChangeAnalysis", "CommitType",
    "Verifier", "Patcher",
    # Agents
    "Orchestrator", "SubagentDispatcher",
    # Tools
    "SecurityHealer", "SecurityScanReport", "VulnerabilityFinding", "VulnerabilityHealResult", "VulnerabilitySeverity", "VulnerabilityType",
    "IncidentHealResult", "IncidentReport", "IncidentTriageEngine", "LogType", "StackFrame",
    "DiagramGenerator", "DiagramType",
    "MCPClient", "MCPManager", "MCPServerConfig", "MCPTool", "MCPToolResult", "MCPResource", "MCPPrompt",
]
