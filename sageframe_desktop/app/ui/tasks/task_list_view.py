"""Simple task list view with table display."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush


class TaskListView(QWidget):
    """Simple list/table view for tasks.
    
    Displays tasks in expandable tree structure with columns:
    - Task name
    - Status
    - Due date
    - Priority
    """
    
    # Signals
    taskDoubleClicked = Signal(int)  # task_id
    createTaskRequested = Signal()
    
    def __init__(self, task_view_model, parent=None):
        super().__init__(parent)
        self.task_view_model = task_view_model
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Build the list view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Top bar with New Task button
        top_bar = QHBoxLayout()
        new_task_btn = QPushButton("+ New Task")
        new_task_btn.setObjectName("newTaskButton")
        new_task_btn.clicked.connect(self.createTaskRequested.emit)
        new_task_btn.setStyleSheet("""
            QPushButton#newTaskButton {
                background: #c69749;
                color: #1e1e1e;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton#newTaskButton:hover {
                background: #d4a84e;
            }
        """)
        top_bar.addWidget(new_task_btn)
        top_bar.addStretch()
        layout.addLayout(top_bar)
        
        # Tree widget for hierarchical task list
        self.tree_widget = QTreeWidget()
        self.tree_widget.setObjectName("taskTreeWidget")
        self.tree_widget.setHeaderLabels(["Task", "Status", "Due Date", "Priority"])
        self.tree_widget.setColumnCount(4)
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setRootIsDecorated(True)  # Show expand/collapse arrows
        self.tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # Configure column widths
        header = self.tree_widget.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Task name stretch
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Due date
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Priority
        
        # Styling
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 6px;
                border-bottom: 1px solid #2a2a2a;
            }
            QTreeWidget::item:hover {
                background: rgba(198, 151, 73, 0.1);
            }
            QTreeWidget::item:selected {
                background: rgba(198, 151, 73, 0.2);
                color: #c69749;
            }
            QHeaderView::section {
                background: #2d2d2d;
                color: #a0a0a0;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #c69749;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.tree_widget)
    
    def _connect_signals(self):
        """Connect view model signals."""
        if self.task_view_model:
            self.task_view_model.tasksListChanged.connect(self.refresh)
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle tree item double click."""
        task_id = item.data(0, Qt.ItemDataRole.UserRole)
        if task_id:
            self.taskDoubleClicked.emit(task_id)
    
    def refresh(self):
        """Refresh the task list from view model."""
        self.tree_widget.clear()
        
        if not self.task_view_model:
            return
        
        # Get tasks from view model (use the correct method)
        tasks_list = self.task_view_model.get_tasks_list()
        
        # Simple flat list for MVP (hierarchical grouping can be added later)
        for task_dict in tasks_list:
            # Skip completed tasks in the active list
            if task_dict.get('status') == 'done':
                continue
            self._add_task_dict(task_dict)
    
    def _add_task_dict(self, task_dict: dict):
        """Add a task item to the tree from dict."""
        item = QTreeWidgetItem()
        
        # Task name (use 'title' field, fallback to 'name')
        title = task_dict.get('title', task_dict.get('name', ''))
        item.setText(0, title)
        item.setData(0, Qt.ItemDataRole.UserRole, task_dict.get('id'))
        
        # Status
        status_text = task_dict.get('status', 'todo')
        item.setText(1, status_text)
        
        # Color code by status
        if status_text == "done":
            item.setForeground(1, QBrush(QColor("#4ade80")))  # Green
        elif status_text == "in_progress":
            item.setForeground(1, QBrush(QColor("#60a5fa")))  # Blue
        elif status_text == "blocked":
            item.setForeground(1, QBrush(QColor("#f87171")))  # Red
        else:
            item.setForeground(1, QBrush(QColor("#a0a0a0")))  # Gray
        
        # Due date
        due_date_text = task_dict.get('due_date', '—')
        if due_date_text and due_date_text != '—':
            # If it's a date object, format it
            if hasattr(due_date_text, 'strftime'):
                due_date_text = due_date_text.strftime("%Y-%m-%d")
        item.setText(2, due_date_text if due_date_text else "—")
        
        # Priority
        priority_val = task_dict.get('priority', '')
        if priority_val:
            priority_val_str = priority_val.value if hasattr(priority_val, 'value') else str(priority_val)
            if priority_val_str == "high":
                item.setText(3, "🔴 High")
                item.setForeground(3, QBrush(QColor("#f87171")))
            elif priority_val_str == "medium":
                item.setText(3, "🟡 Medium")
                item.setForeground(3, QBrush(QColor("#fbbf24")))
            elif priority_val_str == "low":
                item.setText(3, "🟢 Low")
                item.setForeground(3, QBrush(QColor("#4ade80")))
            else:
                item.setText(3, "—")
        else:
            item.setText(3, "—")
        
        self.tree_widget.addTopLevelItem(item)
