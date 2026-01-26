"""Tests for concrete UndoCommand implementations."""

import pytest
from unittest.mock import Mock

from app.core.undo_commands import (
    PropertyChangeCommand,
    CallbackCommand,
    TextEditCommand,
    MultiCommandGroup,
    CriticalOperationCommand,
)


class MockObject:
    """Simple object for testing property changes."""

    def __init__(self):
        self.text = "initial"
        self.count = 0
        self.enabled = True


class TestPropertyChangeCommand:
    """Test PropertyChangeCommand functionality."""

    def test_basic_property_change(self):
        """Test changing a simple property."""
        obj = MockObject()
        assert obj.count == 0

        cmd = PropertyChangeCommand(obj, "count", 42, "Set count to 42")
        cmd.redo()

        assert obj.count == 42

        cmd.undo()
        assert obj.count == 0

    def test_property_change_with_auto_description(self):
        """Test that description is auto-generated if not provided."""
        obj = MockObject()
        cmd = PropertyChangeCommand(obj, "text", "modified")

        assert "text" in cmd.description.lower()

    def test_property_change_string(self):
        """Test changing string properties."""
        obj = MockObject()
        obj.text = "hello"

        cmd = PropertyChangeCommand(obj, "text", "world")
        cmd.redo()

        assert obj.text == "world"

        cmd.undo()
        assert obj.text == "hello"

    def test_property_change_boolean(self):
        """Test toggling boolean properties."""
        obj = MockObject()
        assert obj.enabled is True

        cmd = PropertyChangeCommand(obj, "enabled", False)
        cmd.redo()

        assert obj.enabled is False

        cmd.undo()
        assert obj.enabled is True


class TestCallbackCommand:
    """Test CallbackCommand functionality."""

    def test_callback_execution(self):
        """Test that callbacks are executed."""
        state = {"redo_called": False, "undo_called": False}

        def on_redo():
            state["redo_called"] = True

        def on_undo():
            state["undo_called"] = True

        cmd = CallbackCommand(on_redo, on_undo, "Custom operation")

        cmd.redo()
        assert state["redo_called"]

        cmd.undo()
        assert state["undo_called"]

    def test_callback_with_state_change(self):
        """Test callbacks that modify application state."""
        items = []

        def add_item():
            items.append("new")

        def remove_item():
            items.pop()

        cmd = CallbackCommand(add_item, remove_item, "Add item")

        cmd.redo()
        assert len(items) == 1

        cmd.undo()
        assert len(items) == 0


class TestTextEditCommand:
    """Test TextEditCommand functionality."""

    def test_insert_text(self):
        """Test inserting text."""
        obj = MockObject()
        obj.text = "helo"

        cmd = TextEditCommand(obj, "text", 2, inserted_text="l", description="Insert 'l'")
        cmd.redo()

        assert obj.text == "hello"

        cmd.undo()
        assert obj.text == "helo"

    def test_delete_text(self):
        """Test deleting text."""
        obj = MockObject()
        obj.text = "hello"

        cmd = TextEditCommand(
            obj, "text", 2, deleted_text="ll", description="Delete 'll'"
        )
        cmd.redo()

        assert obj.text == "heo"

        cmd.undo()
        assert obj.text == "hello"

    def test_replace_text(self):
        """Test replacing text."""
        obj = MockObject()
        obj.text = "hello"

        cmd = TextEditCommand(
            obj,
            "text",
            1,
            inserted_text="a",
            deleted_text="e",
            description="Replace 'e' with 'a'",
        )
        cmd.redo()

        assert obj.text == "hallo"

        cmd.undo()
        assert obj.text == "hello"

    def test_text_edit_auto_description(self):
        """Test auto-generated descriptions for text edits."""
        obj = MockObject()

        insert_cmd = TextEditCommand(obj, "text", 0, inserted_text="hi")
        assert "insert" in insert_cmd.description.lower()

        delete_cmd = TextEditCommand(obj, "text", 0, deleted_text="x")
        assert "delete" in delete_cmd.description.lower()

    def test_text_edit_merge(self):
        """Test merging consecutive text insertions."""
        obj = MockObject()
        obj.text = ""

        cmd1 = TextEditCommand(obj, "text", 0, inserted_text="h")
        cmd1.redo()
        assert obj.text == "h"

        cmd2 = TextEditCommand(obj, "text", 1, inserted_text="i")

        # Should be mergeable since cmd2 is adjacent to cmd1
        assert cmd1.merge(cmd2)

        cmd2.redo()
        assert obj.text == "hi"

        cmd1.undo()
        assert obj.text == ""

    def test_text_edit_merge_with_different_objects(self):
        """Test that text edits for different objects don't merge."""
        obj1 = MockObject()
        obj2 = MockObject()

        cmd1 = TextEditCommand(obj1, "text", 0, inserted_text="a")
        cmd2 = TextEditCommand(obj2, "text", 0, inserted_text="b")

        assert not cmd1.merge(cmd2)

    def test_text_edit_merge_with_deletions(self):
        """Test that text edits with deletions don't merge."""
        obj = MockObject()

        cmd1 = TextEditCommand(obj, "text", 0, inserted_text="a")
        cmd2 = TextEditCommand(obj, "text", 1, inserted_text="b", deleted_text="x")

        assert not cmd1.merge(cmd2)


