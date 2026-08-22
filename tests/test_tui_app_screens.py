"""
test_tui_app_screens.py - Unit Tests for KCliCyberWorkstation, Widgets & Modals
Project Bankai Engine v0.4.0
"""

import os
from unittest.mock import MagicMock, patch
import pytest

from k_cli.tui_app import (
    KCliCyberWorkstation,
    CredentialsVaultModal,
    ConflictStudioWidget,
    GitHubCommandCenterWidget,
    ModelHubWidget,
)


def test_kcli_cyber_workstation_init():
    """Verifies that KCliCyberWorkstation initializes with title, sub_title and bindings."""
    app = KCliCyberWorkstation()
    assert app.TITLE == "K-CLI"
    assert "Agentic Coding Workstation" in app.SUB_TITLE
    assert len(app.BINDINGS) >= 5


def test_credentials_vault_modal_structure_and_labels():
    """Verifies CredentialsVaultModal widgets and status label resolution."""
    modal = CredentialsVaultModal()
    assert modal._get_status_label("NON_EXISTENT_KEY_12345") == "○ Missing"

    with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaTestKey"}):
        assert modal._get_status_label("GEMINI_API_KEY") == "✔ Active"


def test_conflict_studio_widget_methods():
    """Verifies ConflictStudioWidget scanning and actions."""
    widget = ConflictStudioWidget()
    with patch("k_cli.tui_app.ConflictResolver.find_conflicts", return_value=[]):
        widget.refresh_conflicts = MagicMock()
        widget.on_accept = MagicMock()
        widget.on_resolve_all = MagicMock()

        assert callable(widget.refresh_conflicts)
        assert callable(widget.on_accept)


def test_github_command_center_widget():
    """Verifies GitHubCommandCenterWidget methods."""
    widget = GitHubCommandCenterWidget()
    assert hasattr(widget, "refresh_github_items")
    assert hasattr(widget, "on_solve_btn")
    assert hasattr(widget, "on_review_btn")
    assert hasattr(widget, "on_release_btn")


def test_model_hub_widget():
    """Verifies ModelHubWidget methods."""
    widget = ModelHubWidget()
    assert hasattr(widget, "refresh_models")
    assert hasattr(widget, "on_bench_btn")
    assert hasattr(widget, "on_pull_btn")
    assert hasattr(widget, "on_switch_btn")
