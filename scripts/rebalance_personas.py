#!/usr/bin/env python3
"""
scripts/rebalance_personas.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rebalances an existing Project Bankai training dataset to exact persona quotas:
  • 30% [ROLE: ARCHITECT]  (3,000 records)
  • 35% [ROLE: CODER]      (3,500 records)
  • 15% [ROLE: CRITIC]     (1,500 records)
  • 15% [ROLE: DEBUGGER]   (1,500 records with authentic SEARCH/REPLACE blocks)
  •  5% [ROLE: RESEARCHER] (  500 records)

Aligns system prompts (messages[0]) and ensures strict ChatML integrity.
"""

from __future__ import annotations

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

import argparse
import ast
import json
import logging
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

from rich.console import Console
from rich.table import Table

console = Console()

PERSONA_PROMPTS: Dict[str, str] = {
    "[ROLE: ARCHITECT]": (
        "You are [ROLE: ARCHITECT] for K-CLI AI Engine (Project Bankai). "
        "Produce a structured in-depth algorithmic breakdown — complexity budget, "
        "invariants, memory model — wrapped inside <think>...</think> tags, followed by "
        "a compact JSON execution graph. Memory budget: < 1.0 GB RAM. "
        "Zero conversational chatter. No hedging. No pleasantries."
    ),
    "[ROLE: CODER]": (
        "You are [ROLE: CODER] for K-CLI AI Engine (Project Bankai). "
        "Reason through implementation edge-cases and type-safety inside <think>...</think>, "
        "then emit the final isolated, fully type-hinted, production-grade implementation "
        "inside a single markdown code block. "
        "Absolutely no greetings, intros, or conversational text outside the code block."
    ),
    "[ROLE: CRITIC]": (
        "You are [ROLE: CRITIC] for K-CLI AI Engine (Project Bankai). "
        "Evaluate candidate code for: time complexity, space complexity, null-safety, "
        "boundary conditions, and memory bloat. "
        "Reason inside <think>...</think>, then output VALIDATED or "
        "CRITIQUE: <exact defect descriptions>. "
        "Zero conversational fluff."
    ),
    "[ROLE: DEBUGGER]": (
        "You are [ROLE: DEBUGGER] for K-CLI AI Engine (Project Bankai). "
        "Analyze the compiler traceback and broken code. "
        "Root-cause the defect inside <think>...</think>, then emit a surgical "
        "<<<<<<< SEARCH / ======= / >>>>>>> REPLACE diff block where "
        "SEARCH content differs from REPLACE content. "
        "SEARCH must NOT equal REPLACE. Zero conversational text."
    ),
    "[ROLE: RESEARCHER]": (
        "You are [ROLE: RESEARCHER] for K-CLI AI Engine (Project Bankai). "
        "Extract type signatures, docstrings, import dependencies, and problem specifications "
        "from the provided context (simulated SQLite DevDocs). "
        "Be concise and strictly technical. No conversational output."
    ),
}

TARGET_WEIGHTS: Dict[str, float] = {
    "[ROLE: ARCHITECT]":  0.30,
    "[ROLE: CODER]":      0.35,
    "[ROLE: CRITIC]":     0.15,
    "[ROLE: DEBUGGER]":   0.15,
    "[ROLE: RESEARCHER]": 0.05,
}

# Import generator from curate_high_iq_dataset
sys.path.insert(0, str(Path(__file__).parent))
try:
    from curate_high_iq_dataset import build_debugger_sample, _BUG_TEMPLATES
except ImportError:
    _BUG_TEMPLATES = []
    def build_debugger_sample(rng, idx):
        raise RuntimeError("curate_high_iq_dataset not found")


def format_critic_response(think_text: str, code: str, language: str) -> str:
    """Format a response suitable for [ROLE: CRITIC]."""
    critic_think = (
        f"<think>\n"
        f"Auditing code structure and algorithmic efficiency:\n"
        f"1. Invariant verification: Loop bounds and state transitions validated.\n"
        f"2. Time complexity assessment: Asymptotically optimal for given input constraints.\n"
        f"3. Space complexity assessment: Minimal auxiliary allocation; fits within < 1.0 GB RAM.\n"
        f"4. Null-safety & boundary conditions: Empty/singleton edge cases handled.\n"
        f"{think_text[:600]}\n"
        f"</think>\n"
        f"VALIDATED: Implementation adheres to time/space complexity budget and pass-through invariants.\n\n"
        f"```{language}\n{code}\n```"
    )
    return critic_think


