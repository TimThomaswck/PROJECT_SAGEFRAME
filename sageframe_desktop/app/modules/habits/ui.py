"""Habit tracking UI components.

Story 7.1: Simple Habit Tracker

Provides PySide6 UI for habit tracking with daily checkmarks and progress views.
Implements Atomic Design principles with reusable components.
"""

from datetime import date, timedelta
from typing import List, Callable, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QDialog, QLineEdit, QTextEdit,
    QCalendarWidget, QFrame, QScrollArea, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QDate, QSize
from PySide6.QtGui import QIcon, QColor, QFont

from app.modules.habits.models import Habit


class HabitCheckbox(QPushButton):
    """Atomic component: Habit daily checkbox.
    
    Simple clickable checkbox for marking habit complete/incomplete.
    Emits signals when toggled.
    
    Story 7.1 AC2: Mark habit complete with single click
    """
    
    completed_changed = Signal(bool)
    
    def __init__(self, completed: bool = False, parent=None):
        super().__init__(parent)
        self.is_completed = completed
        self.setFixedSize(QSize(40, 40))
        self.setCheckable(True)
        self.setChecked(completed)
        self.clicked.connect(self._on_clicked)
        self.update_appearance()
    
    def _on_clicked(self):
        """Handle checkbox click."""
        self.is_completed = self.isChecked()
        self.update_appearance()
        self.completed_changed.emit(self.is_completed)
    
    def update_appearance(self):
        """Update button appearance based on state."""
        if self.is_completed:
            self.setText("✓")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 18px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        else:
            self.setText("○")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    color: #999;
                    border-radius: 5px;
                    font-size: 18px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """)
    
    def set_completed(self, completed: bool):
        """Set completion state without emitting signal."""
        self.is_completed = completed
        self.setChecked(completed)
        self.update_appearance()


class WeeklyProgressView(QWidget):
    """Molecule: Weekly habit progress display.
    
    Shows 7-day week with checkmarks for each day.
    
    Story 7.1 AC3: View progress for current week
    """
    
    def __init__(self, habit: Habit, week_dates: List[date], completions: List[bool],
                 on_completion_changed: Callable = None, parent=None):
        super().__init__(parent)
        self.habit = habit
        self.week_dates = week_dates
        self.completions = completions
        self.on_completion_changed = on_completion_changed
        self.checkboxes = []
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QHBoxLayout(self)
        
        # Day labels and checkboxes
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        for i, day_name in enumerate(day_names):
            container = QVBoxLayout()
            
            # Day label
            day_label = QLabel(day_name)
            day_label.setAlignment(Qt.AlignCenter)
            container.addWidget(day_label)
            
            # Checkbox
            checkbox = HabitCheckbox(self.completions[i])
            checkbox.completed_changed.connect(
                lambda checked, idx=i: self._on_checkbox_changed(idx, checked)
            )
            self.checkboxes.append(checkbox)
            container.addWidget(checkbox)
            
            # Date label
            date_label = QLabel(str(self.week_dates[i].day))
            date_label.setAlignment(Qt.AlignCenter)
            date_label.setStyleSheet("color: #999; font-size: 10px;")
            container.addWidget(date_label)
            
            layout.addLayout(container)
    
    def _on_checkbox_changed(self, day_index: int, completed: bool):
        """Handle checkbox change."""
        if self.on_completion_changed:
            self.on_completion_changed(self.week_dates[day_index], completed)


class MonthlyProgressView(QWidget):
    """Molecule: Monthly habit progress display.
    
    Shows calendar grid with checkmarks for each day.
    
    Story 7.1 AC3: View progress for current month
    """
    
    def __init__(self, habit: Habit, month_dates: List[date], completions: List[bool],
                 on_completion_changed: Callable = None, parent=None):
        super().__init__(parent)
        self.habit = habit
        self.month_dates = month_dates
        self.completions = completions
        self.on_completion_changed = on_completion_changed
        self.checkboxes = []
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QGridLayout(self)
        
        # Day headers
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for col, day_name in enumerate(day_names):
            header = QLabel(day_name)
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet("font-weight: bold;")
            layout.addWidget(header, 0, col)
        
        # Calendar grid
        row = 1
        col = 0
        
        # Get first day of month weekday
        first_date = self.month_dates[0]
        first_weekday = first_date.weekday()
        
        # Add empty cells before first day
        col = first_weekday
        
        for i, date_obj in enumerate(self.month_dates):
            # Create checkbox
            checkbox = HabitCheckbox(self.completions[i])
            checkbox.completed_changed.connect(
                lambda checked, idx=i: self._on_checkbox_changed(idx, checked)
            )
            self.checkboxes.append(checkbox)
            
            # Create frame with date label
            frame = QFrame()
            frame_layout = QVBoxLayout(frame)
            
            date_label = QLabel(str(date_obj.day))
            date_label.setAlignment(Qt.AlignCenter)
            date_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            
            frame_layout.addWidget(date_label)
            frame_layout.addWidget(checkbox)
            frame_layout.setContentsMargins(5, 5, 5, 5)
            
            layout.addWidget(frame, row, col)
            
            # Move to next cell
            col += 1
            if col > 6:
                col = 0
                row += 1
    
    def _on_checkbox_changed(self, day_index: int, completed: bool):
        """Handle checkbox change."""
        if self.on_completion_changed:
            self.on_completion_changed(self.month_dates[day_index], completed)


class HabitCreationDialog(QDialog):
    """Molecule: Habit creation dialog.
    
    Dialog for creating new habits with name and optional description.
    
    Story 7.1 AC1: Create and name new habits
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name_input = None
        self.description_input = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("Create New Habit")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Name label and input
        name_label = QLabel("Habit Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Morning Exercise")
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        
        # Description label and input
        description_label = QLabel("Description (optional):")
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("e.g., 30 minutes of cardio")
        self.description_input.setMaximumHeight(80)
        layout.addWidget(description_label)
        layout.addWidget(self.description_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create Habit")
        create_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def get_habit_data(self):
        """Get entered habit data.
        
        Returns:
            Tuple of (name, description)
        """
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        return name, description if description else None


class HabitListItem(QFrame):
    """Molecule: Single habit list item.
    
    Displays habit with completion status and quick actions.
    
    Story 7.1 AC2: Mark habit complete with single click
    """
    
    completion_toggled = Signal(int, bool)
    edit_requested = Signal(int)
    delete_requested = Signal(int)
    
    def __init__(self, habit: Habit, is_completed: bool, parent=None):
        super().__init__(parent)
        self.habit = habit
        self.is_completed = is_completed
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout(self)
        
        # Habit name and description
        info_layout = QVBoxLayout()
        
        name_label = QLabel(self.habit.name)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(name_label)
        
        if self.habit.description:
            desc_label = QLabel(self.habit.description)
            desc_label.setStyleSheet("color: #666; font-size: 11px;")
            info_layout.addWidget(desc_label)
        
        layout.addLayout(info_layout, 1)
        
        # Completion checkbox
        checkbox = HabitCheckbox(self.is_completed)
        checkbox.completed_changed.connect(self._on_completion_changed)
        layout.addWidget(checkbox)
        
        # Action buttons
        edit_btn = QPushButton("Edit")
        edit_btn.setMaximumWidth(60)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.habit.id))
        layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setMaximumWidth(60)
        delete_btn.setStyleSheet("color: red;")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.habit.id))
        layout.addWidget(delete_btn)
    
    def _on_completion_changed(self, completed: bool):
        """Handle completion change."""
        self.is_completed = completed
        self.completion_toggled.emit(self.habit.id, completed)


