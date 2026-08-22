"""Concurrent multi-model orchestration, public model indexing, and API key vaulting."""

from __future__ import annotations

import base64
import concurrent.futures
import hashlib
import hmac
import json
import os
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

try:
    import keyring  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    keyring = None

try:
    from k_cli.llm_driver import LLMDriver
except ModuleNotFoundError:
    from llm_driver import LLMDriver


PROVIDER_ENV_MAP = {
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "openai-compatible": "KCLI_API_KEY",
}


@dataclass(frozen=True)
class ModelTarget:
    provider: Optional[str]
    model: str
    base_url: Optional[str] = None


@dataclass(frozen=True)
class ModelMeshResult:
    target: ModelTarget
    success: bool
    output: str
    latency_ms: int
    error: Optional[str] = None


@dataclass(frozen=True)
class ModelIndexEntry:
    model_id: str
    name: str
    provider: str
    context_length: Optional[int]
    pricing_summary: str
    specialty: str
    description: str


def parse_model_target(spec: str) -> ModelTarget:
    """Parse target string syntax: `model`, `provider:model`, or `provider:model@base_url`."""
    raw = (spec or "").strip()
    if not raw:
        raise ValueError("Empty model target")
    base_url = None
    if "@" in raw:
        raw, base_url = raw.rsplit("@", 1)
        base_url = base_url.strip() or None
    if ":" in raw:
        provider, model = raw.split(":", 1)
        provider = provider.strip().lower() or None
        model = model.strip()
    else:
        provider, model = None, raw
    if not model:
        raise ValueError(f"Invalid model target: {spec}")
    return ModelTarget(provider=provider, model=model, base_url=base_url)


def _infer_specialty(text: str) -> str:
    lower = text.lower()
    if any(token in lower for token in ("coder", "code", "program", "software", "dev")):
        return "coding"
    if any(token in lower for token in ("reason", "math", "think", "logic")):
        return "reasoning"
    if any(token in lower for token in ("vision", "image", "multimodal", "video")):
        return "multimodal"
    if any(token in lower for token in ("translation", "lingual", "language")):
        return "language"
    if any(token in lower for token in ("cheap", "fast", "mini", "flash", "haiku")):
        return "speed"
    return "general"