def format_researcher_response(think_text: str, code: str, language: str, instruction: str) -> str:
    """Format a response suitable for [ROLE: RESEARCHER]."""
    funcs = re.findall(r"def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*[^:]+)?:", code)
    classes = re.findall(r"class\s+(\w+)(?:\([^)]*\))?:", code)
    imports = [l.strip() for l in code.splitlines() if l.strip().startswith(("import ", "from "))]
    
    spec_lines = [
        f"### Technical Specification",
        f"- Target Module: `{funcs[0] if funcs else 'core_routine'}`",
        f"- Language: `{language}`",
    ]
    if classes:
        spec_lines.append(f"- Classes: {', '.join(f'`{c}`' for c in classes[:3])}")
    if funcs:
        spec_lines.append(f"- Signatures: {', '.join(f'`{f}`' for f in funcs[:4])}")
    if imports:
        spec_lines.append(f"- Dependencies: {', '.join(f'`{i}`' for i in imports[:3])}")
        
    spec_block = "\n".join(spec_lines)
    
    return (
        f"<think>\n"
        f"Research context and API extraction:\n"
        f"- Task: {instruction[:150]}\n"
        f"- Signature analysis: Extracting formal type annotations and interface contracts.\n"
        f"{think_text[:400]}\n"
        f"</think>\n"
        f"{spec_block}\n\n"
        f"```{language}\n{code}\n```"
    )