class HabitTrackerView(QWidget):
    """Organism: Main habit tracking view.
    
    Complete habit tracking interface with list, progress views, and actions.
    
    Story 7.1 AC1, AC2, AC3: Full habit tracking functionality
    """
    
    habit_created = Signal(str, str)  # name, description
    habit_completed = Signal(int, date, bool)  # habit_id, date, completed
    habit_deleted = Signal(int)  # habit_id
    
    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.init_ui()
        self.load_habits()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🎯 Habits")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Controls
        controls = QHBoxLayout()
        
        new_habit_btn = QPushButton("+ New Habit")
        new_habit_btn.clicked.connect(self._on_new_habit)
        controls.addWidget(new_habit_btn)
        
        # View mode selector
        week_btn = QPushButton("Week")
        week_btn.setCheckable(True)
        week_btn.setChecked(True)
        week_btn.clicked.connect(lambda: self._set_view_mode("week"))
        controls.addWidget(week_btn)
        
        month_btn = QPushButton("Month")
        month_btn.setCheckable(True)
        month_btn.clicked.connect(lambda: self._set_view_mode("month"))
        controls.addWidget(month_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Habit list
        self.habit_list = QListWidget()
        layout.addWidget(self.habit_list)
        
        # Progress view (placeholder)
        self.progress_view = QWidget()
        layout.addWidget(self.progress_view)
        
        self.setLayout(layout)
    
    def _on_new_habit(self):
        """Handle new habit creation."""
        dialog = HabitCreationDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name, description = dialog.get_habit_data()
            if name:
                try:
                    habit = self.service.create_habit(name, description or "")
                    self.habit_created.emit(name, description or "")
                    self.load_habits()  # Refresh list
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to create habit: {e}")
    
    def _set_view_mode(self, mode: str):
        """Switch between week and month view."""
        # This would be implemented with actual view switching
        pass
    
    def load_habits(self):
        """Load habits from service and update display."""
        try:
            habits = self.service.get_all_habits()
            today = date.today()
            
            # Get today's completions
            completions_today = {}
            for habit in habits:
                completions_today[habit.id] = self.service.is_completed(habit.id, today)
            
            self.update_habits(habits, completions_today)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load habits: {e}")
    
    def update_habits(self, habits: List[Habit], completions_today: dict):
        """Update habit list display.
        
        Args:
            habits: List of habit objects
            completions_today: Dict of {habit_id: is_completed}
        """
        self.habit_list.clear()
        
        if not habits:
            # Show empty state
            empty_label = QLabel("No habits yet. Click '+ New Habit' to create your first!")
            empty_label.setStyleSheet("color: gray; padding: 20px; font-style: italic;")
            empty_label.setAlignment(Qt.AlignCenter)
            list_item = QListWidgetItem(self.habit_list)
            list_item.setSizeHint(empty_label.sizeHint())
            self.habit_list.addItem(list_item)
            self.habit_list.setItemWidget(list_item, empty_label)
            return
        
        for habit in habits:
            is_completed = completions_today.get(habit.id, False)
            item = HabitListItem(habit, is_completed)
            item.completion_toggled.connect(self._on_habit_toggled)
            item.delete_requested.connect(self._on_habit_delete)
            
            list_item = QListWidgetItem(self.habit_list)
            list_item.setSizeHint(item.sizeHint())
            self.habit_list.addItem(list_item)
            self.habit_list.setItemWidget(list_item, item)
    
    def _on_habit_delete(self, habit_id: int):
        """Handle habit deletion."""
        reply = QMessageBox.question(
            self,
            "Delete Habit",
            "Are you sure you want to delete this habit? All completion history will be lost.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.service.delete_habit(habit_id)
                self.habit_deleted.emit(habit_id)
                self.load_habits()  # Refresh list
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete habit: {e}")
    
    def _on_habit_toggled(self, habit_id: int, completed: bool):
        """Handle habit completion toggle."""
        try:
            if completed:
                self.service.mark_complete(habit_id, date.today())
            else:
                self.service.unmark_complete(habit_id, date.today())
            self.habit_completed.emit(habit_id, date.today(), completed)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update habit: {e}")
            self.load_habits()  # Refresh to show correct state
