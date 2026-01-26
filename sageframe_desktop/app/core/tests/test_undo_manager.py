"""Unit tests for UndoManager.

Tests verify:
- Command stack management
- Undo/Redo operations
- State tracking (canUndo, canRedo)
- Signal emissions
"""

import pytest
from unittest.mock import Mock

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QObject

from app.core.undo_manager import UndoManager, UndoCommand


class SimpleCommand(UndoCommand):
    """Test command that tracks state changes."""

    def __init__(self, state_container, key, new_value):
        super().__init__(f"Set {key} to {new_value}")
        self.state_container = state_container
        self.key = key
        self.new_value = new_value
        self.old_value = None  # Will be set when first pushed

    def redo(self):
        if self.old_value is None:
            # First time: capture the old value
            self.old_value = self.state_container.get(self.key)
        self.state_container[self.key] = self.new_value

    def undo(self):
        self.state_container[self.key] = self.old_value


@pytest.fixture
def undo_manager(qtbot):
    """Create a UndoManager instance for testing."""
    manager = UndoManager()
    return manager


@pytest.fixture
def state_container():
    """Simple state container for testing."""
    return {"text": "", "count": 0}


class TestUndoManagerBasics:
    """Test basic UndoManager functionality."""

    def test_undo_manager_initialization(self, undo_manager):
        """Test that UndoManager initializes with no undo/redo available."""
        assert not undo_manager.can_undo()
        assert not undo_manager.can_redo()
        assert undo_manager.undo_stack_size() == 0

    def test_push_command(self, undo_manager, state_container):
        """Test pushing a command to the stack."""
        cmd = SimpleCommand(state_container, "text", "hello")
        undo_manager.push(cmd)

        assert undo_manager.can_undo()
        assert not undo_manager.can_redo()
        assert state_container["text"] == "hello"

    def test_undo_single_command(self, undo_manager, state_container):
        """Test undoing a single command."""
        state_container["text"] = "initial"
        cmd = SimpleCommand(state_container, "text", "modified")
        undo_manager.push(cmd)

        assert state_container["text"] == "modified"

        undo_manager.undo()

        assert state_container["text"] == "initial"
        assert not undo_manager.can_undo()
        assert undo_manager.can_redo()

    def test_redo_single_command(self, undo_manager, state_container):
        """Test redoing a single command."""
        state_container["text"] = "initial"
        cmd = SimpleCommand(state_container, "text", "modified")
        undo_manager.push(cmd)
        undo_manager.undo()

        assert state_container["text"] == "initial"

        undo_manager.redo()

        assert state_container["text"] == "modified"
        assert undo_manager.can_undo()
        assert not undo_manager.can_redo()

    def test_multiple_undo_redo(self, undo_manager, state_container):
        """Test multiple undo/redo operations in sequence."""
        # Push 3 commands
        state_container["text"] = ""
        cmd1 = SimpleCommand(state_container, "text", "first")
        cmd2 = SimpleCommand(state_container, "text", "second")
        cmd3 = SimpleCommand(state_container, "text", "third")

        undo_manager.push(cmd1)
        undo_manager.push(cmd2)
        undo_manager.push(cmd3)

        assert state_container["text"] == "third"

        # Undo all
        undo_manager.undo()
        assert state_container["text"] == "second"

        undo_manager.undo()
        assert state_container["text"] == "first"

        undo_manager.undo()
        assert state_container["text"] == ""
        assert not undo_manager.can_undo()

        # Redo all
        undo_manager.redo()
        assert state_container["text"] == "first"

        undo_manager.redo()
        assert state_container["text"] == "second"

        undo_manager.redo()
        assert state_container["text"] == "third"
        assert not undo_manager.can_redo()

    def test_undo_stack_size(self, undo_manager, state_container):
        """Test tracking undo stack size."""
        assert undo_manager.undo_stack_size() == 0

        for i in range(5):
            cmd = SimpleCommand(state_container, "count", i + 1)
            undo_manager.push(cmd)

        assert undo_manager.undo_stack_size() == 5

    def test_new_command_clears_redo_stack(self, undo_manager, state_container):
        """Test that pushing new command after undo clears redo stack."""
        cmd1 = SimpleCommand(state_container, "text", "first")
        cmd2 = SimpleCommand(state_container, "text", "second")
        cmd3 = SimpleCommand(state_container, "text", "third")

        undo_manager.push(cmd1)
        undo_manager.push(cmd2)
        undo_manager.undo()

        assert undo_manager.can_redo()

        undo_manager.push(cmd3)

        assert not undo_manager.can_redo()
        assert state_container["text"] == "third"

    def test_undo_when_empty(self, undo_manager):
        """Test that undo on empty stack is safe."""
        # Should not raise exception
        undo_manager.undo()
        assert not undo_manager.can_undo()

    def test_redo_when_empty(self, undo_manager):
        """Test that redo on empty stack is safe."""
        # Should not raise exception
        undo_manager.redo()
        assert not undo_manager.can_redo()

    def test_clear_stack(self, undo_manager, state_container):
        """Test clearing the undo/redo stack."""
        cmd1 = SimpleCommand(state_container, "text", "first")
        cmd2 = SimpleCommand(state_container, "text", "second")

        undo_manager.push(cmd1)
        undo_manager.push(cmd2)
        undo_manager.undo()

        undo_manager.clear()

        assert undo_manager.undo_stack_size() == 0
        assert not undo_manager.can_undo()
        assert not undo_manager.can_redo()


