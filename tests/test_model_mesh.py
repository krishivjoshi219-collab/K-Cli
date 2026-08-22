import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

try:
    import k_cli.model_mesh as model_mesh
except ModuleNotFoundError:
    import model_mesh


def test_parse_model_target_variants():
    plain = model_mesh.parse_model_target("gpt-4o")
    assert plain.provider is None
    assert plain.model == "gpt-4o"

    provider = model_mesh.parse_model_target("openai:gpt-4o")
    assert provider.provider == "openai"
    assert provider.model == "gpt-4o"

    endpoint = model_mesh.parse_model_target("openai-compatible:my-model@https://models.example/v1")
    assert endpoint.provider == "openai-compatible"
    assert endpoint.model == "my-model"
    assert endpoint.base_url == "https://models.example/v1"


def test_fetch_global_model_index_parses_entries():
    payload = {
        "data": [
            {
                "id": "anthropic/claude-3.7-sonnet",
                "name": "Claude Sonnet",
                "description": "Powerful coding and reasoning model",
                "context_length": 200000,
                "top_provider": {"name": "anthropic"},
                "pricing": {"prompt": "0.000003", "completion": "0.000015"},
            }
        ]
    }
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response

    with patch("urllib.request.urlopen", return_value=response):
        rows = model_mesh.fetch_global_model_index()

    assert len(rows) == 1
    assert rows[0].model_id == "anthropic/claude-3.7-sonnet"
    assert rows[0].specialty in {"coding", "reasoning", "general"}


def test_run_model_mesh_returns_results(monkeypatch):
    class FakeDriver:
        def __init__(self, model_name, mock_mode, provider, openai_base_url):
            self.model_name = model_name

        def generate(self, prompt, temperature=0.2):
            return f"{self.model_name}:{prompt}"

    monkeypatch.setattr(model_mesh, "LLMDriver", FakeDriver)
    targets = [
        model_mesh.ModelTarget(provider="openai", model="gpt-4o"),
        model_mesh.ModelTarget(provider="gemini", model="gemini-2.5-pro"),
    ]
    results = model_mesh.run_model_mesh("write code", targets, mock=False)
    assert len(results) == 2
    assert all(item.success for item in results)
    assert all("write code" in item.output for item in results)


def test_api_key_vault_file_backend_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(model_mesh, "keyring", None)
    monkeypatch.setenv("KCLI_VAULT_PASSPHRASE", "strong-passphrase")
    store = tmp_path / "secure_keys.json"
    vault = model_mesh.APIKeyVault(storage_path=store)

    backend = vault.set_key("openai", "sk-test-token-123")
    assert backend == "encrypted-file"
    assert store.exists()
    assert vault.get_key("openai") == "sk-test-token-123"
    assert vault.export_to_env("openai") is True
    assert os.environ["OPENAI_API_KEY"] == "sk-test-token-123"
