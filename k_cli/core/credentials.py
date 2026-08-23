"""
credentials.py - Universal Credentials & API Key Manager for K-CLI
Project Bankai Engine v0.4.0

Provides multi-tier key discovery, interactive terminal setup, and persistent storage
for all AI model providers and GitHub tokens.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("k_cli.core.credentials")

SUPPORTED_KEYS = [
    ("GEMINI_API_KEY", "Google Gemini API Key", "AIzaSy..."),
    ("ANTHROPIC_API_KEY", "Anthropic Claude API Key", "sk-ant-..."),
    ("OPENAI_API_KEY", "OpenAI API Key", "sk-proj-..."),
    ("DEEPSEEK_API_KEY", "DeepSeek API Key", "sk-..."),
    ("GROQ_API_KEY", "Groq Fast Inference API Key", "gsk_..."),
    ("MISTRAL_API_KEY", "Mistral AI API Key", "..."),
    ("OPENROUTER_API_KEY", "OpenRouter Multi-Model Key", "sk-or-..."),
    ("GITHUB_TOKEN", "GitHub Personal Access Token", "ghp_..."),
    ("OLLAMA_URL", "Local Ollama Endpoint URL", "http://localhost:11434"),
]


class CredentialsManager:
    """
    Central API Key & Credentials Store for K-CLI.
    """

    CRED_DIR = Path.home() / ".kcli"
    ENV_FILE = CRED_DIR / "credentials.env"
    JSON_FILE = CRED_DIR / "credentials.json"

    @classmethod
    def load_all_credentials(cls) -> Dict[str, str]:
        """
        Loads all credentials into os.environ from files, environment, and common locations.
        """
        loaded: Dict[str, str] = {}

        # 1. Load from ~/.kcli/credentials.env
        if cls.ENV_FILE.exists():
            try:
                for line in cls.ENV_FILE.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip()
                        if k and v:
                            os.environ[k] = v
                            loaded[k] = v
            except Exception:
                pass

        # 2. Load from ~/.kcli/credentials.json
        if cls.JSON_FILE.exists():
            try:
                data = json.loads(cls.JSON_FILE.read_text(encoding="utf-8"))
                for k, v in data.items():
                    if isinstance(v, str) and v.strip():
                        os.environ[k] = v.strip()
                        loaded[k] = v.strip()
            except Exception:
                pass

        # 3. Load from local .env / key.json if present in cwd or parents
        cwd = Path.cwd()
        candidates = [
            cwd / ".env",
            cwd / "key.json",
            cwd.parent / ".env",
            cwd.parent / "key.json",
            Path.home() / "BankaiProject" / "key.json",
            Path.home() / ".env",
        ]
        for cand in candidates:
            if cand.exists():
                try:
                    if cand.suffix == ".json":
                        data = json.loads(cand.read_text(encoding="utf-8"))
                        for k, v in data.items():
                            if isinstance(v, str) and v.strip() and k in [sk[0] for sk in SUPPORTED_KEYS]:
                                if k not in os.environ:
                                    os.environ[k] = v.strip()
                                loaded[k] = v.strip()
                    else:
                        for line in cand.read_text(encoding="utf-8").splitlines():
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k, v = line.split("=", 1)
                                k, v = k.strip(), v.strip()
                                if k in [sk[0] for sk in SUPPORTED_KEYS] and v:
                                    if k not in os.environ:
                                        os.environ[k] = v
                                    loaded[k] = v
                except Exception:
                    pass

        return loaded

    @classmethod
    def set_key(cls, key_name: str, key_val: str) -> None:
        """
        Saves a single key to persistent storage and active os.environ.
        """
        key_name = key_name.strip().upper()
        key_val = key_val.strip()
        if not key_name:
            return
        os.environ[key_name] = key_val

        cls.CRED_DIR.mkdir(parents=True, exist_ok=True)
        existing = {}
        if cls.JSON_FILE.exists():
            try:
                existing = json.loads(cls.JSON_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        existing[key_name] = key_val
        cls.JSON_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")

        # Also write .env format
        env_lines = [f"{k}={v}" for k, v in existing.items() if v]
        cls.ENV_FILE.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    @classmethod
    def get_key_statuses(cls) -> List[Dict[str, Any]]:
        """
        Returns status summary for all supported keys.
        """
        cls.load_all_credentials()
        statuses = []
        for key_name, label, placeholder in SUPPORTED_KEYS:
            val = os.environ.get(key_name, "")
            is_active = bool(val and len(val.strip()) > 0)
            masked = f"{val[:4]}...{val[-4:]}" if len(val) >= 10 else ("***" if val else "")
            statuses.append({
                "key": key_name,
                "label": label,
                "active": is_active,
                "masked": masked,
                "placeholder": placeholder,
            })
        return statuses

    @classmethod
    def test_key_connectivity(cls, key_name: str) -> Tuple[bool, str]:
        """
        Quick connectivity test for a specific provider key.
        """
        val = os.environ.get(key_name, "").strip()
        if not val and key_name != "OLLAMA_URL":
            return False, "Key missing"

        if key_name == "OLLAMA_URL":
            url = val or "http://localhost:11434"
            try:
                req = urllib.request.Request(f"{url}/api/tags", headers={"User-Agent": "K-CLI"})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    if resp.status == 200:
                        return True, "Ollama running"
            except Exception as e:
                return False, f"Ollama not reachable: {e}"

        elif key_name == "GEMINI_API_KEY":
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={val}"
                req = urllib.request.Request(url, headers={"User-Agent": "K-CLI"})
                with urllib.request.urlopen(req, timeout=4.0) as resp:
                    if resp.status == 200:
                        return True, "Gemini connected"
            except Exception as e:
                return False, f"Auth failed ({e})"

        elif key_name == "GITHUB_TOKEN":
            try:
                req = urllib.request.Request(
                    "https://api.github.com/user",
                    headers={"Authorization": f"Bearer {val}", "User-Agent": "K-CLI", "Accept": "application/vnd.github.v3+json"},
                )
                with urllib.request.urlopen(req, timeout=4.0) as resp:
                    if resp.status == 200:
                        return True, "GitHub connected"
            except Exception as e:
                return False, f"GitHub auth failed ({e})"

        # Default check for others
        return True, "Key configured"
