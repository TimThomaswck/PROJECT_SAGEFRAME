"""ViewModel dedicated to Gantt chart interactions."""

from datetime import datetime
from typing import Dict, List, Optional

from app.modules.tasks.services import TaskService
from app.modules.tasks.models import TaskDependencyType


class GanttViewModel:
    """Lightweight ViewModel for Gantt chart operations.

    Keeps database interactions contained to timeline and dependency updates.
    """

    def __init__(self, service: Optional[TaskService] = None, refresh_callback=None):
        self._service = service or TaskService()
        self._refresh_callback = refresh_callback

    def load_tasks(self, project_id: Optional[int] = None) -> List[Dict]:
        """Fetch tasks with timeline metadata for Gantt rendering."""
        tasks = self._service.list_tasks(project_id=project_id)
        gantt_tasks: List[Dict] = []
        for task in tasks:
            # Only include tasks with both start and end to render a bar
            if getattr(task, "start_date", None) is None or getattr(task, "end_date", None) is None:
                continue
            gantt_tasks.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "start_date": task.start_date,
                    "end_date": task.end_date,
                    "depends_on_task_id": getattr(task, "depends_on_task_id", None),
                    "dependency_type": getattr(task, "dependency_type", None),
                    "project_id": task.project_id,
                }
            )
        return sorted(gantt_tasks, key=lambda t: t["id"])

    def update_task_dates(self, task_id: int, start_date: datetime, end_date: datetime) -> bool:
        """Persist date changes after interactive updates.

        Returns True when update succeeds; returns False for validation failures.
        """
        if end_date < start_date:
            return False
        try:
            updated = self._service.update_task(task_id=task_id, start_date=start_date, end_date=end_date)
            if updated is not None and self._refresh_callback:
                self._refresh_callback()
            return updated is not None
        except ValueError:
            return False
        except Exception:
            return False

    def set_dependency(self, task_id: int, depends_on_task_id: Optional[int], dependency_type: Optional[TaskDependencyType]) -> bool:
        """Update task dependency metadata."""
        try:
            updated = self._service.update_task(
                task_id=task_id,
                depends_on_task_id=depends_on_task_id,
                dependency_type=dependency_type,
            )
            if updated is not None and self._refresh_callback:
                self._refresh_callback()
            return updated is not None
        except ValueError:
            return False
        except Exception:
            return False

    def close(self):
        """Dispose the underlying service if owned here."""
        if hasattr(self._service, "close"):
            self._service.close()
