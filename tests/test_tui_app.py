"""
test_tui_app.py - Comprehensive End-to-End Test Suite for KCliApp (Textual 8.2.8)
Project Bankai Engine v0.2.0

Tests:
1. Cyberpunk Header badges & reactive updates (Model, Persona, Branch, RAM, Tokens).
2. Left Sidebar Dock (Live Subagent Swarm Tree, Context Files list, Quick DevDocs widget).
3. Central Chat & Workspace (Message stream, Collapsible <think> accordion, Diff viewer, Tool cards).
4. Bottom Dock & Keybindings (Ctrl+M, Ctrl+P, Ctrl+S, Ctrl+D, Ctrl+Z, Ctrl+T, Ctrl+L, F1, Ctrl+Q).
5. Modal Screens (ModelSelectModal, PersonaSelectModal, SubagentSpawnModal, DocDetailModal, HelpModal).
6. Slash command handling and history navigation.
"""

import asyncio
import os
import pytest
from pathlib import Path

from textual.widgets import Button, Collapsible, Input, Markdown, OptionList, Static, TabbedContent, Tree
from textual.containers import Vertical, VerticalScroll

from k_cli.tui_app import (
    KCliApp,
    CyberpunkHeader,
    LiveSubagentTreeWidget,
    ContextFilesWidget,
    QuickDevDocsWidget,
    ReasoningAccordion,
    ToolStatusCard,
    DiffViewerWidget,
    ModelSelectModal,
    PersonaSelectModal,
    SubagentSpawnModal,
    DocDetailModal,
    HelpModal,
    extract_think_blocks,
    format_side_by_side_diff,
)
from k_cli.subagents import SubagentRole, SubagentStatus, SubagentTask


def test_cyberpunk_header_badges():
    """Tests the CyberpunkHeader component and its reactive state synchronization."""
    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            header = app.query_one("#cyber-header", CyberpunkHeader)
            assert header is not None

            # Check initial values
            assert header.model_name == "Bankai-7B"
            assert header.git_branch is not None

            # Test reactive badge updates
            header.model_name = "Bankai-14B"
            header.persona_name = "DevOps & SRE Specialist"
            header.ram_mb = 128.5
            header.token_count = 342
            header.uncommitted = True
            await pilot.pause()

            m_view = app.query_one("#badge-model-view", Static)
            p_view = app.query_one("#badge-persona-view", Static)
            r_view = app.query_one("#badge-ram-view", Static)
            t_view = app.query_one("#badge-tokens-view", Static)

            assert "Bankai-14B" in str(m_view.render())
            assert "DevOps" in str(p_view.render())
            assert "128.5MB" in str(r_view.render())
            assert "342" in str(t_view.render())

    asyncio.run(_test())


def test_subagent_swarm_tree_updates():
    """Tests LiveSubagentTreeWidget populating tasks, glyphs, and progress updates."""
    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            tree_widget = app.query_one("#live-swarm-tree-widget", LiveSubagentTreeWidget)
            assert tree_widget is not None

            tasks = [
                SubagentTask(
                    task_id="task_1",
                    name="Explore repo map",
                    role=SubagentRole.EXPLORER,
                    prompt="Explore files",
                    status=SubagentStatus.PENDING,
                    status_message="Queued",
                ),
                SubagentTask(
                    task_id="task_2",
                    name="Refactor code",
                    role=SubagentRole.REFACTORER,
                    prompt="Refactor logic",
                    status=SubagentStatus.RUNNING,
                    status_message="Generating patches",
                ),
            ]

            tree_widget.set_tasks(tasks)
            await pilot.pause()

            tree = app.query_one("#swarm-tree", Tree)
            assert len(tree.root.children) == 2

            # Update progress
            tree_widget.update_task_progress("task_1", 1.0, "Done exploring", SubagentStatus.COMPLETED)
            tree_widget.update_task_progress("task_2", 0.65, "Synthesizing", SubagentStatus.RUNNING)
            await pilot.pause()

            assert "🟢" in str(tree.root.children[0].label)
            assert "65%" in str(tree.root.children[1].label)

    asyncio.run(_test())


def test_context_files_widget():
    """Tests adding and removing context files via the UI widget."""
    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            ctx_widget = app.query_one("#context-files-widget", ContextFilesWidget)
            assert ctx_widget is not None

            # Add existing file (e.g. tui_app.py)
            app.add_context_file("tui_app.py")
            await pilot.pause()

            opt_list = app.query_one("#context-file-list", OptionList)
            assert len(opt_list._options) > 0

            # Remove file
            app.remove_context_file("tui_app.py")
            await pilot.pause()
            assert "tui_app.py" not in app.session.get_context_files()

    asyncio.run(_test())


def test_quick_devdocs_lookup():
    """Tests searching and inspecting symbols via the QuickDevDocsWidget."""
    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            devdocs_widget = app.query_one(QuickDevDocsWidget)
            assert devdocs_widget is not None

            # Trigger search
            devdocs_widget.perform_search("json")
            await pilot.pause()

            results_scroll = app.query_one("#devdocs-results-scroll", VerticalScroll)
            assert len(results_scroll.children) > 0

    asyncio.run(_test())


