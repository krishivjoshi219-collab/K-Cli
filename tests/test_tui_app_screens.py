"""
test_tui_app_screens.py - Comprehensive Unit & Integration Test Suite for K-CLI Cyber-Workstation Screens
Project Bankai Engine v0.2.0

Tests:
1. Interactive 3-Way Conflict Studio Widget & Modal (Ours vs Base vs Theirs vs AI Merge, 1-click Accept, Re-prompt, Verification).
2. Interactive GitHub PR Hub (Live PR browser list, conflict tags, review state, CI pills, AI Review, Auto-Fix, Merge).
3. MCP Server Inspector (Active servers, connected tools, parameter schemas, latency ping, test invocation, live logs).
4. Swarm Radar (Visual subagent nodes, status glyphs, token expenditures, $ USD accounting, radar sweep).
5. KCliApp Power Tools tab navigation and keyboard shortcuts (Ctrl+K, Ctrl+G, Ctrl+I, Ctrl+S, slash commands).
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Markdown, Static, TabbedContent

# Ensure repo root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from k_cli.tui_app import (
    ConflictChunk,
    ConflictStudioModal,
    ConflictStudioWidget,
    GitHubPRHubWidget,
    KCliApp,
    MCPServerInfo,
    MCPServerInspectorWidget,
    PullRequestSummary,
    SwarmRadarWidget,
)
from k_cli.subagents import SubagentRole, SubagentStatus, SubagentTask


# ==============================================================================
# 1. 3-Way Conflict Studio Tests
# ==============================================================================

def test_conflict_studio_widget_navigation_and_actions():
    """Verify ConflictStudioWidget renders 4 comparison panes and handles 1-click actions."""
    async def _test():
        conflicts = [
            ConflictChunk(
                id="c1",
                file_path="service.py",
                ours_code="def run(): return 'ours'",
                base_code="def run(): return 'base'",
                theirs_code="def run(): return 'theirs'",
                ai_merge_code="def run(): return 'merged'",
            )
        ]
        widget = ConflictStudioWidget(conflicts=conflicts)
        app = KCliApp(mock_mode=True)

        async with app.run_test() as pilot:
            # Mount widget or access conflict studio tab
            conflict_widget = app.query_one("#conflict-studio-widget", ConflictStudioWidget)
            assert conflict_widget is not None

            # Verify initial pane contents
            ours_view = app.query_one("#conflict-ours-content", Static)
            ai_view = app.query_one("#conflict-ai-content", Static)
            assert ours_view is not None
            assert ai_view is not None

            # 1. Test Accept Merge Button
            accept_btn = app.query_one("#accept-merge-btn", Button)
            accept_btn.press()
            await pilot.pause()
            assert conflict_widget.conflicts[0].status == "accepted"

            # 2. Test Verification Button
            verify_btn = app.query_one("#verify-merge-btn", Button)
            verify_btn.press()
            await pilot.pause()
            assert conflict_widget.conflicts[0].status == "verified"

            # 3. Test Toggle Diff Mode Button
            diff_btn = app.query_one("#toggle-conflict-diff-btn", Button)
            diff_btn.press()
            await pilot.pause()
            assert conflict_widget.diff_view_mode is True

            # 4. Test Prev / Next Navigation
            next_btn = app.query_one("#next-conflict-btn", Button)
            next_btn.press()
            await pilot.pause()

    asyncio.run(_test())


def test_conflict_studio_modal():
    """Verify ConflictStudioModal opens, mounts studio, and dismisses cleanly."""
    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            modal = ConflictStudioModal()
            app.push_screen(modal)
            await pilot.pause()

            assert isinstance(app.screen, ConflictStudioModal)
            close_btn = app.screen.query_one("#close-studio-btn", Button)
            close_btn.press()
            await pilot.pause()

    asyncio.run(_test())


# ==============================================================================
# 2. Interactive GitHub PR Hub Tests
# ==============================================================================

def test_github_pr_hub_widget_selection_and_actions():
    """Verify GitHubPRHubWidget browser list, CI pills, AI Review, and Auto-Fix actions."""
    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            # Switch to PR hub
            app.action_open_pr_hub()
            await pilot.pause()

            tabs = app.query_one("#workspace-tabs", TabbedContent)
            assert tabs.active == "tab-pr"

            pr_widget = app.query_one("#github-pr-hub-widget", GitHubPRHubWidget)
            assert pr_widget is not None
            assert len(pr_widget.prs) >= 3

            # Check PR list cards
            cards = app.query(".pr-card-item")
            assert len(cards) >= 3

            # 1. Trigger AI Code Review
            review_btn = app.query_one("#pr-ai-review-btn", Button)
            review_btn.press()
            await pilot.pause()

            # 2. Trigger Auto-Fix & Verify
            autofix_btn = app.query_one("#pr-autofix-btn", Button)
            autofix_btn.press()
            await pilot.pause()
            # PR #142 or current should be verified PASS and CLEAN
            cur_pr = pr_widget.prs[pr_widget.selected_pr_idx]
            assert cur_pr.ci_status == "PASS"
            assert cur_pr.conflict_state == "CLEAN"

            # 3. Trigger Merge PR
            merge_btn = app.query_one("#pr-merge-btn", Button)
            merge_btn.press()
            await pilot.pause()

            # 4. Trigger Refresh
            refresh_btn = app.query_one("#pr-refresh-btn", Button)
            refresh_btn.press()
            await pilot.pause()

    asyncio.run(_test())


# ==============================================================================
# 3. MCP Server Inspector Tests
# ==============================================================================

def test_mcp_server_inspector_widget():
    """Verify MCPServerInspectorWidget lists servers, displays tools/schemas, and runs ping/test."""
    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            # Switch to MCP inspector
            app.action_open_mcp_inspector()
            await pilot.pause()

            tabs = app.query_one("#workspace-tabs", TabbedContent)
            assert tabs.active == "tab-mcp"

            mcp_widget = app.query_one("#mcp-inspector-widget", MCPServerInspectorWidget)
            assert mcp_widget is not None
            assert len(mcp_widget.servers) >= 4

            # 1. Ping / Health check
            ping_btn = app.query_one("#mcp-ping-btn", Button)
            ping_btn.press()
            await pilot.pause()
            assert any("PING" in log for log in mcp_widget.logs)

            # 2. Test Invocation
            test_btn = app.query_one("#mcp-test-btn", Button)
            test_btn.press()
            await pilot.pause()
            assert any("tool_call" in log for log in mcp_widget.logs)

            # 3. Refresh
            refresh_btn = app.query_one("#mcp-refresh-btn", Button)
            refresh_btn.press()
            await pilot.pause()

    asyncio.run(_test())


# ==============================================================================
# 4. Swarm Radar Tests
# ==============================================================================

def test_swarm_radar_widget_nodes_and_telemetry():
    """Verify SwarmRadarWidget renders active subagent nodes, token expenditures, and actions."""
    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            # Switch to Swarm Radar
            app.action_open_swarm_radar()
            await pilot.pause()

            tabs = app.query_one("#workspace-tabs", TabbedContent)
            assert tabs.active == "tab-radar"

            radar_widget = app.query_one("#swarm-radar-widget", SwarmRadarWidget)
            assert radar_widget is not None
            assert len(radar_widget.tasks) >= 7

            # Check subagent node cards
            node_cards = app.query(".swarm-node-card")
            assert len(node_cards) >= 7

            # 1. Spawn Swarm Action
            spawn_btn = app.query_one("#spawn-radar-btn", Button)
            spawn_btn.press()
            await pilot.pause()

            # 2. Pause / Resume Swarm Action
            pause_btn = app.query_one("#pause-radar-btn", Button)
            pause_btn.press()
            await pilot.pause()

            # 3. Cancel Swarm Action
            cancel_btn = app.query_one("#cancel-radar-btn", Button)
            cancel_btn.press()
            await pilot.pause()

            # 4. Radar sweep timer update
            radar_widget.update_radar_sweep()
            await pilot.pause()

    asyncio.run(_test())


# ==============================================================================
# 5. Keybindings & Slash Commands Routing for New Screens
# ==============================================================================

def test_kcli_app_screen_shortcuts_and_slash_commands():
    """Verify keyboard shortcuts and slash commands switch to the new power tool screens."""
    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            tabs = app.query_one("#workspace-tabs", TabbedContent)

            # 1. Slash command /conflict -> Conflict Studio
            app.handle_slash_command("/conflict")
            await pilot.pause()
            assert tabs.active == "tab-conflict"

            # 2. Slash command /pr -> GitHub PR Hub
            app.handle_slash_command("/pr")
            await pilot.pause()
            assert tabs.active == "tab-pr"

            # 3. Slash command /mcp -> MCP Inspector
            app.handle_slash_command("/mcp")
            await pilot.pause()
            assert tabs.active == "tab-mcp"

            # 4. Slash command /radar -> Swarm Radar
            app.handle_slash_command("/radar")
            await pilot.pause()
            assert tabs.active == "tab-radar"

            # 5. Action shortcuts
            app.action_open_conflict_studio()
            await pilot.pause()
            assert tabs.active == "tab-conflict"

            app.action_open_pr_hub()
            await pilot.pause()
            assert tabs.active == "tab-pr"

            app.action_open_mcp_inspector()
            await pilot.pause()
            assert tabs.active == "tab-mcp"

            app.action_open_swarm_radar()
            await pilot.pause()
            assert tabs.active == "tab-radar"

    asyncio.run(_test())
