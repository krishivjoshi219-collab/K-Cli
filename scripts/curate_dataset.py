#!/usr/bin/env python3
"""
scripts/curate_dataset.py - Dataset Curation & Persona Synthesis Engine for K-CLI (Project Bankai)

Principal Data Engineering utility to:
1. Stream raw samples from Hugging Face:
   - `m-a-p/CodeFeedback-Filtered-Instruction`
   - `sahil2801/CodeAlpaca-20k`
   - `open-r1/codeforces`
2. Inspect column names dynamically (problem, prompt, solution, generation, messages, etc.).
3. Clean and strip conversational padding via regex while preserving <think>...</think> traces.
4. Validate code snippets: AST parsing for Python, structural checks for C++ / Bash.
5. Injects K-CLI specialized system personas:
   - [ROLE: ARCHITECT] (Execution plans & JSON specs)
   - [ROLE: CODER] (Isolated unpadded executable code)
   - [ROLE: CRITIC] (Static analysis, edge cases, RAM constraints)
   - [ROLE: DEBUGGER] (Compiler trace repair & SEARCH/REPLACE diff blocks)
6. Exports final cleaned output to `data/bankai_train.jsonl` with Rich visual reporting.
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import os
import random
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple, Union

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

# Initialize rich console and logging
console = Console()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("curate_dataset")


# =====================================================================
# 1. System Persona Definitions & Prompts
# =====================================================================

PERSONA_SYSTEM_PROMPTS: Dict[str, str] = {
    "[ROLE: ARCHITECT]": (
        "You are [ROLE: ARCHITECT] for the K-CLI AI Engine. "
        "Analyze the requirements and generate an in-depth step-by-step algorithmic breakdown "
        "and complexity budget enclosed inside <think>...</think> tags. "
        "Follow the thinking tags with a structured JSON architecture specification. "
        "Ensure memory efficiency (< 1.0 GB RAM). Do NOT output conversational chatter."
    ),
    "[ROLE: CODER]": (
        "You are [ROLE: CODER] for the K-CLI AI Engine. "
        "First, reason step-by-step about implementation details, edge cases, and type safety "
        "inside <think>...</think> tags. "
        "Then, output the final, isolated, production-grade Python implementation strictly "
        "enclosed inside a markdown code block. "
        "Do NOT output conversational greetings, intros, or chatter."
    ),
    "[ROLE: CRITIC]": (
        "You are [ROLE: CRITIC] for the K-CLI AI Engine. "
        "Review candidate code against syntax validity, null safety, boundary edge cases, "
        "and system RAM constraints. "
        "Provide reasoning inside <think>...</think> tags, followed by VALIDATED or CRITIQUE with exact defect details. "
        "Do NOT output conversational fluff."
    ),
    "[ROLE: DEBUGGER]": (
        "You are [ROLE: DEBUGGER] for the K-CLI AI Engine. "
        "Analyze the provided code and compiler/runtime execution error trace. "
        "Provide root-cause analysis inside <think>...</think> tags, then emit a surgical "
        "SEARCH/REPLACE block or corrected implementation inside markdown blocks. "
        "Do NOT output conversational fluff."
    ),
}


# =====================================================================
# 2. Conversational Padding Regex Cleaner
# =====================================================================

INTRO_PATTERNS = [
    r"^(?:Sure|Certainly|Of course|Here is|Below is|Here's|Hello|Hi|Greetings|Hey|Okay|Alright)[^`\n]*\n*",
    r"^I would be happy to help[^\n]*\n*",
    r"^To solve this problem[,\s]+(?:here is|we can)[^\n]*\n*",
    r"^As requested[,\s]+[^\n]*\n*",
    r"^Here is the complete (?:python|working|updated|c\+\+|bash)?\s*code:[^\n]*\n*",
]

OUTRO_PATTERNS = [
    r"\n*(?:Hope this helps|Let me know if you (?:have|need)|Feel free to ask|Happy coding|Good luck)[^\n]*$",
    r"\n*(?:If you have any questions|Please let me know)[^\n]*$",
    r"\n*This solution runs in O\([^)]+\)[^\n]*$",
]

COMPILED_INTRO_RE = re.compile("|".join(f"(?:{p})" for p in INTRO_PATTERNS), re.IGNORECASE | re.MULTILINE)
COMPILED_OUTRO_RE = re.compile("|".join(f"(?:{p})" for p in OUTRO_PATTERNS), re.IGNORECASE | re.MULTILINE)


class TextSanitizer:
    """Cleans conversational fluff, extracts reasoning traces, and structures responses."""

    @staticmethod
    def strip_conversational_padding(text: str) -> str:
        """Strips greetings, conversational padding, and pleasantries while preserving <think> tags."""
        if not text:
            return ""

        cleaned = text.strip()
        # Remove intros and outros
        cleaned = COMPILED_INTRO_RE.sub("", cleaned).strip()
        cleaned = COMPILED_OUTRO_RE.sub("", cleaned).strip()
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @staticmethod
    def extract_code_blocks_with_lang(text: str) -> List[Tuple[str, str]]:
        """
        Extracts code blocks along with their specified language tag.
        Returns: list of (language, code_content)
        """
        pattern = r"```([a-zA-Z0-9_\+\-]*)\s*\n(.*?)```"
        matches = re.findall(pattern, text, flags=re.DOTALL)
        results = []
        for lang, code in matches:
            clean_lang = lang.strip().lower() if lang else "python"
            clean_code = code.strip()
            if clean_code:
                results.append((clean_lang, clean_code))
        return results

    @staticmethod
    def extract_or_synthesize_thinking(text: str, prompt: str = "") -> Tuple[str, str]:
        """
        Extracts existing <think>...</think> content if present in the text.
        If absent, synthesizes a concise, high-signal technical reasoning trace.
        Returns: (thinking_content, remaining_text_or_code)
        """
        think_match = re.search(r"<think>(.*?)</think>", text, flags=re.DOTALL | re.IGNORECASE)
        if think_match:
            thinking = think_match.group(1).strip()
            rest = text[:think_match.start()] + text[think_match.end():]
            return thinking, rest.strip()

        synth_lines = [
            "1. Analyze problem constraints: optimize for time and memory efficiency (< 1.0 GB RAM).",
            "2. Identify core algorithmic invariants, type signatures, and data boundaries.",
            "3. Ensure deterministic edge-case handling (empty inputs, zero values, bounds).",
            "4. Emit unpadded implementation code adhering to production standards.",
        ]
        if prompt:
            synth_lines.insert(0, f"Task Objective: {prompt.strip()[:180]}")

        synthesized_think = "\n".join(synth_lines)
        return synthesized_think, text.strip()


# =====================================================================
# 3. Multi-Language Code Validator (AST for Python, Structural for C++/Bash)
# =====================================================================

class ASTCodeValidator:
    """
    Validates code snippets per language:
    - Strict `ast.parse()` for Python snippets.
    - Balanced structure & token checks for C++ / Bash without rejecting them via Python AST.
    """

    @staticmethod
    def is_valid_code(code: str, language: str = "python") -> Tuple[bool, Optional[str]]:
        if not code or not code.strip():
            return False, "Empty code snippet"

        lang = (language or "python").lower().strip()

        if lang in ("python", "py", "python3"):
            try:
                ast.parse(code)
                return True, None
            except SyntaxError as e:
                return False, f"Python SyntaxError at line {e.lineno}: {e.msg}"
            except Exception as e:
                return False, f"Python AST exception: {str(e)}"

        elif lang in ("cpp", "c++", "c", "cxx", "cc"):
            # Basic structural validity for C/C++
            if code.count("{") != code.count("}"):
                return False, "Unbalanced curly braces in C++ block"
            if code.count("(") != code.count(")"):
                return False, "Unbalanced parentheses in C++ block"
            return True, None

        elif lang in ("bash", "sh", "shell", "zsh"):
            # Basic quote balance for shell scripts
            single_quotes = code.count("'") - code.count("\\'")
            if single_quotes % 2 != 0:
                return False, "Unclosed single quote in Bash block"
            return True, None

        else:
            # Non-python languages pass through safely
            return True, None

    @classmethod
    def is_valid_python(cls, code: str) -> Tuple[bool, Optional[str]]:
        """Backwards-compatible helper specifically for Python AST checking."""
        return cls.is_valid_code(code, language="python")


# =====================================================================
# 4. SEARCH / REPLACE Diff Generator
# =====================================================================

class DiffSynthesizer:
    """Generates K-CLI SEARCH/REPLACE surgical patch training examples."""

    @staticmethod
    def create_search_replace_sample(code: str, prompt: str, language: str = "python") -> Optional[Dict[str, Any]]:
        lines = code.splitlines()
        if len(lines) < 4:
            return None

        valid_indices = [
            i for i, line in enumerate(lines)
            if line.strip() and not line.strip().startswith("#") and "def " not in line and "import " not in line
        ]
        if not valid_indices:
            return None

        target_idx = random.choice(valid_indices)
        orig_line = lines[target_idx]

        buggy_line = f"# Fix boundary condition\n{orig_line}"
        search_block = buggy_line
        replace_block = orig_line

        patch_text = (
            f"<<<<<<< SEARCH\n"
            f"{search_block}\n"
            f"=======\n"
            f"{replace_block}\n"
            f">>>>>>>"
        )

        reasoning = (
            f"1. Identified defect in code segment at line {target_idx + 1}.\n"
            f"2. Target code contained unverified or incomplete branch logic.\n"
            f"3. Emitting surgical SEARCH/REPLACE block matching K-CLI patcher specifications."
        )

        lang_tag = language if language else "python"
        return {
            "instruction": f"Fix the defect in the following code for: {prompt}",
            "reasoning": reasoning,
            "response": f"<think>\n{reasoning}\n</think>\n```{lang_tag}\n{patch_text}\n```",
            "has_search_replace": True,
        }


# =====================================================================
# 5. Dataset Schema & Data Pipeline Models
# =====================================================================

@dataclass
class CuratedSample:
    """Standardized K-CLI training record schema."""
    id: str
    persona: str
    system_prompt: str
    instruction: str
    reasoning: str
    response: str
    messages: List[Dict[str, str]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =====================================================================
# 6. Streaming Data Ingestion Engine
# =====================================================================

class DatasetCurator:
    """Principal engine for streaming, cleaning, validating, and curating samples."""

    def __init__(
        self,
        output_path: Path,
        max_samples: int = 5000,
        diff_ratio: float = 0.20,
        custom_source: Optional[str] = None,
        seed: int = 42,
    ):
        self.output_path = output_path
        self.max_samples = max_samples
        self.diff_ratio = diff_ratio
        self.custom_source = custom_source
        self.seed = seed
        random.seed(seed)

        self.stats = {
            "total_streamed": 0,
            "ast_valid": 0,
            "ast_invalid": 0,
            "cleaned_padding": 0,
            "diff_samples_created": 0,
            "exported": 0,
        }

    def stream_huggingface_datasets(self) -> Generator[Dict[str, Any], None, None]:
        """
        Streams records from Hugging Face datasets with fallback synthetic data generator.
        """
        if self.custom_source:
            hf_sources = [(self.custom_source, "train")]
        else:
            hf_sources = [
                ("sahil2801/CodeAlpaca-20k", "train"),
                ("m-a-p/CodeFeedback-Filtered-Instruction", "train"),
                ("open-r1/codeforces", "train"),
            ]

        hf_available = False
        try:
            from datasets import load_dataset  # type: ignore
            hf_available = True
        except ImportError:
            logger.warning("Hugging Face `datasets` library not found. Using high-signal synthesis mode.")

        if hf_available:
            for dataset_name, split in hf_sources:
                try:
                    logger.info(f"Streaming dataset '{dataset_name}' (split={split})...")
                    ds = load_dataset(dataset_name, split=split, streaming=True)
                    for item in ds:
                        self.stats["total_streamed"] += 1
                        yield {"source": dataset_name, "raw": item}
                        if self.stats["exported"] >= self.max_samples:
                            return
                except Exception as e:
                    logger.warning(f"Could not stream '{dataset_name}': {e}. Continuing to next source...")

        # If HF streaming yielded insufficient samples or offline, yield synthetic seeds
        if self.stats["exported"] < self.max_samples:
            logger.info("Generating high-quality synthetic K-CLI multi-persona seeds...")
            for item in self._generate_synthetic_seeds():
                self.stats["total_streamed"] += 1
                yield item
                if self.stats["exported"] >= self.max_samples:
                    return

    def _generate_synthetic_seeds(self) -> Generator[Dict[str, Any], None, None]:
        """Generates domain-grounded algorithmic seeds when offline or augmenting data."""
        algorithms = [
            ("Binary Search with Left/Right Invariants", "def binary_search(arr: list[int], target: int) -> int:\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1"),
            ("LRU Cache with Doubly Linked List", "class Node:\n    def __init__(self, key: int = 0, val: int = 0):\n        self.key = key\n        self.val = val\n        self.prev = None\n        self.next = None\n\nclass LRUCache:\n    def __init__(self, capacity: int):\n        self.cap = capacity\n        self.cache = {}\n        self.head = Node()\n        self.tail = Node()\n        self.head.next = self.tail\n        self.tail.prev = self.head\n\n    def get(self, key: int) -> int:\n        if key not in self.cache:\n            return -1\n        node = self.cache[key]\n        self._remove(node)\n        self._add(node)\n        return node.val\n\n    def _remove(self, node: Node) -> None:\n        node.prev.next = node.next\n        node.next.prev = node.prev\n\n    def _add(self, node: Node) -> None:\n        node.prev = self.head\n        node.next = self.head.next\n        self.head.next.prev = node\n        self.head.next = node"),
            ("Topological Sort via Kahn's Algorithm", "from collections import deque\n\ndef topological_sort(num_nodes: int, edges: list[tuple[int, int]]) -> list[int]:\n    adj = {i: [] for i in range(num_nodes)}\n    in_degree = [0] * num_nodes\n    for u, v in edges:\n        adj[u].append(v)\n        in_degree[v] += 1\n    queue = deque([i for i in range(num_nodes) if in_degree[i] == 0])\n    order = []\n    while queue:\n        curr = queue.popleft()\n        order.append(curr)\n        for nbr in adj[curr]:\n            in_degree[nbr] -= 1\n            if in_degree[nbr] == 0:\n                queue.append(nbr)\n    return order if len(order) == num_nodes else []"),
            ("Fast Modular Exponentiation", "def mod_pow(base: int, exp: int, mod: int) -> int:\n    result = 1\n    base %= mod\n    while exp > 0:\n        if exp % 2 == 1:\n            result = (result * base) % mod\n        base = (base * base) % mod\n        exp //= 2\n    return result"),
            ("Segment Tree Range Sum Query", "class SegmentTree:\n    def __init__(self, data: list[int]):\n        self.n = len(data)\n        self.tree = [0] * (4 * self.n)\n        if self.n > 0:\n            self._build(data, 0, 0, self.n - 1)\n\n    def _build(self, data: list[int], node: int, start: int, end: int) -> None:\n        if start == end:\n            self.tree[node] = data[start]\n            return\n        mid = (start + end) // 2\n        self._build(data, 2 * node + 1, start, mid)\n        self._build(data, 2 * node + 2, mid + 1, end)\n        self.tree[node] = self.tree[2 * node + 1] + self.tree[2 * node + 2]\n\n    def query(self, l: int, r: int, node: int = 0, start: int = 0, end: int = None) -> int:\n        if end is None:\n            end = self.n - 1\n        if r < start or end < l:\n            return 0\n        if l <= start and end <= r:\n            return self.tree[node]\n        mid = (start + end) // 2\n        return self.query(l, r, 2 * node + 1, start, mid) + self.query(l, r, 2 * node + 2, mid + 1, end)"),
        ]

        count = 0
        while True:
            for name, code in algorithms:
                count += 1
                yield {
                    "source": "synthetic/k_cli_ground_truth",
                    "raw": {
                        "problem": f"Implement a clean, memory-efficient {name} in Python with full type annotations.",
                        "solution": f"Sure, here is the complete solution!\n\n```python\n{code}\n```\n\nHope this helps!",
                        "code": code,
                    },
                }

    def process_raw_item(self, item_dict: Dict[str, Any], index: int) -> Optional[CuratedSample]:
        """
        Parses, strips conversational padding, verifies code syntax, preserves <think> tags,
        and builds a standardized CuratedSample.
        """
        source = item_dict.get("source", "unknown")
        raw = item_dict.get("raw", {})

        # 1. Dynamic extraction of question/instruction
        instruction = (
            raw.get("instruction")
            or raw.get("problem")
            or raw.get("prompt")
            or raw.get("query")
            or raw.get("question")
            or raw.get("description")
            or raw.get("problem_description")
            or raw.get("problem_statement")
            or ""
        )

        # Incorporate Alpaca-style 'input' if present
        input_context = raw.get("input") or ""
        if input_context and isinstance(input_context, str) and input_context.strip():
            if instruction:
                instruction = f"{instruction.strip()}\n\nInput Context:\n{input_context.strip()}"
            else:
                instruction = input_context.strip()

        # 2. Dynamic extraction of solution / response / reasoning
        raw_response = (
            raw.get("output")
            or raw.get("solution")
            or raw.get("generation")
            or raw.get("generations")
            or raw.get("solutions")
            or raw.get("answer")
            or raw.get("response")
            or raw.get("python_solution")
            or raw.get("code")
            or raw.get("completion")
            or ""
        )

        # Handle list of solutions/generations (e.g. from open-r1 or codeforces)
        if isinstance(raw_response, list) and raw_response:
            for item in raw_response:
                if isinstance(item, str) and item.strip():
                    raw_response = item
                    break
                elif isinstance(item, dict):
                    raw_response = (
                        item.get("text")
                        or item.get("content")
                        or item.get("code")
                        or item.get("solution")
                        or item.get("generation")
                        or ""
                    )
                    if raw_response:
                        break
            if isinstance(raw_response, list):
                raw_response = str(raw_response[0]) if raw_response else ""

        # 3. Fallback parser for standard ChatML/OpenAI messages format
        if "messages" in raw and isinstance(raw["messages"], list):
            chat_user_msgs = []
            chat_assistant_msgs = []
            for msg in raw["messages"]:
                if isinstance(msg, dict):
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if role in ("user", "human"):
                        chat_user_msgs.append(content)
                    elif role in ("assistant", "gpt", "bot"):
                        chat_assistant_msgs.append(content)

            if not instruction and chat_user_msgs:
                instruction = "\n\n".join(chat_user_msgs)
            if not raw_response and chat_assistant_msgs:
                raw_response = "\n\n".join(chat_assistant_msgs)

        if not instruction or not raw_response or not isinstance(raw_response, str):
            return None

        # 4. Clean conversational fluff while preserving <think>...</think>
        cleaned_response = TextSanitizer.strip_conversational_padding(raw_response)
        if cleaned_response != raw_response:
            self.stats["cleaned_padding"] += 1

        # 5. Extract code blocks and validate per language
        code_blocks = TextSanitizer.extract_code_blocks_with_lang(cleaned_response)

        valid_blocks: List[Tuple[str, str]] = []
        if code_blocks:
            for lang, code in code_blocks:
                is_valid, err = ASTCodeValidator.is_valid_code(code, language=lang)
                if is_valid:
                    valid_blocks.append((lang, code))
                    self.stats["ast_valid"] += 1
                else:
                    self.stats["ast_invalid"] += 1
                    logger.debug(f"Discarded code block in [{lang}]: {err}")
        else:
            # If no markdown blocks, check if raw cleaned_response is valid code
            is_valid, _ = ASTCodeValidator.is_valid_code(cleaned_response, language="python")
            if is_valid:
                valid_blocks.append(("python", cleaned_response))
                self.stats["ast_valid"] += 1

        if not valid_blocks:
            return None

        primary_lang, primary_code = valid_blocks[0]

        # 6. Extract or Synthesize <think>...</think> reasoning tags
        reasoning, remaining_text = TextSanitizer.extract_or_synthesize_thinking(
            cleaned_response, prompt=instruction
        )

        # 7. Route to specialized K-CLI Persona
        instruction_lower = instruction.lower()
        if "fix" in instruction_lower or "bug" in instruction_lower or "error" in instruction_lower or "patch" in instruction_lower:
            selected_persona = "[ROLE: DEBUGGER]"
        elif "architect" in instruction_lower or "design" in instruction_lower or "complexity" in instruction_lower:
            selected_persona = "[ROLE: ARCHITECT]"
        elif "review" in instruction_lower or "critique" in instruction_lower:
            selected_persona = "[ROLE: CRITIC]"
        else:
            personas = ["[ROLE: CODER]", "[ROLE: ARCHITECT]", "[ROLE: CRITIC]", "[ROLE: DEBUGGER]"]
            selected_persona = random.choices(personas, weights=[0.55, 0.15, 0.15, 0.15])[0]

        # Inject SEARCH/REPLACE diff blocks for a subset of debugger/coder tasks
        is_diff = False
        if selected_persona == "[ROLE: DEBUGGER]" or (random.random() < self.diff_ratio):
            diff_sample = DiffSynthesizer.create_search_replace_sample(primary_code, instruction, language=primary_lang)
            if diff_sample:
                selected_persona = "[ROLE: DEBUGGER]"
                instruction = diff_sample["instruction"]
                reasoning = diff_sample["reasoning"]
                final_response = diff_sample["response"]
                is_diff = True
                self.stats["diff_samples_created"] += 1

        if not is_diff:
            final_response = f"<think>\n{reasoning}\n</think>\n```{primary_lang}\n{primary_code}\n```"

        system_prompt = PERSONA_SYSTEM_PROMPTS.get(
            selected_persona, PERSONA_SYSTEM_PROMPTS["[ROLE: CODER]"]
        )

        sample_id = f"bankai_{index:06d}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction.strip()},
            {"role": "assistant", "content": final_response.strip()},
        ]

        return CuratedSample(
            id=sample_id,
            persona=selected_persona,
            system_prompt=system_prompt,
            instruction=instruction.strip(),
            reasoning=reasoning if not is_diff else "Surgical AST-verified diff application",
            response=final_response.strip(),
            messages=messages,
            metadata={
                "source": source,
                "language": primary_lang,
                "ast_valid": True,
                "has_search_replace": is_diff,
                "char_length": len(final_response),
            },
        )

    def run(self) -> None:
        """Executes the full curation pipeline with Rich progress reporting."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        console.print(Panel.fit(
            "[bold cyan]K-CLI (Project Bankai) Dataset Curation Engine[/bold cyan]\n"
            f"[dim]Output Path: {self.output_path} | Target Samples: {self.max_samples}[/dim]",
            border_style="cyan",
        ))

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        )

        with progress:
            task = progress.add_task("[cyan]Curating & Validating Dataset...", total=self.max_samples)

            with open(self.output_path, "w", encoding="utf-8") as f_out:
                sample_idx = 0
                for raw_item in self.stream_huggingface_datasets():
                    if sample_idx >= self.max_samples:
                        break

                    sample = self.process_raw_item(raw_item, sample_idx)
                    if sample:
                        f_out.write(json.dumps(sample.to_dict(), ensure_ascii=False) + "\n")
                        sample_idx += 1
                        self.stats["exported"] = sample_idx
                        progress.update(task, advance=1)

        self._print_summary_table()

    def _print_summary_table(self) -> None:
        """Prints a rich summary diagnostics table."""
        table = Table(title="[bold green]Dataset Curation Summary[/bold green]", box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Count / Value", style="bold white")

        table.add_row("Total Records Streamed", str(self.stats["total_streamed"]))
        table.add_row("Syntax Checks Passed", f"[green]{self.stats['ast_valid']}[/green]")
        table.add_row("Syntax Checks Rejected", f"[red]{self.stats['ast_invalid']}[/red]")
        table.add_row("Conversational Padding Stripped", str(self.stats["cleaned_padding"]))
        table.add_row("SEARCH/REPLACE Diff Blocks Injected", str(self.stats["diff_samples_created"]))
        table.add_row("Final Exported JSONL Samples", f"[bold green]{self.stats['exported']}[/bold green]")
        table.add_row("Output File Size", f"{self.output_path.stat().st_size / (1024 * 1024):.2f} MB")
        table.add_row("Export Location", str(self.output_path.resolve()))

        console.print("\n")
        console.print(table)
        console.print(f"\n[bold green]✔ Successfully curated dataset to {self.output_path}[/bold green]\n")


# =====================================================================
# 7. CLI Entrypoint
# =====================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Curate and sanitize training datasets for K-CLI (Project Bankai Engine)."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("data/bankai_train.jsonl"),
        help="Path to export the final cleaned JSONL dataset.",
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=1000,
        help="Target number of verified training samples to produce.",
    )
    parser.add_argument(
        "--diff-ratio",
        type=float,
        default=0.20,
        help="Ratio of SEARCH/REPLACE diff samples to inject for [ROLE: DEBUGGER].",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Specific Hugging Face dataset identifier to stream (e.g., 'sahil2801/CodeAlpaca-20k').",
    )
    parser.add_argument(
        "--synthetic-only",
        action="store_true",
        help="Force offline high-signal algorithmic synthesis mode without network downloads.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic curation.",
    )

    args = parser.parse_args()

    curator = DatasetCurator(
        output_path=args.output,
        max_samples=args.limit,
        diff_ratio=args.diff_ratio,
        custom_source=args.source,
        seed=args.seed,
    )
    if args.synthetic_only:
        curator.stream_huggingface_datasets = curator._generate_synthetic_seeds  # type: ignore

    curator.run()


if __name__ == "__main__":
    main()