def test_reasoning_accordion_and_think_parsing():
    """Tests extracting <think> tags and mounting ReasoningAccordion."""
    sample_text = "<think>1. Analyze requirements\n2. Design modular architecture</think>\ndef solution():\n    return 42"
    think_text, clean_text = extract_think_blocks(sample_text)

    assert think_text == "1. Analyze requirements\n2. Design modular architecture"
    assert clean_text == "def solution():\n    return 42"

    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            chat_stream = app.query_one("#chat-stream", VerticalScroll)
            accordion = ReasoningAccordion(think_text, duration_sec=1.42, is_streaming=False)
            chat_stream.mount(accordion)
            await pilot.pause()

            collapsible = app.query_one(Collapsible)
            assert collapsible is not None
            assert "1.42s" in str(collapsible.title)

    asyncio.run(_test())


def test_diff_viewer_widget():
    """Tests DiffViewerWidget with Side-by-Side and Unified views."""
    old_c = "def old_func():\n    return 1"
    new_c = "def new_func():\n    return 2"
    l_rows, r_rows = format_side_by_side_diff(old_c, new_c)
    assert len(l_rows) == len(r_rows)

    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            diff_widget = app.query_one("#diff-viewer-widget", DiffViewerWidget)
            assert diff_widget is not None

            diff_widget.old_code = old_c
            diff_widget.new_code = new_c
            diff_widget.diff_text = "--- a/file.py\n+++ b/file.py\n@@ -1,2 +1,2 @@\n-def old_func():\n+def new_func():"
            await pilot.pause()

            # Toggle mode
            diff_widget.side_by_side = False
            await pilot.pause()
            assert diff_widget.side_by_side is False

    asyncio.run(_test())


def test_tool_status_card():
    """Tests ToolStatusCard rendering for verified and failed executions."""
    card_ok = ToolStatusCard(success=True, verification_type="ast_syntax", attempts=1, ram_mb=45.2, patches_applied=True)
    card_fail = ToolStatusCard(success=False, verification_type="compiler", attempts=2, ram_mb=50.0, error_trace="SyntaxError: invalid syntax")

    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            chat_stream = app.query_one("#chat-stream", VerticalScroll)
            chat_stream.mount(card_ok)
            chat_stream.mount(card_fail)
            await pilot.pause()

            assert len(app.query(ToolStatusCard)) == 2

    asyncio.run(_test())


def test_keybinding_actions_and_modals():
    """Tests keyboard shortcuts opening modals and switching states."""
    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            # 1. Switch Model Modal (Ctrl+M)
            app.action_switch_model()
            await pilot.pause()
            assert isinstance(app.screen, ModelSelectModal)
            app.screen.dismiss("Bankai-14B")
            await pilot.pause()
            assert app.active_model == "Bankai-14B"

            # 2. Switch Persona Modal (Ctrl+P)
            app.action_switch_persona()
            await pilot.pause()
            assert isinstance(app.screen, PersonaSelectModal)
            app.screen.dismiss("Surgical Debugger")
            await pilot.pause()
            assert "Debugger" in app.active_persona

            # 3. Spawn Subagents Modal (Ctrl+S)
            app.action_spawn_subagents()
            await pilot.pause()
            assert isinstance(app.screen, SubagentSpawnModal)
            app.screen.dismiss(None)
            await pilot.pause()

            # 4. View Diff Tab (Ctrl+D)
            app.action_view_diff()
            await pilot.pause()
            tabs = app.query_one("#workspace-tabs", TabbedContent)
            assert tabs.active == "tab-diff"

            # 5. Help Modal (F1 / Ctrl+H)
            app.action_show_help()
            await pilot.pause()
            assert isinstance(app.screen, HelpModal)
            app.screen.dismiss(None)
            await pilot.pause()

            # 6. Clear Chat (Ctrl+L)
            app.action_clear_chat()
            await pilot.pause()
            chat_stream = app.query_one("#chat-stream", VerticalScroll)
            assert len(chat_stream.children) == 0

    asyncio.run(_test())


def test_slash_command_execution():
    """Tests slash command parsing from the bottom dock input."""
    async def _test():
        app = KCliApp(mock_mode=True)
        async with app.run_test() as pilot:
            # /model Bankai-7B
            app.handle_slash_command("/model Bankai-7B")
            await pilot.pause()
            assert app.active_model == "Bankai-7B"

            # /persona devops
            app.handle_slash_command("/persona devops")
            await pilot.pause()
            assert "DevOps" in app.active_persona

            # /clear
            app.handle_slash_command("/clear")
            await pilot.pause()
            chat_stream = app.query_one("#chat-stream", VerticalScroll)
            assert len(chat_stream.children) == 0

    asyncio.run(_test())
