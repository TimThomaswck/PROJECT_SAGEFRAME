"""Concrete UndoCommand implementations for specific application actions.

These command classes handle undoing/redoing various application state changes.
New commands can be added as application features expand.
"""

from typing import Any, Callable, Optional

from app.core.undo_manager import UndoCommand


class PropertyChangeCommand(UndoCommand):
    """Generic command for changing an object property.
    
    Useful for simple state changes where the object being modified
    is directly accessible and has a settable attribute.
    """

    def __init__(
        self,
        obj: Any,
        property_name: str,
        new_value: Any,
        description: str = "",
        old_value: Optional[Any] = None,
    ):
        """Initialize PropertyChangeCommand.
        
        Args:
            obj: The object whose property will change
            property_name: Name of the property/attribute
            new_value: The new value to set
            description: Human-readable description (auto-generated if empty)
            old_value: The previous value (auto-captured if None)
        """
        self._obj = obj
        self._property_name = property_name
        self._new_value = new_value
        self._old_value = (
            old_value
            if old_value is not None
            else getattr(obj, property_name, None)
        )

        if not description:
            description = f"Change {property_name}"

        super().__init__(description)

    def redo(self) -> None:
        """Set property to new value."""
        setattr(self._obj, self._property_name, self._new_value)

    def undo(self) -> None:
        """Restore property to old value."""
        setattr(self._obj, self._property_name, self._old_value)


class CallbackCommand(UndoCommand):
    """Command that executes arbitrary callbacks for undo/redo.
    
    Useful for complex operations where custom logic is needed
    for both redo and undo operations.
    """

    def __init__(
        self,
        redo_callback: Callable[[], None],
        undo_callback: Callable[[], None],
        description: str = "",
    ):
        """Initialize CallbackCommand.
        
        Args:
            redo_callback: Function to call for redo operation
            undo_callback: Function to call for undo operation
            description: Human-readable description
        """
        self._redo_callback = redo_callback
        self._undo_callback = undo_callback
        super().__init__(description or "Custom action")

    def redo(self) -> None:
        """Execute the redo callback."""
        self._redo_callback()

    def undo(self) -> None:
        """Execute the undo callback."""
        self._undo_callback()


class TextEditCommand(UndoCommand):
    """Command for text editing operations.
    
    Handles insertion or deletion of text in a string-based property
    or object.
    """

    def __init__(
        self,
        obj: Any,
        property_name: str,
        position: int,
        inserted_text: str = "",
        deleted_text: str = "",
        description: str = "",
    ):
        """Initialize TextEditCommand.
        
        Args:
            obj: Object whose text property will change
            property_name: Name of the text property
            position: Position in text where change occurs
            inserted_text: Text that was inserted
            deleted_text: Text that was deleted
            description: Custom description
        """
        self._obj = obj
        self._property_name = property_name
        self._position = position
        self._inserted_text = inserted_text
        self._deleted_text = deleted_text
        self._original_text = getattr(obj, property_name, "")

        if not description:
            if inserted_text and not deleted_text:
                description = f"Insert '{inserted_text[:20]}'"
            elif deleted_text and not inserted_text:
                description = f"Delete '{deleted_text[:20]}'"
            else:
                description = "Edit text"

        super().__init__(description)

    def redo(self) -> None:
        """Apply the text change (insert or replace)."""
        text = getattr(self._obj, self._property_name, "")
        # Remove deleted text and insert new text
        new_text = (
            text[: self._position]
            + self._inserted_text
            + text[self._position + len(self._deleted_text) :]
        )
        setattr(self._obj, self._property_name, new_text)

    def undo(self) -> None:
        """Restore text to original state."""
        setattr(self._obj, self._property_name, self._original_text)

    def merge(self, other: UndoCommand) -> bool:
        """Merge consecutive text edits into one command.
        
        Allows merging nearby text insertions/deletions to reduce
        undo stack clutter (e.g., typing a word becomes one undo).
        """
        if not isinstance(other, TextEditCommand):
            return False

        if (
            other._obj is not self._obj
            or other._property_name != self._property_name
        ):
            return False

        # Merge if the new edit is adjacent or overlapping
        # This handles consecutive insertions
        if (
            other._deleted_text == ""
            and self._deleted_text == ""
            and other._position == self._position + len(self._inserted_text)
        ):
            # Adjacent insertion - merge them
            self._inserted_text += other._inserted_text
            return True

        return False


class MultiCommandGroup(UndoCommand):
    """Command that groups multiple commands together.
    
    Allows treating multiple operations as a single undo/redo action.
    Useful for compound operations that should be undone together.
    """

    def __init__(self, description: str = ""):
        """Initialize MultiCommandGroup.
        
        Args:
            description: Description of the group operation
        """
        super().__init__(description or "Multi-step action")
        self._commands: list[UndoCommand] = []

    def add_command(self, command: UndoCommand) -> None:
        """Add a command to the group.
        
        Args:
            command: The command to add
        """
        self._commands.append(command)

    def redo(self) -> None:
        """Execute all commands in order."""
        for cmd in self._commands:
            cmd.redo()

    def undo(self) -> None:
        """Undo all commands in reverse order."""
        for cmd in reversed(self._commands):
            cmd.undo()

class CriticalOperationCommand(UndoCommand):
    """Command for critical operations that require confirmation before undoing.
    
    Handles operations that may result in data loss or other critical consequences.
    Addresses AC4: "system provides a warning or prevents the undo action for critical operations"
    """

    def __init__(
        self,
        redo_callback: Callable[[], None],
        undo_callback: Callable[[], None],
        description: str = "",
        requires_confirmation: bool = True,
        confirmation_message: str = "",
    ):
        """Initialize CriticalOperationCommand.
        
        Args:
            redo_callback: Function to call for redo operation
            undo_callback: Function to call for undo operation  
            description: Human-readable description
            requires_confirmation: Whether undo requires user confirmation
            confirmation_message: Message to show when requesting confirmation
        """
        self._redo_callback = redo_callback
        self._undo_callback = undo_callback
        self._requires_confirmation = requires_confirmation
        self._confirmation_message = confirmation_message or f"Are you sure you want to undo: {description}?"
        self._confirmation_callback: Optional[Callable[[bool], None]] = None
        
        super().__init__(description or "Critical operation")

    def redo(self) -> None:
        """Execute the redo callback."""
        self._redo_callback()

    def undo(self) -> None:
        """Execute the undo callback with optional confirmation."""
        if self._requires_confirmation:
            # Callback will be set by UndoManager or UI layer
            if self._confirmation_callback:
                self._confirmation_callback(self._perform_undo)
            else:
                # Default behavior: perform undo without asking
                self._perform_undo()
        else:
            self._perform_undo()

    def _perform_undo(self) -> None:
        """Actually perform the undo operation."""
        self._undo_callback()

    def set_confirmation_callback(self, callback: Callable[[Callable[[], None]], None]) -> None:
        """Set the callback for requesting user confirmation.
        
        Args:
            callback: Function that takes the undo function and handles confirmation
        """
        self._confirmation_callback = callback