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


# ============================================================================
# Project Management Commands (Story 2.1)
# ============================================================================

class CreateProjectCommand(UndoCommand):
    """Command for creating a new project.
    
    Handles undo by deleting the created project, redo by recreating it.
    """

    def __init__(
        self,
        service: Any,  # ProjectService instance
        name: str,
        description: Optional[str] = None,
        created_project_id: Optional[int] = None,
    ):
        """Initialize CreateProjectCommand.
        
        Args:
            service: ProjectService instance for CRUD operations
            name: Project name
            description: Optional project description
            created_project_id: ID of created project (set after initial creation)
        """
        self._service = service
        self._name = name
        self._project_description = description  # Renamed to avoid conflict with parent _description
        self._project_id = created_project_id
        super().__init__(f"Create project '{name}'")

    def redo(self) -> None:
        """Create or recreate the project with ID preservation.
        
        On initial creation, the project gets a new ID from the database.
        On redo after undo, the original ID is preserved to maintain data integrity
        and prevent stale references to the project.
        """
        if self._project_id is None:
            # Initial creation - let database assign ID
            project = self._service.create_project(
                name=self._name,
                description=self._project_description
            )
            self._project_id = project.id
        else:
            # Recreate with same data (after undo) - ID is preserved
            # This ensures external references to this project remain valid
            project = self._service.create_project(
                name=self._name,
                description=self._project_description,
                id=self._project_id  # Preserve original ID on redo
            )
            # Verify ID consistency for data integrity
            assert project.id == self._project_id, f"Project ID mismatch on redo: expected {self._project_id}, got {project.id}"

    def undo(self) -> None:
        """Delete the created project."""
        if self._project_id is not None:
            self._service.delete_project(self._project_id)

    def get_project_id(self) -> Optional[int]:
        """Get the ID of the created project.
        
        Returns:
            Project ID if created, None otherwise
        """
        return self._project_id


class EditProjectCommand(UndoCommand):
    """Command for editing an existing project.
    
    Captures before/after state and can restore previous values.
    """

    def __init__(
        self,
        service: Any,  # ProjectService instance
        project_id: int,
        new_name: Optional[str] = None,
        new_description: Optional[str] = None,
    ):
        """Initialize EditProjectCommand.
        
        Args:
            service: ProjectService instance for CRUD operations
            project_id: ID of project to edit
            new_name: New project name (if changing)
            new_description: New project description (if changing)
        """
        self._service = service
        self._project_id = project_id
        
        # Capture current state before change
        current_project = self._service.get_project(project_id)
        if current_project is None:
            raise ValueError(f"Project {project_id} not found")
        
        self._old_name = current_project.name
        self._old_description = current_project.description
        
        # Store new values
        self._new_name = new_name if new_name is not None else self._old_name
        self._new_description = new_description if new_description is not None else self._old_description
        
        super().__init__(f"Edit project '{self._old_name}'")

    def redo(self) -> None:
        """Apply the edit (set new values)."""
        self._service.update_project(
            project_id=self._project_id,
            name=self._new_name,
            description=self._new_description
        )

    def undo(self) -> None:
        """Restore project to previous state."""
        self._service.update_project(
            project_id=self._project_id,
            name=self._old_name,
            description=self._old_description
        )


class DeleteProjectCommand(UndoCommand):
    """Command for deleting a project.
    
    Captures project data before deletion to enable restoration.
    """

    def __init__(
        self,
        service: Any,  # ProjectService instance
        project_id: int,
    ):
        """Initialize DeleteProjectCommand.
        
        Args:
            service: ProjectService instance for CRUD operations
            project_id: ID of project to delete
        """
        self._service = service
        self._project_id = project_id
        
        # Capture project data before deletion
        project = self._service.get_project(project_id)
        if project is None:
            raise ValueError(f"Project {project_id} not found")
        
        self._name = project.name
        self._project_description = project.description  # Renamed to avoid conflict
        self._user_id = project.user_id
        
        super().__init__(f"Delete project '{self._name}'")

    def redo(self) -> None:
        """Delete the project."""
        self._service.delete_project(self._project_id)

    def undo(self) -> None:
        """Restore the deleted project with ID preservation.
        
        When undoing a delete, the project is recreated with its original ID.
        This ensures that external references to this project (from other commands
        or UI state) remain valid, preventing data integrity issues.
        """
        # Recreate project with same data, preserving the original ID
        project = self._service.create_project(
            name=self._name,
            description=self._project_description,
            user_id=self._user_id,
            id=self._project_id  # Restore with original ID to preserve data integrity
        )
        # Verify ID consistency
        assert project.id == self._project_id, f"Project ID mismatch on undo: expected {self._project_id}, got {project.id}"


