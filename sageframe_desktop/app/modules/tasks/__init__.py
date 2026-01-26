"""Task management module for Sageframe.

This module provides functionality for creating, viewing, editing, and deleting tasks.
Tasks can be standalone or associated with a project (Story 2.1).
"""

from app.modules.tasks.models import Task, TaskSchema, TaskUpdateSchema
from app.modules.tasks.services import TaskService
from app.modules.tasks.view_models import TaskViewModel
from app.modules.tasks.views import TaskCreateDialog, TaskViewWidget, TaskEditDialog

__all__ = [
    'Task', 'TaskSchema', 'TaskUpdateSchema',
    'TaskService', 'TaskViewModel',
    'TaskCreateDialog', 'TaskViewWidget', 'TaskEditDialog'
]
