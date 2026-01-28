"""Interactive Gantt chart widget using pyqtgraph."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import pyqtgraph as pg
from pyqtgraph.graphicsItems.DateAxisItem import DateAxisItem
from pyqtgraph.graphicsItems.ROI import RectROI
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class GanttChartWidget(QWidget):
    """Render tasks on a timeline with drag/resize interactions."""
    
    # Signal emitted when a task bar is clicked
    taskClicked = Signal(int)  # task_id

    def __init__(self, view_model, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._view_model = view_model
        self._tasks: List[Dict] = []
        self._task_items: Dict[int, RectROI] = {}
        self._dependency_lines: List[pg.PlotDataItem] = []
        self._scale = "monthly"  # Default to monthly
        self._init_ui()
        # Add dummy tasks for visualization
        self._ensure_dummy_tasks()
        # Initial render
        self.refresh()

    def _init_ui(self) -> None:
        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(8)

        scale_label = QLabel(self.tr("Time Scale:"))
        self._scale_combo = QComboBox()
        self._scale_combo.addItems(["Weekly", "Monthly"])
        self._scale_combo.setCurrentText("Monthly")  # Default to Monthly
        self._scale_combo.currentTextChanged.connect(self.set_time_scale)

        controls.addWidget(scale_label)
        controls.addWidget(self._scale_combo)
        controls.addStretch()

        axis = DateAxisItem(orientation='bottom')
        self._plot = pg.PlotWidget(axisItems={'bottom': axis})
        self._plot.showGrid(x=True, y=True, alpha=0.3)
        self._plot.setLabel('left', self.tr('Tasks'))
        # Disable mouse zoom to prevent zooming
        self._plot.setMouseEnabled(x=False, y=False)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(self._plot)
        self.setLayout(layout)

    def refresh(self) -> None:
        """Reload tasks from the ViewModel and redraw the chart."""
        if hasattr(self._view_model, "load_tasks"):
            self._tasks = self._view_model.load_tasks()
        else:
            self._tasks = []
        self._render_tasks()

    def _render_tasks(self) -> None:
        self._plot.clear()
        self._task_items.clear()
        self._dependency_lines.clear()
        if not self._tasks:
            return

        y_positions: Dict[int, float] = {}
        y_step = 1.5
        min_ts = None
        max_ts = None

        for idx, task in enumerate(self._tasks):
            start_dt = task.get("start_date")
            end_dt = task.get("end_date")
            if start_dt is None or end_dt is None:
                continue
            start_ts = start_dt.timestamp()
            end_ts = end_dt.timestamp()
            duration = max(end_ts - start_ts, 0.01)
            y = idx * y_step
            y_positions[task["id"]] = y

            # Determine color based on status or priority
            status = task.get("status", "todo")
            priority = task.get("priority", "medium")
            
            if status == "done":
                color = (76, 175, 80)  # Green
            elif status == "in_progress":
                color = (33, 150, 243)  # Blue
            elif status == "blocked":
                color = (244, 67, 54)   # Red
            elif priority == "high":
                color = (255, 152, 0)   # Orange
            else:
                color = (198, 151, 73)  # Gold (default)

            # Create ROI with colored pen
            pen = pg.mkPen(color=color, width=3)
            
            roi = RectROI(pos=(start_ts, y), size=(duration, 0.9), movable=True, resizable=True, pen=pen)
            
            roi.addScaleHandle((1, 0.5), (0, 0.5))
            roi.addScaleHandle((0, 0.5), (1, 0.5))
            roi.sigRegionChangeFinished.connect(lambda _roi=roi, task_id=task["id"]: self._on_roi_changed(task_id, _roi))
            # Add click handler for opening task details
            roi.sigClicked.connect(lambda _roi=roi, task_id=task["id"]: self._on_task_bar_clicked(task_id))
            self._plot.addItem(roi)
            self._task_items[task["id"]] = roi

            # Add task title label with white text
            label = pg.TextItem(text=task.get("title", ""), anchor=(0, 0.5), color=(255, 255, 255))
            label.setPos(start_ts, y + 0.45)
            self._plot.addItem(label)

            min_ts = start_ts if min_ts is None else min(min_ts, start_ts)
            max_ts = end_ts if max_ts is None else max(max_ts, end_ts)

        self._render_dependencies(y_positions)
        self._apply_view_range(min_ts, max_ts)

    def _render_dependencies(self, y_positions: Dict[int, float]) -> None:
        for task in self._tasks:
            dep_id = task.get("depends_on_task_id")
            if dep_id is None or dep_id not in y_positions or task.get("id") not in self._task_items:
                continue
            source_roi = self._task_items.get(dep_id)
            target_roi = self._task_items.get(task["id"])
            if source_roi is None or target_roi is None:
                continue
            source_x = source_roi.pos()[0] + source_roi.size()[0]
            source_y = y_positions[dep_id] + 0.45
            target_x = target_roi.pos()[0]
            target_y = y_positions[task["id"]] + 0.45
            line = self._plot.plot([source_x, target_x], [source_y, target_y], pen=pg.mkPen(color=(200, 200, 0), width=2))
            self._dependency_lines.append(line)

    def _apply_view_range(self, min_ts: float, max_ts: float) -> None:
        if min_ts is None or max_ts is None:
            return
        padding_days = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30,
        }.get(self._scale, 1)
        pad_seconds = padding_days * 24 * 3600
        self._plot.setXRange(min_ts - pad_seconds, max_ts + pad_seconds, padding=0)
        self._plot.setYRange(-0.5, len(self._tasks) * 1.5 + 0.5)

    def _on_roi_changed(self, task_id: int, roi: RectROI) -> None:
        start_ts = roi.pos()[0]
        duration = roi.size()[0]
        start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(start_ts + duration, tz=timezone.utc)
        self.apply_task_time_change(task_id, start_dt, end_dt)

    def apply_task_time_change(self, task_id: int, start_date: datetime, end_date: datetime) -> bool:
        if end_date < start_date:
            return False
        if hasattr(self._view_model, "update_task_dates"):
            return bool(self._view_model.update_task_dates(task_id, start_date, end_date))
        return False

    def set_time_scale(self, value: str) -> None:
        """Update current scale and refresh view range."""
        normalized = value.lower()
        if normalized not in {"weekly", "monthly"}:
            return
        self._scale = normalized
        if self._tasks:
            min_ts = min(t["start_date"].timestamp() for t in self._tasks if t.get("start_date"))
            max_ts = max(t["end_date"].timestamp() for t in self._tasks if t.get("end_date"))
            self._apply_view_range(min_ts, max_ts)

    def current_scale(self) -> str:
        return self._scale

    def task_count(self) -> int:
        return len(self._tasks)
    
    def _on_task_bar_clicked(self, task_id: int) -> None:
        """Handle click on a task bar in the gantt chart."""
        self.taskClicked.emit(task_id)
    
    def _ensure_dummy_tasks(self) -> None:
        """Create dummy tasks if the gantt chart is empty."""
        try:
            from app.modules.tasks.services import TaskService
            from app.database import get_db
            
            service = TaskService()
            tasks = service.list_tasks()
            
            # Only create dummy tasks if no tasks with dates exist
            has_tasks_with_dates = any(
                hasattr(t, 'start_date') and hasattr(t, 'end_date') and 
                t.start_date is not None and t.end_date is not None 
                for t in tasks
            )
            
            if has_tasks_with_dates:
                return  # Already have tasks with dates
            
            # Create 3 dummy tasks with dates
            today = datetime.now(timezone.utc)
            
            dummy_tasks = [
                {
                    "title": "Frontend Development Sprint",
                    "start_date": today,
                    "end_date": today + timedelta(days=14),
                    "priority": "high",
                    "status": "in_progress"
                },
                {
                    "title": "Backend API Integration",
                    "start_date": today + timedelta(days=7),
                    "end_date": today + timedelta(days=28),
                    "priority": "medium",
                    "status": "todo"
                },
                {
                    "title": "User Acceptance Testing",
                    "start_date": today + timedelta(days=21),
                    "end_date": today + timedelta(days=35),
                    "priority": "high",
                    "status": "todo"
                }
            ]
            
            for task_data in dummy_tasks:
                service.create_task(**task_data)
            
        except Exception as e:
            print(f"Failed to create dummy tasks: {e}")