def fetch_global_model_index(timeout: float = 20.0) -> List[ModelIndexEntry]:
    """Fetch model catalog from OpenRouter and infer model specialties."""
    req = urllib.request.Request("https://openrouter.ai/api/v1/models", method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    data = payload.get("data", [])
    entries: List[ModelIndexEntry] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        model_id = str(row.get("id") or "").strip()
        if not model_id:
            continue
        name = str(row.get("name") or model_id).strip()
        description = str(row.get("description") or "").strip()
        provider = str((row.get("top_provider") or {}).get("name") or "unknown").strip() or "unknown"
        context_len = row.get("context_length")
        if isinstance(context_len, float):
            context_len = int(context_len)
        if not isinstance(context_len, int):
            context_len = None
        pricing = row.get("pricing") or {}
        in_price = pricing.get("prompt")
        out_price = pricing.get("completion")
        pricing_summary = f"in={in_price or 'n/a'}, out={out_price or 'n/a'}"
        specialty = _infer_specialty(f"{model_id} {name} {description}")
        entries.append(
            ModelIndexEntry(
                model_id=model_id,
                name=name,
                provider=provider,
                context_length=context_len,
                pricing_summary=pricing_summary,
                specialty=specialty,
                description=description,
            )
        )
    return entries


def search_model_index(entries: List[ModelIndexEntry], query: str, limit: int = 20) -> List[ModelIndexEntry]:
    """Filter model index entries by query and return first N matches."""
    q = (query or "").strip().lower()
    if not q:
        return entries[:limit]
    filtered = [
        item
        for item in entries
        if q in item.model_id.lower()
        or q in item.name.lower()
        or q in item.provider.lower()
        or q in item.specialty.lower()
        or q in item.description.lower()
    ]
    return filtered[:limit]


class APIKeyVault:
    """Store provider API keys in OS keyring, with encrypted file fallback."""

    def __init__(self, service_name: str = "k-cli", storage_path: Optional[Path] = None):
        self.service_name = service_name
        self.storage_path = storage_path or (Path.home() / ".kcli" / "secure_keys.json")

    def _normalize_provider(self, provider: str) -> str:
        val = (provider or "").strip().lower()
        if val not in PROVIDER_ENV_MAP:
            raise ValueError(f"Unsupported provider '{provider}'")
        return val

    def set_key(self, provider: str, api_key: str) -> str:
        provider = self._normalize_provider(provider)
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")
        if keyring is not None:
            keyring.set_password(self.service_name, provider, api_key.strip())
            return "keyring"
        self._set_file_key(provider, api_key.strip())
        return "encrypted-file"

    def get_key(self, provider: str) -> Optional[str]:
        provider = self._normalize_provider(provider)
        if keyring is not None:
            return keyring.get_password(self.service_name, provider)
        return self._get_file_key(provider)

    def export_to_env(self, provider: str) -> bool:
        provider = self._normalize_provider(provider)
        val = self.get_key(provider)
        if not val:
            return False
        os.environ[PROVIDER_ENV_MAP[provider]] = val
        return True

    def _derive_key(self, salt: bytes) -> bytes:
        passphrase = os.getenv("KCLI_VAULT_PASSPHRASE")
        if not passphrase:
            raise RuntimeError("KCLI_VAULT_PASSPHRASE is required when keyring is unavailable")
        return hashlib.scrypt(passphrase.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)

    @staticmethod
    def _xor_stream(data: bytes, seed: bytes) -> bytes:
        out = bytearray(len(data))
        block = b""
        counter = 0
        idx = 0
        while idx < len(data):
            if not block:
                block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
                counter += 1
            take = min(len(block), len(data) - idx)
            for i in range(take):
                out[idx + i] = data[idx + i] ^ block[i]
            idx += take
            block = block[take:]
        return bytes(out)

    def _read_file_store(self) -> Dict[str, Dict[str, str]]:
        if not self.storage_path.exists():
            return {}
        try:
            return json.loads(self.storage_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_file_store(self, data: Dict[str, Dict[str, str]]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.chmod(self.storage_path, 0o600)

    def _set_file_key(self, provider: str, api_key: str) -> None:
        salt = os.urandom(16)
        nonce = os.urandom(16)
        key = self._derive_key(salt)
        ciphertext = self._xor_stream(api_key.encode("utf-8"), key + nonce)
        tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        store = self._read_file_store()
        store[provider] = {
            "salt": base64.b64encode(salt).decode("ascii"),
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
            "tag": base64.b64encode(tag).decode("ascii"),
        }
        self._write_file_store(store)

    def _get_file_key(self, provider: str) -> Optional[str]:
        row = self._read_file_store().get(provider)
        if not row:
            return None
        salt = base64.b64decode(row["salt"])
        nonce = base64.b64decode(row["nonce"])
        ciphertext = base64.b64decode(row["ciphertext"])
        tag = base64.b64decode(row["tag"])
        key = self._derive_key(salt)
        expected = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected):
            raise RuntimeError("Encrypted key store integrity check failed")
        plaintext = self._xor_stream(ciphertext, key + nonce)
        return plaintext.decode("utf-8")


def run_model_mesh(
    prompt: str,
    targets: List[ModelTarget],
    mock: bool = False,
    temperature: float = 0.2,
    max_workers: int = 8,
) -> List[ModelMeshResult]:
    """Run one prompt against multiple model targets concurrently."""
    if not targets:
        return []

    def _run(target: ModelTarget) -> ModelMeshResult:
        started = time.perf_counter()
        try:
            driver = LLMDriver(
                model_name=target.model,
                mock_mode=mock,
                provider=target.provider,
                openai_base_url=target.base_url,
            )
            output = driver.generate(prompt, temperature=temperature)
            latency_ms = int((time.perf_counter() - started) * 1000)
            return ModelMeshResult(target=target, success=True, output=output, latency_ms=latency_ms)
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return ModelMeshResult(target=target, success=False, output="", latency_ms=latency_ms, error=str(exc))

    results: List[ModelMeshResult] = []
    workers = max(1, min(max_workers, len(targets)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_run, target) for target in targets]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: (item.target.provider or "auto", item.target.model))
    return results