# ============================================================================
# Task Management Commands (Story 2.2)
# ============================================================================

class CreateTaskCommand(UndoCommand):
    """Command for creating a new task.
    
    Handles undo by deleting the created task, redo by recreating it.
    """

    def __init__(
        self,
        service: Any,  # TaskService instance
        title: str,
        description: Optional[str] = None,
        due_date: Optional[Any] = None,  # datetime
        status: str = 'todo',
        priority: Optional[Any] = None,
        complexity: Optional[Any] = None,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        created_task_id: Optional[int] = None,
    ):
        """Initialize CreateTaskCommand.
        
        Args:
            service: TaskService instance for CRUD operations
            title: Task title
            description: Optional task description
            due_date: Optional due date
            status: Task status (default: 'todo')
            project_id: Optional project association
            user_id: Optional user ID
            created_task_id: ID of created task (set after initial creation)
        """
        self._service = service
        self._title = title
        self._task_description = description  # Renamed to avoid conflict with parent _description
        self._due_date = due_date
        self._status = status
        self._priority = priority
        self._complexity = complexity
        self._project_id = project_id
        self._user_id = user_id
        self._task_id = created_task_id
        super().__init__(f"Create task '{title}'")

    def redo(self) -> None:
        """Create or recreate the task."""
        task = self._service.create_task(
            title=self._title,
            description=self._task_description,
            due_date=self._due_date,
            status=self._status,
            priority=self._priority,
            complexity=self._complexity,
            project_id=self._project_id,
            user_id=self._user_id
        )
        self._task_id = task.id

    def undo(self) -> None:
        """Delete the created task."""
        if self._task_id is not None:
            self._service.delete_task(self._task_id)

    def get_task_id(self) -> Optional[int]:
        """Get the ID of the created task.
        
        Returns:
            Task ID if created, None otherwise
        """
        return self._task_id


class EditTaskCommand(UndoCommand):
    """Command for editing an existing task.
    
    Captures before/after state and can restore previous values.
    Supports editing all task properties including priority and complexity.
    """

    def __init__(
        self,
        service: Any,  # TaskService instance
        task_id: int,
        new_title: Optional[str] = None,
        new_description: Optional[str] = None,
        new_due_date: Optional[Any] = None,  # datetime
        new_status: Optional[str] = None,
        new_priority: Optional[Any] = None,  # TaskPriority enum or string
        new_complexity: Optional[Any] = None,  # TaskComplexity enum or string
        new_project_id: Optional[int] = None,
    ):
        """Initialize EditTaskCommand.
        
        Args:
            service: TaskService instance for CRUD operations
            task_id: ID of task to edit
            new_title: New task title (if changing)
            new_description: New task description (if changing)
            new_due_date: New due date (if changing)
            new_status: New status (if changing)
            new_priority: New priority level (if changing)
            new_complexity: New complexity level (if changing)
            new_project_id: New project association (if changing)
        """
        self._service = service
        self._task_id = task_id
        
        # Capture current state before change
        current_task = self._service.get_task(task_id)
        if current_task is None:
            raise ValueError(f"Task {task_id} not found")
        
        self._old_title = current_task.title
        self._old_description = current_task.description
        self._old_due_date = current_task.due_date
        self._old_status = current_task.status
        self._old_priority = current_task.priority
        self._old_complexity = current_task.complexity
        self._old_project_id = current_task.project_id
        
        # Store new values (use old if not changing)
        self._new_title = new_title if new_title is not None else self._old_title
        self._new_description = new_description if new_description is not None else self._old_description
        self._new_due_date = new_due_date if new_due_date is not None else self._old_due_date
        self._new_status = new_status if new_status is not None else self._old_status
        self._new_priority = new_priority if new_priority is not None else self._old_priority
        self._new_complexity = new_complexity if new_complexity is not None else self._old_complexity
        self._new_project_id = new_project_id if new_project_id is not None else self._old_project_id
        
        super().__init__(f"Edit task '{self._old_title}'")

    def redo(self) -> None:
        """Apply the edit (set new values)."""
        self._service.update_task(
            task_id=self._task_id,
            title=self._new_title,
            description=self._new_description,
            due_date=self._new_due_date,
            status=self._new_status,
            priority=self._new_priority,
            complexity=self._new_complexity,
            project_id=self._new_project_id
        )

    def undo(self) -> None:
        """Restore task to previous state."""
        self._service.update_task(
            task_id=self._task_id,
            title=self._old_title,
            description=self._old_description,
            due_date=self._old_due_date,
            status=self._old_status,
            priority=self._old_priority,
            complexity=self._old_complexity,
            project_id=self._old_project_id
        )


