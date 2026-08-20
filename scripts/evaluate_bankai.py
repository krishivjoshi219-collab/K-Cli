#!/usr/bin/env python3
"""
scripts/evaluate_bankai.py
━━━━━━━━━━━━━━━━━━━━━━━━━━
50-Sample Adversarial Test Harness & Error Profiling for Project Bankai.

Evaluates Bankai models (bankai:3b, bankai:7b, etc.) across 3 specialized roles:
1. [CODER] (20 tests): Complex Python AST (decorators, generators, async pools, dataclasses).
2. [DEBUGGER] (15 tests): Surgical SEARCH/REPLACE diff blocks (validates SEARCH != REPLACE).
3. [ARCHITECT] (15 tests): Deep reasoning inside <think> tags (>200 words, Big-O proofs).

Outputs structured failures to data/failures_<model_tag>.json for targeted distillation.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

console = Console()

DEFAULT_FAILURES_PATH = Path("data/failures_3b.json")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Test Definitions (50 Adversarial Cases)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TestCase:
    test_id: str
    role: str
    name: str
    prompt: str
    original_code: Optional[str] = None
    expected_big_o: Optional[str] = None


def generate_test_suite() -> List[TestCase]:
    suite: List[TestCase] = []

    # ─────────────────────────────
    # ROLE: CODER (20 Tests)
    # ─────────────────────────────
    coder_prompts = [
        ("CODER-01", "Async Worker Pool with Queue", "Implement an asynchronous worker pool class `AsyncWorkerPool` in Python using `asyncio.Queue` and `asyncio.create_task` with graceful cancellation and error recovery."),
        ("CODER-02", "Memoization Decorator with TTL", "Implement a generic Python decorator `@timed_lru_cache(maxsize=128, ttl_seconds=60)` that caches function results and expires entries after TTL."),
        ("CODER-03", "Thread-Safe Singleton Metaclass", "Implement a thread-safe singleton metaclass `ThreadSafeSingleton` in Python using `threading.Lock` and `__call__`."),
        ("CODER-04", "Chunked Generator Stream", "Write a Python generator function `stream_chunked(iterator, chunk_size: int)` that yields tuples of size `chunk_size` without loading the full iterator into memory."),
        ("CODER-05", "Context Manager for Temporary Environment Variables", "Implement a context manager `temp_environ(**kwargs)` using `@contextmanager` that temporarily sets `os.environ` keys and restores original values on exit."),
        ("CODER-06", "Generic Trie with Autocomplete", "Write a Python `Trie` class with `insert(word: str)`, `search(word: str) -> bool`, and `autocomplete(prefix: str, limit: int = 5) -> list[str]`."),
        ("CODER-07", "Dataclass Serialization with Custom Deserializer", "Create a `@dataclass` `NetworkPacket` with fields `header: str`, `payload: bytes`, `timestamp: float` and custom `to_bytes()` and `@classmethod from_bytes(data: bytes)` methods."),
        ("CODER-08", "Token Bucket Rate Limiter", "Write a Python class `TokenBucketRateLimiter` with `consume(tokens: int = 1) -> bool` using monotonic time and thread safety."),
        ("CODER-09", "Binary Min-Heap from Scratch", "Implement a complete binary min-heap `MinHeap` in Python with `push(val)`, `pop() -> int`, `peek() -> int`, `heapify(arr)` without using `heapq`."),
        ("CODER-10", "Custom Iterator for Fibonacci Matrix Exponentiation", "Implement a Python class `FibonacciMatrixIterator` that computes the N-th Fibonacci number in O(log N) time using 2x2 matrix multiplication."),
        ("CODER-11", "Segment Tree with Range Sum Query", "Implement a Python `SegmentTree` class for array range sum queries and point updates in O(log N) time."),
        ("CODER-12", "Topological Sort with Cycle Detection", "Write a Python function `topological_sort(num_nodes: int, edges: list[tuple[int, int]]) -> list[int]` that detects directed cycles and raises `ValueError` if cyclic."),
        ("CODER-13", "Async Retry with Exponential Backoff", "Implement an `async def retry_with_backoff(coro_fn, max_retries=3, base_delay=1.0)` helper with jitter and configurable exception filtering."),
        ("CODER-14", "Deep Object Diff Generator", "Write a Python function `deep_diff(obj_a: dict, obj_b: dict) -> dict` that recursively computes added, removed, and modified keys with JSON-compatible dot notation."),
        ("CODER-15", "LRU Cache with Doubly Linked List", "Implement an `LRUCache(capacity: int)` using a custom `Node` and doubly-linked list with O(1) `get` and `put` operations."),
        ("CODER-16", "Disjoint Set Union (Union-Find) with Path Compression", "Implement a `DisjointSetUnion` class with `find(x)` (path compression) and `union(x, y)` (union by rank)."),
        ("CODER-17", "Stream Line Parser with Buffer Overrun Protection", "Write a generator `stream_lines(file_stream, max_line_length=65536)` that reads chunks from a binary stream and yields decoded UTF-8 lines safely."),
        ("CODER-18", "Event Bus with Async Listeners", "Implement an `AsyncEventBus` class with `subscribe(event_name, async_callback)`, `unsubscribe(...)`, and `publish(event_name, *args, **kwargs)`."),
        ("CODER-19", "Circular Ring Buffer", "Implement a fixed-size `CircularRingBuffer(capacity: int)` with `append(val)`, `popleft() -> Any`, `is_full() -> bool`, and indexing `__getitem__`."),
        ("CODER-20", "Fast Inverted Index Builder", "Write a class `InvertedIndex` in Python that tokenizes documents, strips punctuation, normalizes case, and supports boolean AND search."),
    ]
    for tid, name, prompt in coder_prompts:
        suite.append(TestCase(test_id=tid, role="CODER", name=name, prompt=prompt))

    # ─────────────────────────────
    # ROLE: DEBUGGER (15 Tests)
    # ─────────────────────────────
    debugger_cases = [
        ("DEBUG-01", "Off-by-One in Binary Search",
         "The following binary search has an off-by-one error and infinite loop bug. Provide a surgical SEARCH/REPLACE block to fix it.",
         "def binary_search(arr, target):\n    low = 0\n    high = len(arr)\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid\n        else:\n            high = mid\n    return -1"),
        ("DEBUG-02", "Mutable Default Argument in Function",
         "The following function uses a mutable default list that retains state across calls. Provide a SEARCH/REPLACE patch to fix it.",
         "def append_item(item, target_list=[]):\n    target_list.append(item)\n    return target_list"),
        ("DEBUG-03", "Asyncio Task Exception Loss",
         "The following background worker does not await or handle task exceptions. Fix it using a SEARCH/REPLACE diff.",
         "async def process_items(items):\n    tasks = [asyncio.create_task(do_work(item)) for item in items]\n    return 'Started'"),
        ("DEBUG-04", "Incorrect Matrix Transpose in Python",
         "Fix the matrix transpose function which crashes on non-square matrices using a SEARCH/REPLACE block.",
         "def transpose(matrix):\n    return [[matrix[i][j] for i in range(len(matrix[0]))] for j in range(len(matrix))]"),
        ("DEBUG-05", "Division by Zero in Weighted Average",
         "Fix the ZeroDivisionError bug in `weighted_average` when sum of weights is zero using a SEARCH/REPLACE block.",
         "def weighted_average(values, weights):\n    total_weight = sum(weights)\n    return sum(v * w for v, w in zip(values, weights)) / total_weight"),
        ("DEBUG-06", "Dict Key Mutation During Iteration",
         "Fix the RuntimeError: dictionary changed size during iteration using a SEARCH/REPLACE block.",
         "def remove_inactive(users):\n    for uid, user in users.items():\n        if not user['active']:\n            del users[uid]\n    return users"),
        ("DEBUG-07", "Memory Leak in Event Listener List",
         "Fix the reference leak where callbacks are never weakref-ed in `EventManager` using a SEARCH/REPLACE block.",
         "class EventManager:\n    def __init__(self):\n        self.listeners = []\n    def add_listener(self, callback):\n        self.listeners.append(callback)"),
        ("DEBUG-08", "Deadlock in Double Locking",
         "Fix the lock acquisition order in `transfer_funds` to prevent deadlocks using a SEARCH/REPLACE block.",
         "def transfer(acc1, acc2, amount):\n    with acc1.lock:\n        with acc2.lock:\n            acc1.balance -= amount\n            acc2.balance += amount"),
        ("DEBUG-09", "Incorrect String Formatting / SQL Injection Vulnerability",
         "Fix the insecure raw string formatting in SQL query execution using parameterized queries.",
         "def get_user_by_email(cursor, email):\n    query = f\"SELECT * FROM users WHERE email = '{email}'\"\n    cursor.execute(query)\n    return cursor.fetchone()"),
        ("DEBUG-10", "Unclosed File Resource in Exception Path",
         "Fix the resource leak when an exception is raised before `file.close()` using a context manager SEARCH/REPLACE patch.",
         "def read_header(filepath):\n    f = open(filepath, 'r')\n    header = f.readline()\n    validate(header)\n    f.close()\n    return header"),
        ("DEBUG-11", "Flawed Flattening in Recursive Tree",
         "Fix the infinite recursion bug in `flatten_tree` when cycles are present using a visited set SEARCH/REPLACE block.",
         "def flatten(node):\n    res = [node.val]\n    for child in node.children:\n        res.extend(flatten(child))\n    return res"),
        ("DEBUG-12", "Broken QuickSelect Partition Step",
         "Fix the partition index calculation in QuickSelect using a SEARCH/REPLACE block.",
         "def partition(arr, l, r):\n    pivot = arr[r]\n    i = l\n    for j in range(l, r):\n        if arr[j] <= pivot:\n            arr[i], arr[j] = arr[j], arr[i]\n            i += 1\n    return i"),
        ("DEBUG-13", "Incorrect Variable Scope in List Comprehension Loop",
         "Fix the late-binding closure bug in generated lambda list using a default argument in SEARCH/REPLACE.",
         "def make_multipliers(n):\n    return [lambda x: x * i for i in range(n)]"),
        ("DEBUG-14", "Shallow Copy Bug in Nested Dict",
         "Fix the state mutation bug caused by `.copy()` instead of `copy.deepcopy()` in config updates.",
         "def clone_config(default_cfg, overrides):\n    cfg = default_cfg.copy()\n    cfg['db']['host'] = overrides.get('host', 'localhost')\n    return cfg"),
        ("DEBUG-15", "Missing Await in Async Generator Yield",
         "Fix the missing await in async generator pipeline using a SEARCH/REPLACE patch.",
         "async def stream_records(db_pool, query):\n    conn = db_pool.acquire()\n    async for row in conn.cursor(query):\n        yield format_row(row)"),
    ]
    for tid, name, prompt, orig in debugger_cases:
        full_prompt = f"{prompt}\n\n```python\n{orig}\n```\n\nProvide your fix using the exact format:\n<<<<<<< SEARCH\n[code to replace]\n=======\n[replacement code]\n>>>>>>>"
        suite.append(TestCase(test_id=tid, role="DEBUGGER", name=name, prompt=full_prompt, original_code=orig))

    # ─────────────────────────────
    # ROLE: ARCHITECT (15 Tests)
    # ─────────────────────────────
    architect_prompts = [
        ("ARCH-01", "Distributed Rate Limiter Design", "Design a distributed sliding-window rate limiter handling 100,000 req/sec across 10 regions. Explain data structures, Redis Lua scripts, memory requirements, and formal Big-O time/space complexity proof."),
        ("ARCH-02", "LSM-Tree vs B-Tree Storage Engines", "Provide a comprehensive comparative architecture between Log-Structured Merge Trees (LSM) and B+ Trees for write-heavy vs read-heavy database workloads. Include Big-O complexity proofs for read/write/scan."),
        ("ARCH-03", "Zero-Copy High-Throughput Packet Pipeline", "Architect a high-performance network packet parser in C++ using zero-copy memory buffers, ring buffers, and SIMD instructions. Provide mathematical proof of throughput bottlenecks and Big-O memory scaling."),
        ("ARCH-04", "Consistent Hashing with Virtual Nodes", "Explain the formal mathematical mechanics of Consistent Hashing with virtual nodes (vnodes) for distributed caching. Prove replication bounds and O(log N) lookup complexity."),
        ("ARCH-05", "Raft Consensus Log Compaction & Snapshotting", "Architect the snapshotting and log compaction mechanism in Raft consensus. Detail state transition invariants, garbage collection safety, and Big-O network transmission overhead."),
        ("ARCH-06", "Vector Similarity Search at Scale (HNSW)", "Analyze the Hierarchical Navigable Small World (HNSW) graph algorithm for approximate nearest neighbors. Detail graph construction complexity, beam search complexity, and trade-offs against IVF-PQ."),
        ("ARCH-07", "Optimistic Concurrency Control (OCC) in Distributed DB", "Architect an Optimistic Concurrency Control system with read/validate/write phases for high-throughput OLTP. Include formal abort rate probability models and Big-O verification bounds."),
        ("ARCH-08", "Kafka Partition Rebalancing & Distributed Consumer Groups", "Design the partition assignment strategy (Cooperative Sticky Assignor) in Apache Kafka. Prove why it minimizes stop-the-world partition revocations with Big-O analysis."),
        ("ARCH-09", "CRDT (Conflict-Free Replicated Data Types) for Collaborative Text Editing", "Design a state-based RGA (Replicated Growable Array) CRDT for real-time collaborative text editing. Prove convergence invariants, causality tracking via Lamport clocks, and Big-O space amplification."),
        ("ARCH-10", "GPU Kernel Memory Hierarchy Optimization", "Architect a high-performance matrix multiplication (GEMM) CUDA kernel using shared memory tiling, register caching, and warp-level primitives. Include formal memory bandwidth and FLOP/s Big-O limits."),
        ("ARCH-11", "Disaster Recovery Replication: Async vs Sync vs Quorum", "Provide a rigorous trade-off architecture comparing Synchronous, Asynchronous, and Semi-Synchronous Quorum replication under the CAP and PACELC theorems with recovery point objective (RPO) and recovery time objective (RTO) proofs."),
        ("ARCH-12", "Garbage Collection Algorithms in Modern Runtimes", "Architect a concurrent generational Tri-Color garbage collector. Prove why the write barrier prevents illegal references and derive the Big-O pause time bounds."),
        ("ARCH-13", "Distributed Tracing at Million Spans/Sec", "Architect a distributed tracing infrastructure (like OpenTelemetry / Jaeger) with tail-based sampling, bloom filters, and column-store ingestion. Include Big-O storage growth equations."),
        ("ARCH-14", "Actor Model vs CSP Concurrency", "Compare the Actor model (Erlang/Akka) with Communicating Sequential Processes (Go/CSP). Formally evaluate mailbox buffering limits, deadlocking conditions, and Big-O scheduling complexity."),
        ("ARCH-15", "Distributed Global ID Generator (Snowflake vs UUIDv7)", "Design a globally unique, k-sorted, collision-resistant 64-bit ID generator system capable of generating 50M IDs/sec across 128 nodes. Detail clock drift handling and Big-O generation latency."),
    ]
    for tid, name, prompt in architect_prompts:
        suite.append(TestCase(test_id=tid, role="ARCHITECT", name=name, prompt=prompt, expected_big_o="O("))

    return suite


# ─────────────────────────────────────────────────────────────────────────────
# 2. Ollama Query & Evaluation Harness
# ─────────────────────────────────────────────────────────────────────────────

def query_ollama(model_name: str, prompt: str, system_prompt: Optional[str] = None, timeout: int = 120) -> str:
    """Dispatches generation request to local Ollama server."""
    url = "http://localhost:11434/api/generate"
    payload: Dict[str, Any] = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.95,
            "num_predict": 1024,
        },
    }
    if system_prompt:
        payload["system"] = system_prompt

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            return res_json.get("response", "")
    except Exception as e:
        return f"[ERROR: Ollama query failed: {e}]"


def extract_python_code(text: str) -> str:
    """Extracts python code block or returns clean text."""
    matches = re.findall(r"```(?:python)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if matches:
        return max(matches, key=len).strip()
    return text.strip()


def validate_test(test: TestCase, response: str) -> Tuple[bool, Optional[str]]:
    """Validates response against role-specific requirements."""
    if not response or "[ERROR:" in response:
        return False, "Empty or error response from model"

    # [ROLE: CODER]: AST Syntax Validation
    if test.role == "CODER":
        code = extract_python_code(response)
        if not code:
            return False, "No code block found in response"
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"AST SyntaxError at line {e.lineno}: {e.msg}"

    # [ROLE: DEBUGGER]: Surgical Diff Validation
    elif test.role == "DEBUGGER":
        diff_pattern = r"<<<<<<<\s*SEARCH\s*\n(.*?)\n=======\s*\n(.*?)\n>>>>>>>"
        matches = re.findall(diff_pattern, response, flags=re.DOTALL)
        if not matches:
            return False, "Missing or malformed <<<<<<< SEARCH ... ======= ... >>>>>>> diff block"
        
        search_block, replace_block = matches[0]
        search_clean = search_block.strip()
        replace_clean = replace_block.strip()

        if not search_clean:
            return False, "SEARCH block is empty"
        if search_clean == replace_clean:
            return False, "SEARCH block is identical to REPLACE block (no-op diff)"
        if test.original_code and search_clean not in test.original_code:
            # Check if search block is approximately in original code
            compact_search = re.sub(r"\s+", " ", search_clean)
            compact_orig = re.sub(r"\s+", " ", test.original_code)
            if compact_search not in compact_orig:
                return False, "SEARCH block does not match target lines in original buggy code"

        return True, None

    # [ROLE: ARCHITECT]: Depth & Big-O Validation
    elif test.role == "ARCHITECT":
        has_think = ("<think>" in response and "</think>" in response)
        think_text = ""
        if has_think:
            think_match = re.search(r"<think>(.*?)</think>", response, flags=re.DOTALL)
            if think_match:
                think_text = think_match.group(1).strip()
        
        # Word count check (>200 words in response or think block)
        word_count = len(response.split())
        think_word_count = len(think_text.split()) if think_text else 0

        if not has_think:
            return False, "Missing <think>...</think> reasoning block"
        if think_word_count < 100 and word_count < 200:
            return False, f"Reasoning too shallow (<think> words: {think_word_count}, total words: {word_count})"
        
        # Big-O complexity check
        big_o_present = bool(re.search(r"O\([^\)]+\)", response))
        if not big_o_present:
            return False, "Missing formal Big-O complexity proof/notation (e.g., O(N), O(log N))"

        return True, None

    return True, None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Main Evaluation Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_evaluation(model_name: str, failures_output_path: Path) -> Dict[str, Any]:
    console.print(Panel(
        f"[bold cyan]Project Bankai — Adversarial Test Harness (50 Cases)[/bold cyan]\n"
        f"Target Model  : [bold white]{model_name}[/bold white]\n"
        f"Failures Output: [yellow]{failures_output_path}[/yellow]",
        expand=False,
    ))

    suite = generate_test_suite()
    results: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []

    passed_by_role = {"CODER": 0, "DEBUGGER": 0, "ARCHITECT": 0}
    total_by_role = {"CODER": 0, "DEBUGGER": 0, "ARCHITECT": 0}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task(f"[cyan]Evaluating {model_name}...[/cyan]", total=len(suite))

        for test in suite:
            total_by_role[test.role] += 1
            progress.update(task_id, description=f"[cyan]{test.test_id}: {test.name}[/cyan]")
            
            t0 = time.time()
            response = query_ollama(model_name, test.prompt)
            elapsed = time.time() - t0

            passed, error_msg = validate_test(test, response)

            result_entry = {
                "test_id": test.test_id,
                "role": test.role,
                "name": test.name,
                "passed": passed,
                "error": error_msg,
                "elapsed_seconds": round(elapsed, 2),
                "response_length": len(response),
            }
            results.append(result_entry)

            if passed:
                passed_by_role[test.role] += 1
            else:
                failure_entry = {
                    "test_id": test.test_id,
                    "role": test.role,
                    "name": test.name,
                    "prompt": test.prompt,
                    "error": error_msg,
                    "response": response,
                }
                failures.append(failure_entry)

            progress.advance(task_id, 1)

    # Save failures JSON for targeted counter-example generation
    failures_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(failures_output_path, "w", encoding="utf-8") as f:
        json.dump(failures, f, indent=2, ensure_ascii=False)

    # Summary Table
    total_passed = sum(passed_by_role.values())
    total_tests = sum(total_by_role.values())
    overall_accuracy = (total_passed / total_tests) * 100 if total_tests else 0.0

    summary_table = Table(title=f"[bold green]Evaluation Results for {model_name}[/bold green]", show_header=True, header_style="bold magenta", show_lines=True)
    summary_table.add_column("Persona / Role", style="yellow")
    summary_table.add_column("Tests Passed", justify="right", style="bold white")
    summary_table.add_column("Total Tests", justify="right", style="white")
    summary_table.add_column("Pass Rate (%)", justify="right", style="bold green")

    for role in ["CODER", "DEBUGGER", "ARCHITECT"]:
        p = passed_by_role[role]
        t = total_by_role[role]
        rate = (p / t) * 100 if t else 0.0
        summary_table.add_row(role, f"{p}", f"{t}", f"{rate:.1f}%")

    summary_table.add_row("[bold]TOTAL / OVERALL[/bold]", f"[bold green]{total_passed}[/bold green]", f"{total_tests}", f"[bold green]{overall_accuracy:.1f}%[/bold green]")
    console.print("\n")
    console.print(summary_table)
    console.print(f"\n[bold yellow]Logged {len(failures)} failures to {failures_output_path}[/bold yellow]\n")

    return {
        "model_name": model_name,
        "total_tests": total_tests,
        "total_passed": total_passed,
        "overall_accuracy": overall_accuracy,
        "passed_by_role": passed_by_role,
        "total_by_role": total_by_role,
        "failures_count": len(failures),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Adversarial evaluation harness for Project Bankai.")
    parser.add_argument("--model", default="bankai:3b", help="Target Ollama model tag (e.g., bankai:3b, bankai:7b)")
    parser.add_argument("--failures-out", default=str(DEFAULT_FAILURES_PATH), help="Path to write failure JSON")
    args = parser.parse_args()

    failures_path = Path(args.failures_out)
    run_evaluation(args.model, failures_path)


if __name__ == "__main__":
    main()
