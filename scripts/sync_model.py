#!/usr/bin/env python3
"""
scripts/sync_model.py - High-Speed Direct Stream Download for Colab GGUF Artifacts
"""

import sys
import os
import requests
from pathlib import Path
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn, DownloadColumn

from colab_cli.state import StateStore

def sync_gguf(remote_path: str, local_path: str):
    store = StateStore()
    sessions = store.list()
    if not sessions:
        print("Error: No active Colab session found in store.")
        sys.exit(1)
    
    session_name = list(sessions.keys())[0]
    session = sessions[session_name]
    base_url = session.url.rstrip("/")
    token = session.token

    local_file = Path(local_path)
    local_file.parent.mkdir(parents=True, exist_ok=True)

    clean_remote = remote_path.lstrip("/")
    if clean_remote.startswith("content/"):
        clean_remote = clean_remote[len("content/"):]

    # Jupyter /files/ endpoint
    url = f"{base_url}/files/{clean_remote}"
    params = {"authuser": "0", "colab-runtime-proxy-token": token}

    print(f"Connecting to session [{session_name}] stream: {url}")
    resp = requests.get(url, params=params, stream=True, timeout=60)
    
    if resp.status_code != 200:
        url = f"{base_url}/files/content/{clean_remote}"
        print(f"Retrying with content path: {url}")
        resp = requests.get(url, params=params, stream=True, timeout=60)

    resp.raise_for_status()
    total_size = int(resp.headers.get("content-length", 0))
    print(f"Downloading {total_size / (1024*1024):.2f} MB to {local_path}...")

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("Streaming GGUF", total=total_size)
        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024 * 4): # 4MB chunks
                if chunk:
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))

    print(f"✔ Download complete: {local_path} ({os.path.getsize(local_path) / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    remote = sys.argv[1] if len(sys.argv) > 1 else "bankai_1.5b_model_gguf/qwen2.5-coder-1.5b-instruct.Q4_K_M.gguf"
    local = sys.argv[2] if len(sys.argv) > 2 else "/home/k/models/bankai-1.5b.gguf"
    sync_gguf(remote, local)
