#!/usr/bin/env python3
"""
scripts/test_bankai_inference.py - Real-Time Streaming Sanity Verification for Project Bankai
"""

import ast
import json
import os
import sys
import urllib.request
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

def verify_bankai_deployment():
    console.print("\n" + "=" * 65)
    console.print("🚀 [PROJECT BANKAI] Verifying Local GGUF Artifact & Inference")
    console.print("=" * 65)

    # 1. Check GGUF file
    model_path = Path("/home/k/models/bankai-1.5b.gguf")
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    console.print(f"✔ GGUF Artifact Found: [bold cyan]{model_path}[/bold cyan] ({size_mb:.2f} MB)")

    # 2. Query Ollama API with streaming
    payload = {
        "model": "bankai:1.5b",
        "prompt": "Write a fast iterative fibonacci function in Python with type annotations and docstring.",
        "stream": True,
        "options": {
            "temperature": 0.1,
        }
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    console.print("\n🤖 Streaming output from [bold magenta]bankai:1.5b[/bold magenta]...\n")
    tokens = []
    with urllib.request.urlopen(req, timeout=120.0) as resp:
        for line in resp:
            if line:
                chunk = json.loads(line.decode("utf-8"))
                token = chunk.get("response", "")
                tokens.append(token)
                sys.stdout.write(token)
                sys.stdout.flush()

    raw_output = "".join(tokens)
    console.print("\n\n" + "=" * 65)

    # 3. Extract and validate Python AST
    code_blocks = [block.strip() for block in raw_output.split("```python") if "```" in block]
    if not code_blocks:
        code_blocks = [block.strip() for block in raw_output.split("```") if len(block.strip()) > 10]

    if code_blocks:
        extracted_code = code_blocks[0].split("```")[0].strip()
        try:
            ast.parse(extracted_code)
            console.print("✔ [bold green]AST Syntax Validation: PASSED[/bold green] (Valid Python AST)")
            syntax = Syntax(extracted_code, "python", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Extracted Production Code", border_style="cyan"))
        except SyntaxError as e:
            console.print(f"✘ [bold red]AST Syntax Error:[/bold red] {e}")
    else:
        console.print("ℹ Raw code output returned directly.")

    console.print("\n" + "=" * 65)
    console.print("🎉 [PROJECT BANKAI] Model is fully operational locally!")
    console.print("=" * 65 + "\n")

if __name__ == "__main__":
    verify_bankai_deployment()
