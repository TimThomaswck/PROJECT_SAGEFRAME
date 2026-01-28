"""Projects module for Sageframe.

Provides project management functionality including CRUD operations,
data persistence, and UI components.
"""

from app.modules.projects.models import Project, ProjectSchema
from app.modules.projects.services import ProjectService
from app.modules.projects.view_models import ProjectViewModel
from app.modules.projects.views import (
    ProjectCreateDialog,
    ProjectViewWidget,
    ProjectEditDialog
)

__all__ = [
    'Project',
    'ProjectSchema',
    'ProjectService',
    'ProjectViewModel',
    'ProjectCreateDialog',
    'ProjectViewWidget',
    'ProjectEditDialog',
]
