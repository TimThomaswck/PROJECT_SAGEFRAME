"""Undo/Redo command stack management for Sageframe.

Implements a command-based undo/redo system using a stack pattern.
Commands are executed immediately when pushed, with undo/redo capabilities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from PySide6.QtCore import QObject, Signal


class UndoCommand(ABC):
    """Base class for undoable commands.
    
    Subclasses implement undo/redo logic for specific actions.
    Commands are executed (redo) when pushed to the stack.
    """

    def __init__(self, description: str = ""):
        """Initialize command.
        
        Args:
            description: Human-readable description of the command (e.g., "Add task")
        """
        self._description = description

    @property
    def description(self) -> str:
        """Return the human-readable description of this command."""
        return self._description

    @abstractmethod
    def redo(self) -> None:
        """Execute or re-execute the command.
        
        This is called when the command is first pushed to the stack,
        and again when the user invokes Redo.
        """
        pass

    @abstractmethod
    def undo(self) -> None:
        """Reverse the command's effects.
        
        Restores the application state to before the command was executed.
        """
        pass

    def merge(self, other: "UndoCommand") -> bool:
        """Optionally merge this command with another.
        
        Used for combining related commands (e.g., consecutive text edits).
        Default implementation returns False (no merging).
        
        Args:
            other: Another command to potentially merge with this one.
            
        Returns:
            True if the commands were merged, False otherwise.
        """
        return False


class UndoManager(QObject):
    """Centralized undo/redo stack management.
    
    Manages a stack of commands, tracking undo/redo state and signaling
    changes to UI elements.
    
    Signals:
        can_undo_changed: Emitted when undo availability changes (bool new_state)
        can_redo_changed: Emitted when redo availability changes (bool new_state)
    """

    can_undo_changed = Signal(bool)
    can_redo_changed = Signal(bool)

    def __init__(self, parent: Optional[QObject] = None, max_depth: int = 50):
        """Initialize UndoManager.
        
        Args:
            parent: Parent QObject (optional)
            max_depth: Maximum number of commands to keep in history (default 50)
        """
        super().__init__(parent)
        self._undo_stack: List[UndoCommand] = []
        self._redo_stack: List[UndoCommand] = []
        self._max_depth = max_depth
        self._block_signals_flag = False

    def push(self, command: UndoCommand) -> None:
        """Execute a command and add it to the undo stack.
        
        The command's redo() method is called immediately.
        Any existing redo stack is cleared (standard undo/redo behavior).
        
        Args:
            command: The command to execute and track
        """
        # Execute the command
        command.redo()

        # Try to merge with the last command if possible
        if (
            self._undo_stack
            and self._undo_stack[-1].merge(command)
        ):
            # Command was merged, no need to add separately
            pass
        else:
            # Add to undo stack
            self._undo_stack.append(command)

            # Enforce history depth limit
            if len(self._undo_stack) > self._max_depth:
                self._undo_stack.pop(0)

        # Clear redo stack (user performed new action after undo)
        old_can_redo = bool(self._redo_stack)
        self._redo_stack.clear()

        if old_can_redo:
            self._emit_can_redo_changed()

        # Signal undo availability changed
        self._emit_can_undo_changed()

    def undo(self) -> None:
        """Undo the last command.
        
        If undo stack is empty, does nothing.
        """
        if not self._undo_stack:
            return

        # Move command from undo to redo stack
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)

        # Update signals
        self._emit_can_undo_changed()
        self._emit_can_redo_changed()

    def redo(self) -> None:
        """Redo the last undone command.
        
        If redo stack is empty, does nothing.
        """
        if not self._redo_stack:
            return

        # Move command from redo to undo stack
        command = self._redo_stack.pop()
        command.redo()
        self._undo_stack.append(command)

        # Update signals
        self._emit_can_undo_changed()
        self._emit_can_redo_changed()

    def can_undo(self) -> bool:
        """Return whether undo is currently available."""
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        """Return whether redo is currently available."""
        return bool(self._redo_stack)

    def undo_stack_size(self) -> int:
        """Return the current size of the undo stack."""
        return len(self._undo_stack)

    def redo_stack_size(self) -> int:
        """Return the current size of the redo stack."""
        return len(self._redo_stack)

    def clear(self) -> None:
        """Clear both undo and redo stacks."""
        old_can_undo = self.can_undo()
        old_can_redo = self.can_redo()

        self._undo_stack.clear()
        self._redo_stack.clear()

        if old_can_undo:
            self._emit_can_undo_changed()
        if old_can_redo:
            self._emit_can_redo_changed()

    def block_signals(self, block: bool) -> None:
        """Block or unblock signal emissions.
        
        Useful for batch operations that shouldn't trigger UI updates
        until the batch is complete.
        
        Args:
            block: True to block signals, False to unblock
        """
        self._block_signals_flag = block

    def _emit_can_undo_changed(self) -> None:
        """Emit can_undo_changed signal if signals are not blocked."""
        if not self._block_signals_flag:
            self.can_undo_changed.emit(self.can_undo())

    def _emit_can_redo_changed(self) -> None:
        """Emit can_redo_changed signal if signals are not blocked."""
        if not self._block_signals_flag:
            self.can_redo_changed.emit(self.can_redo())
