"""Multi-model generation audit with independent local verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

try:
    from k_cli.llm_driver import LLMDriver
    from k_cli.prompting import enhance_prompt
    from k_cli.verifier import CodeExtractor, VerificationResult, Verifier
except ModuleNotFoundError:
    from llm_driver import LLMDriver
    from prompting import enhance_prompt
    from verifier import CodeExtractor, VerificationResult, Verifier


@dataclass
class AuditCandidate:
    model: str
    code: str
    verification: VerificationResult


@dataclass
class AuditResult:
    candidates: List[AuditCandidate]

    @property
    def passed(self) -> List[AuditCandidate]:
        return [candidate for candidate in self.candidates if candidate.verification.success]

    @property
    def consensus_reached(self) -> bool:
        return len(self.passed) >= 2 if len(self.candidates) > 1 else bool(self.passed)


def run_audit(task: str, models: List[str], language: str = "python", mock: bool = False) -> AuditResult:
    """Generate independent candidates and verify each one locally.

    The function never writes a candidate to the workspace; it gives callers a
    reviewable set of verified/unverified alternatives instead.
    """
    verifier = Verifier()
    candidates: List[AuditCandidate] = []
    for model in models:
        cleaned_model = model.strip()
        if not cleaned_model:
            continue
        driver = LLMDriver(model_name=cleaned_model, mock_mode=mock)
        response = driver.generate(enhance_prompt(task, cleaned_model, language))
        detected_language, code = CodeExtractor.extract_primary_code(response, default_lang=language)
        verification = verifier.verify(code, language=detected_language)
        candidates.append(AuditCandidate(model=cleaned_model, code=code, verification=verification))
    return AuditResult(candidates=candidates)