class TestMultiCommandGroup:
    """Test MultiCommandGroup functionality."""

    def test_group_execution(self):
        """Test executing grouped commands."""
        obj = MockObject()
        obj.count = 0
        obj.text = "initial"

        group = MultiCommandGroup("Multiple changes")

        cmd1 = PropertyChangeCommand(obj, "count", 10)
        cmd2 = PropertyChangeCommand(obj, "text", "modified")

        group.add_command(cmd1)
        group.add_command(cmd2)

        group.redo()

        assert obj.count == 10
        assert obj.text == "modified"

        group.undo()

        assert obj.count == 0
        assert obj.text == "initial"

    def test_group_with_many_commands(self):
        """Test grouping many commands."""
        obj = MockObject()
        obj.count = 0

        group = MultiCommandGroup()

        # Manually add commands with correct old values
        for i in range(5):
            cmd = PropertyChangeCommand(obj, "count", i + 1, old_value=i)
            group.add_command(cmd)

        group.redo()
        assert obj.count == 5

        group.undo()
        assert obj.count == 0

    def test_empty_group(self):
        """Test that empty groups don't cause errors."""
        group = MultiCommandGroup()

        group.redo()
        group.undo()

        assert group.undo_stack_size() == 0 if hasattr(group, "undo_stack_size") else True

class TestCriticalOperationCommand:
    """Test CriticalOperationCommand functionality for AC4."""

    def test_critical_operation_with_confirmation(self):
        """Test critical operation requiring confirmation."""
        state = {"undo_requested": False, "undo_confirmed": False}

        def on_redo():
            state["redo_called"] = True

        def on_undo():
            state["undo_called"] = True

        def confirmation_callback(undo_func):
            state["undo_requested"] = True
            # Simulate user confirmation
            state["undo_confirmed"] = True
            undo_func()

        cmd = CriticalOperationCommand(
            on_redo,
            on_undo,
            description="Delete all data",
            requires_confirmation=True,
            confirmation_message="This will delete all data. Continue?",
        )

        # Set confirmation callback
        cmd.set_confirmation_callback(confirmation_callback)

        # Redo the operation
        cmd.redo()
        assert state.get("redo_called", False)

        # Undo should request confirmation
        cmd.undo()
        assert state["undo_requested"]
        assert state["undo_confirmed"]
        assert state.get("undo_called", False)

    def test_critical_operation_without_confirmation(self):
        """Test critical operation that doesn't require confirmation."""
        state = {"undo_called": False}

        def on_redo():
            pass

        def on_undo():
            state["undo_called"] = True

        cmd = CriticalOperationCommand(
            on_redo,
            on_undo,
            description="Minor change",
            requires_confirmation=False,
        )

        cmd.undo()
        assert state["undo_called"]

    def test_critical_operation_confirmation_message(self):
        """Test that confirmation message is accessible."""
        def on_redo():
            pass

        def on_undo():
            pass

        custom_message = "This action cannot be reversed. Continue?"
        cmd = CriticalOperationCommand(
            on_redo,
            on_undo,
            description="Permanent action",
            confirmation_message=custom_message,
        )

        assert cmd._confirmation_message == custom_message

    def test_critical_operation_default_confirmation_message(self):
        """Test default confirmation message generation."""
        def on_redo():
            pass

        def on_undo():
            pass

        cmd = CriticalOperationCommand(
            on_redo,
            on_undo,
            description="Delete item",
        )

        assert "Delete item" in cmd._confirmation_message
        assert "undo" in cmd._confirmation_message.lower()