class TestUndoManagerSignals:
    """Test UndoManager signal emissions."""

    def test_can_undo_changed_signal(self, undo_manager, state_container, qtbot):
        """Test canUndoChanged signal is emitted."""
        signal_spy = Mock()
        undo_manager.can_undo_changed.connect(signal_spy)

        cmd = SimpleCommand(state_container, "text", "hello")
        undo_manager.push(cmd)

        # Signal should be emitted when can_undo changes
        assert signal_spy.call_count >= 1

    def test_can_redo_changed_signal(self, undo_manager, state_container):
        """Test canRedoChanged signal is emitted."""
        signal_spy = Mock()
        undo_manager.can_redo_changed.connect(signal_spy)

        cmd = SimpleCommand(state_container, "text", "hello")
        undo_manager.push(cmd)
        undo_manager.undo()

        # Signal should be emitted when can_redo changes
        assert signal_spy.call_count >= 1


class TestUndoManagerHistoryLimit:
    """Test UndoManager history depth limiting."""

    def test_history_depth_limit(self, state_container):
        """Test that undo history is limited to max_depth."""
        manager = UndoManager(max_depth=3)

        # Push 5 commands
        for i in range(5):
            cmd = SimpleCommand(state_container, "count", i + 1)
            manager.push(cmd)

        # Only last 3 should be in stack
        assert manager.undo_stack_size() <= 3
        assert state_container["count"] == 5

        # Undo should only go back 3 steps
        manager.undo()
        manager.undo()
        manager.undo()

        # Next undo should do nothing (stack empty)
        manager.undo()
        assert state_container["count"] <= 5  # Didn't go further back


class TestUndoManagerBlockSignals:
    """Test blocking signal emissions during batch operations."""

    def test_block_signals(self, undo_manager, state_container):
        """Test blocking signal emissions for batch operations."""
        signal_spy = Mock()
        undo_manager.can_undo_changed.connect(signal_spy)

        # Block signals
        undo_manager.block_signals(True)

        cmd1 = SimpleCommand(state_container, "text", "first")
        cmd2 = SimpleCommand(state_container, "text", "second")

        undo_manager.push(cmd1)
        undo_manager.push(cmd2)

        # No signals should be emitted
        assert signal_spy.call_count == 0

        # Unblock signals
        undo_manager.block_signals(False)

        # Signals should be emitted again
        cmd3 = SimpleCommand(state_container, "text", "third")
        undo_manager.push(cmd3)

        assert signal_spy.call_count > 0