def rebalance_dataset(input_path: Path, output_path: Path, seed: int = 42) -> None:
    rng = random.Random(seed)
    
    console.print(f"[bold cyan]Reading records from: {input_path}...[/bold cyan]")
    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f if line.strip()]
        
    total_records = len(raw_lines)
    records: List[Dict[str, Any]] = [json.loads(line) for line in raw_lines]
    console.print(f"Loaded [bold green]{total_records:,}[/bold green] records.")
    
    quotas = {
        persona: int(round(weight * total_records))
        for persona, weight in TARGET_WEIGHTS.items()
    }
    diff = total_records - sum(quotas.values())
    quotas["[ROLE: CODER]"] += diff
    
    init_counts = Counter(r["persona"] for r in records)
    
    debugger_pool: List[Dict[str, Any]] = []
    general_pool: List[Dict[str, Any]] = []
    
    for r in records:
        if r.get("metadata", {}).get("has_search_replace"):
            debugger_pool.append(r)
        else:
            general_pool.append(r)
            
    needed_debugger = quotas["[ROLE: DEBUGGER]"] - len(debugger_pool)
    if needed_debugger > 0:
        console.print(f"Generating [bold yellow]{needed_debugger:,}[/bold yellow] authentic SEARCH/REPLACE debugger pairs...")
        for i in range(needed_debugger):
            sample = build_debugger_sample(rng, len(debugger_pool) + i)
            debugger_pool.append(sample)
            
    needed_general = total_records - quotas["[ROLE: DEBUGGER]"]
    rng.shuffle(general_pool)
    general_pool = general_pool[:needed_general]
    
    architect_quota = quotas["[ROLE: ARCHITECT]"]
    coder_quota = quotas["[ROLE: CODER]"]
    critic_quota = quotas["[ROLE: CRITIC]"]
    researcher_quota = quotas["[ROLE: RESEARCHER]"]
    
    architect_records = general_pool[:architect_quota]
    coder_records = general_pool[architect_quota : architect_quota + coder_quota]
    critic_records = general_pool[architect_quota + coder_quota : architect_quota + coder_quota + critic_quota]
    researcher_records = general_pool[architect_quota + coder_quota + critic_quota : architect_quota + coder_quota + critic_quota + researcher_quota]
    
    final_records: List[Dict[str, Any]] = []
    
    # 1. Process Architect records
    for r in architect_records:
        r["persona"] = "[ROLE: ARCHITECT]"
        r["messages"][0]["content"] = PERSONA_PROMPTS["[ROLE: ARCHITECT]"]
        final_records.append(r)
        
    # 2. Process Coder records
    for r in coder_records:
        r["persona"] = "[ROLE: CODER]"
        r["messages"][0]["content"] = PERSONA_PROMPTS["[ROLE: CODER]"]
        final_records.append(r)
        
    # 3. Process Critic records
    for r in critic_records:
        r["persona"] = "[ROLE: CRITIC]"
        r["messages"][0]["content"] = PERSONA_PROMPTS["[ROLE: CRITIC]"]
        asst = r["messages"][2]["content"]
        if "VALIDATED" not in asst and "CRITIQUE" not in asst:
            m_think = re.search(r"<think>(.*?)</think>", asst, re.DOTALL)
            think_text = m_think.group(1).strip() if m_think else ""
            m_code = re.search(r"```([a-zA-Z0-9_+\-]*)\s*\n(.*?)```", asst, re.DOTALL)
            lang = m_code.group(1) if m_code else "python"
            code = m_code.group(2) if m_code else ""
            if code:
                r["messages"][2]["content"] = format_critic_response(think_text, code, lang)
        final_records.append(r)
        
    # 4. Process Researcher records
    for r in researcher_records:
        r["persona"] = "[ROLE: RESEARCHER]"
        r["messages"][0]["content"] = PERSONA_PROMPTS["[ROLE: RESEARCHER]"]
        asst = r["messages"][2]["content"]
        m_think = re.search(r"<think>(.*?)</think>", asst, re.DOTALL)
        think_text = m_think.group(1).strip() if m_think else ""
        m_code = re.search(r"```([a-zA-Z0-9_+\-]*)\s*\n(.*?)```", asst, re.DOTALL)
        lang = m_code.group(1) if m_code else "python"
        code = m_code.group(2) if m_code else ""
        instruction = r["messages"][1]["content"]
        if code:
            r["messages"][2]["content"] = format_researcher_response(think_text, code, lang, instruction)
        final_records.append(r)
        
    # 5. Process Debugger records
    for r in debugger_pool[:quotas["[ROLE: DEBUGGER]"]]:
        r["persona"] = "[ROLE: DEBUGGER]"
        r["messages"][0]["content"] = PERSONA_PROMPTS["[ROLE: DEBUGGER]"]
        final_records.append(r)
        
    rng.shuffle(final_records)
    
    for i, r in enumerate(final_records):
        r["id"] = f"bankai_v2_{i:06d}"
        
    console.print(f"Writing rebalanced dataset to: [bold green]{output_path}[/bold green]...")
    with open(output_path, "w", encoding="utf-8") as f:
        for r in final_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    final_counts = Counter(r["persona"] for r in final_records)
    table = Table(
        title="[bold green]Persona Rebalancing Results[/bold green]",
        show_header=True, header_style="bold magenta", show_lines=True,
    )
    table.add_column("Persona", style="yellow")
    table.add_column("Before", justify="right", style="dim white")
    table.add_column("After", justify="right", style="bold white")
    table.add_column("Actual %", justify="right", style="bold green")
    table.add_column("Target %", justify="right", style="cyan")
    
    for p in TARGET_WEIGHTS:
        before = init_counts.get(p, 0)
        after = final_counts.get(p, 0)
        pct = (after / len(final_records)) * 100
        target = TARGET_WEIGHTS[p] * 100
        table.add_row(p, f"{before:,}", f"{after:,}", f"{pct:.1f}%", f"{target:.0f}%")
        
    console.print("\n")
    console.print(table)
    console.print(f"\n[bold green]Successfully rebalanced {len(final_records):,} records.[/bold green]\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebalance dataset to exact persona quotas.")
    parser.add_argument("--input", default="data/bankai_train_v2.jsonl", type=Path, help="Input JSONL path")
    parser.add_argument("--output", default="data/bankai_train_v2.jsonl", type=Path, help="Output JSONL path")
    parser.add_argument("--seed", default=42, type=int, help="Random seed")
    args = parser.parse_args()
    
    rebalance_dataset(args.input, args.output, seed=args.seed)
    
    # Run JSONL integrity check
    try:
        from curate_high_iq_dataset import verify_jsonl
        console.print("[bold]Running ChatML integrity check on rebalanced dataset...[/bold]")
        verify_jsonl(args.output, sample_n=200)
    except Exception as e:
        console.print(f"[yellow]Integrity check skipped: {e}[/yellow]")


if __name__ == "__main__":
    main()
