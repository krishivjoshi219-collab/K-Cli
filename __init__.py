"""K-CLI: Compiler-Grounded AI Coding Agent (< 1GB RAM)"""

import warnings
warnings.filterwarnings("ignore")

__version__ = "0.3.0"

from k_cli.conflict_resolver import (
    ConflictBlock,
    ConflictResolution,
    ConflictResolver,
    ConflictSummary,
    FileResolutionResult,
)
from k_cli.dedup_engine import (
    CommitRecord,
    DedupEngine,
    DedupMatch,
    SimilarityScorer,
    SymbolRecord,
)
from k_cli.incident_triage import (
    IncidentHealResult,
    IncidentReport,
    IncidentTriageEngine,
    LogType,
    StackFrame,
)
from k_cli.diagram_generator import (
    DiagramGenerator,
    DiagramType,
)
from k_cli.smart_git import (
    SmartGitEngine,
    SmartCommitProposal,
    PRDescriptionProposal,
    AtomicCommitGroup,
    FileChangeAnalysis,
    CommitType,
)
from k_cli.security_healer import (
    SecurityHealer,
    SecurityScanReport,
    VulnerabilityFinding,
    VulnerabilityHealResult,
    VulnerabilitySeverity,
    VulnerabilityType,
)

from k_cli.github_client import (
    CIStatus,
    GitHubAPIError,
    GitHubClient,
    PRFixResult,
    PRLifecycleManager,
    PRReviewResult,
    PullRequest,
)
from k_cli.mcp_client import (
    MCPClient,
    MCPManager,
    MCPPrompt,
    MCPResource,
    MCPServerConfig,
    MCPTool,
    MCPToolResult,
)

__all__ = [
    "ConflictBlock",
    "ConflictResolution",
    "ConflictResolver",
    "ConflictSummary",
    "FileResolutionResult",
    "CommitRecord",
    "DedupEngine",
    "DedupMatch",
    "SimilarityScorer",
    "SymbolRecord",
    "GitHubClient",
    "PRLifecycleManager",
    "PullRequest",
    "CIStatus",
    "PRReviewResult",
    "PRFixResult",
    "MCPClient",
    "MCPManager",
    "MCPServerConfig",
    "MCPTool",
    "MCPToolResult",
    "MCPResource",
    "MCPPrompt",
    "IncidentHealResult",
    "IncidentReport",
    "IncidentTriageEngine",
    "LogType",
    "StackFrame",
    "DiagramGenerator",
    "DiagramType",
    "SmartGitEngine",
    "SmartCommitProposal",
    "PRDescriptionProposal",
    "AtomicCommitGroup",
    "FileChangeAnalysis",
    "CommitType",
    "SecurityHealer",
    "SecurityScanReport",
    "VulnerabilityFinding",
    "VulnerabilityHealResult",
    "VulnerabilitySeverity",
    "VulnerabilityType",
]