class DeleteTaskCommand(UndoCommand):
    """Command for deleting a task.
    
    Captures task data before deletion to enable restoration.
    """

    def __init__(
        self,
        service: Any,  # TaskService instance
        task_id: int,
    ):
        """Initialize DeleteTaskCommand.
        
        Args:
            service: TaskService instance for CRUD operations
            task_id: ID of task to delete
        """
        self._service = service
        self._task_id = task_id
        
        # Capture task data before deletion
        task = self._service.get_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")
        
        self._title = task.title
        self._task_description = task.description  # Renamed to avoid conflict
        self._due_date = task.due_date
        self._status = task.status
        self._priority = task.priority
        self._complexity = task.complexity
        self._project_id = task.project_id
        self._user_id = task.user_id
        
        super().__init__(f"Delete task '{self._title}'")

    def redo(self) -> None:
        """Delete the task."""
        self._service.delete_task(self._task_id)

    def undo(self) -> None:
        """Restore the deleted task.
        
        When undoing a delete, the task is recreated with its original ID preserved.
        """
        # Recreate task with same data AND same ID (critical for undo/redo consistency)
        task = self._service.create_task(
            title=self._title,
            description=self._task_description,
            due_date=self._due_date,
            status=self._status,
            priority=self._priority,
            complexity=self._complexity,
            project_id=self._project_id,
            user_id=self._user_id,
            id=self._task_id  # Preserve original ID
        )
        # Verify ID was preserved
        if task.id != self._task_id:
            raise RuntimeError(f"Failed to restore task with original ID {self._task_id}, got {task.id}")


class EditTaskPropertiesCommand(UndoCommand):
    """Specialized command for changing task properties (priority, complexity).
    
    Handles undo/redo specifically for task property changes.
    This command focuses on property updates and provides clear, atomic
    undo/redo operations for each property change.
    """

    def __init__(
        self,
        service: Any,  # TaskService instance
        task_id: int,
        new_priority: Optional[Any] = None,  # TaskPriority enum or string
        new_complexity: Optional[Any] = None,  # TaskComplexity enum or string
    ):
        """Initialize EditTaskPropertiesCommand.
        
        Args:
            service: TaskService instance for CRUD operations
            task_id: ID of task to edit
            new_priority: New priority level (if changing)
            new_complexity: New complexity level (if changing)
        """
        if new_priority is None and new_complexity is None:
            raise ValueError("At least one property (priority or complexity) must be specified")
        
        self._service = service
        self._task_id = task_id
        
        # Capture current state before change
        current_task = self._service.get_task(task_id)
        if current_task is None:
            raise ValueError(f"Task {task_id} not found")
        
        self._old_priority = current_task.priority
        self._old_complexity = current_task.complexity
        
        # Store new values (use old if not changing)
        self._new_priority = new_priority if new_priority is not None else self._old_priority
        self._new_complexity = new_complexity if new_complexity is not None else self._old_complexity
        
        # Build description based on what changed
        changes = []
        if new_priority is not None:
            changes.append(f"priority to {self._new_priority}")
        if new_complexity is not None:
            changes.append(f"complexity to {self._new_complexity}")
        
        description = f"Change task properties: {', '.join(changes)}"
        super().__init__(description)

    def redo(self) -> None:
        """Apply the property changes."""
        self._service.update_task(
            task_id=self._task_id,
            priority=self._new_priority,
            complexity=self._new_complexity
        )

    def undo(self) -> None:
        """Restore task properties to previous state."""
        self._service.update_task(
            task_id=self._task_id,
            priority=self._old_priority,
            complexity=self._old_complexity
        )