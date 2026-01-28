"""Habit Tracker Grid View - Habitica-style habit management.

Features:
- Grid layout with habits as rows and dates as columns
- Editable checkboxes for today onwards
- Read-only historical data with visual progress
- Streak tracking and completion statistics
- Add/edit/delete habit management
- Quick completion status visualization
"""

from datetime import datetime, timedelta, date
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDialog, QFormLayout, QLineEdit, QComboBox,
    QCheckBox, QMessageBox, QHeaderView, QAbstractItemView, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QColor, QBrush, QFont, QIcon

from app.database import SessionLocal
from app.modules.habits.models import Habit, HabitCompletion
from app.modules.habits.service import HabitService


class HabitTrackerGrid(QWidget):
    """Habitica-style habit tracker with grid view and progress tracking.
    
    Signals:
        habitAdded: Emitted when new habit is created
        habitUpdated: Emitted when habit is updated
        habitDeleted: Emitted when habit is deleted
    """
    
    habitAdded = Signal(object)
    habitUpdated = Signal(object)
    habitDeleted = Signal(int)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("habitTrackerGrid")
        
        # Initialize service
        self.session = SessionLocal()
        self.habit_service = HabitService(self.session)
        
        # Configuration
        self.days_to_display = 7  # Show 7 days leading up to today
        self.days_before_today = 6  # Show 6 days before today (7 total with today)
        
        # Track data
        self.habits: List[Habit] = []
        self.completions: Dict[int, Dict[str, bool]] = {}
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Build the habit tracker UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header with title and add button
        header_layout = QHBoxLayout()
        title = QLabel("🎯 Habit Tracker")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #c69749;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_habit_btn = QPushButton("➕ New Habit")
        add_habit_btn.setStyleSheet(self._get_button_style())
        add_habit_btn.clicked.connect(self._open_add_habit_dialog)
        header_layout.addWidget(add_habit_btn)
        
        delete_habit_btn = QPushButton("🗑️ Delete Habit")
        delete_habit_btn.setStyleSheet(self._get_button_style())
        delete_habit_btn.clicked.connect(self._open_delete_habit_dialog)
        header_layout.addWidget(delete_habit_btn)
        
        layout.addLayout(header_layout)
        
        # Stats row
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Loading...")
        self.stats_label.setStyleSheet("color: #888; font-size: 12px;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Main grid table
        self.grid_table = QTableWidget()
        self.grid_table.setObjectName("habitGrid")
        self.grid_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.grid_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.grid_table.setShowGrid(True)
        self.grid_table.setStyleSheet(self._get_grid_style())
        self.grid_table.cellClicked.connect(self._on_cell_clicked)
        
        layout.addWidget(self.grid_table)
        
        # Legend/Info
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)
        
        legend_items = [
            ("🟢", "Completed Today", "#4ade80"),
            ("⚪", "Not Completed", "#9ca3af"),
            ("🔒", "Read-only (Past)", "#666"),
            ("⏳", "Editable (Future)", "#fbbf24"),
        ]
        
        for icon, label, color in legend_items:
            item_layout = QHBoxLayout()
            icon_label = QLabel(icon)
            text_label = QLabel(label)
            text_label.setStyleSheet("color: #888; font-size: 11px;")
            item_layout.addWidget(icon_label)
            item_layout.addWidget(text_label)
            legend_layout.addLayout(item_layout)
        
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
    
    def _get_button_style(self) -> str:
        """Get style for add button."""
        return """
            QPushButton {
                background-color: #c69749;
                color: #1e1e1e;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #d4a84e;
            }
            QPushButton:pressed {
                background-color: #b58738;
            }
        """
    
    def _get_grid_style(self) -> str:
        """Get stylesheet for grid table."""
        return """
            QTableWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                gridline-color: #2a2a2a;
            }
            QTableWidget::item {
                padding: 4px;
                border: 1px solid #2a2a2a;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #a0a0a0;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #c69749;
                font-weight: bold;
                font-size: 12px;
            }
            QTableWidget::item:selected {
                background-color: rgba(198, 151, 73, 0.2);
            }
        """
    
    def _load_data(self):
        """Load habits and completion data."""
        try:
            # Get all habits
            self.habits = self.habit_service.get_all_habits()
            
            # Load completions for date range
            self._load_completions()
            
            # Build grid
            self._build_grid()
            
            # Update stats
            self._update_stats()
            
        except Exception as e:
            print(f"Error loading habit data: {e}")
    
    def _load_completions(self):
        """Load completion data for all habits."""
        today = date.today()
        start_date = today - timedelta(days=self.days_before_today)
        end_date = today  # End at today
        
        self.completions = {}
        
        for habit in self.habits:
            completions_list = self.habit_service.get_all_completions(habit.id)
            self.completions[habit.id] = {}
            
            for completion in completions_list:
                # Parse date from string format if needed
                if isinstance(completion.completion_date, str):
                    comp_date = datetime.strptime(completion.completion_date, "%Y-%m-%d").date()
                else:
                    comp_date = completion.completion_date
                
                if start_date <= comp_date <= end_date:
                    self.completions[habit.id][comp_date.isoformat()] = True
    
    def _build_grid(self):
        """Build the habit grid table."""
        today = date.today()
        start_date = today - timedelta(days=self.days_before_today)
        end_date = today  # End at today
        
        # Generate date range
        current = start_date
        date_range = []
        while current <= end_date:
            date_range.append(current)
            current += timedelta(days=1)
        
        # Set up table
        num_rows = len(self.habits)
        num_cols = len(date_range)
        
        self.grid_table.setRowCount(num_rows)
        self.grid_table.setColumnCount(num_cols)
        
        # Set column headers with dates
        col_headers = []
        for col_idx, d in enumerate(date_range):
            if d == today:
                header_text = f"✏️ {d.strftime('%a')}\n{d.strftime('%m/%d')} (Today - Editable)"
            else:
                header_text = f"🔒 {d.strftime('%a')}\n{d.strftime('%m/%d')}"
            col_headers.append(header_text)
        
        self.grid_table.setHorizontalHeaderLabels(col_headers)
        
        # Highlight today's column header
        for col_idx, d in enumerate(date_range):
            if d == today:
                header_item = self.grid_table.horizontalHeaderItem(col_idx)
                if header_item:
                    header_item.setBackground(QBrush(QColor("#c69749")))
                    header_item.setForeground(QBrush(QColor("#1e1e1e")))
        
        # Set row heights
        self.grid_table.verticalHeader().setDefaultSectionSize(50)
        self.grid_table.horizontalHeader().setDefaultSectionSize(100)
        
        # Fill habit rows
        for row_idx, habit in enumerate(self.habits):
            # Habit name cell (row header)
            habit_cell = QTableWidgetItem(f"{habit.name}")
            habit_cell.setFlags(habit_cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
            habit_cell.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            habit_cell.setForeground(QBrush(QColor("#c69749")))
            self.grid_table.setItem(row_idx, 0, habit_cell)
            
            # Add completion cells for each date
            for col_idx, current_date in enumerate(date_range):
                date_str = current_date.isoformat()
                is_completed = self.completions.get(habit.id, {}).get(date_str, False)
                
                cell = self._create_habit_cell(habit.id, current_date, is_completed)
                self.grid_table.setItem(row_idx, col_idx, cell)
        
        # Set row labels
        row_labels = [h.name for h in self.habits]
        self.grid_table.setVerticalHeaderLabels(row_labels)
    
    def _create_habit_cell(self, habit_id: int, current_date: date, is_completed: bool) -> QTableWidgetItem:
        """Create a habit grid cell."""
        today = date.today()
        
        cell = QTableWidgetItem()
        cell.setData(Qt.ItemDataRole.UserRole, habit_id)  # Store habit ID
        cell.setData(Qt.ItemDataRole.UserRole + 1, current_date.isoformat())  # Store date
        
        # Check if editable (today or future)
        is_editable = current_date >= today
        
        # Set display
        if is_completed:
            cell.setText("✅")
            if current_date == today:
                cell.setBackground(QBrush(QColor("#22c55e")))  # Brighter green for today
            else:
                cell.setBackground(QBrush(QColor("#4ade80")))  # Green for past
            cell.setForeground(QBrush(QColor("#1e1e1e")))
        else:
            cell.setText("⭕")
            if current_date == today:
                cell.setBackground(QBrush(QColor("#9ca3af")))  # Lighter grey for today
            else:
                cell.setBackground(QBrush(QColor("#6b7280")))  # Grey for past
            cell.setForeground(QBrush(QColor("#d4d4d4")))
        
        cell.setFont(QFont("Arial", 16))
        cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        
        # Set editability and interaction
        if is_editable:
            cell.setFlags(cell.flags() | Qt.ItemFlag.ItemIsEnabled)
            # Add subtle border to today's column
            if current_date == today:
                cell.setData(Qt.ItemDataRole.ToolTipRole, "✏️ Click to toggle (Editable)")
        else:
            cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
            cell.setBackground(QBrush(QColor("#404040")))  # Dark grey for past
            cell.setForeground(QBrush(QColor("#666")))
            cell.setData(Qt.ItemDataRole.ToolTipRole, "🔒 Read-only (Past date)")
        
        return cell
    
    def _on_cell_clicked(self, row: int, col: int):
        """Handle cell click - toggle completion for today and future dates."""
        if row >= len(self.habits):
            # Clicked on action row, ignore
            return
        
        habit = self.habits[row]
        cell = self.grid_table.item(row, col)
        
        if not cell:
            return
        
        date_str = cell.data(Qt.ItemDataRole.UserRole + 1)
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = date.today()
        
        # Only allow toggling today and future dates
        if target_date < today:
            return
        
        # Toggle completion
        self.toggle_completion(habit.id, date_str)
    
    def _open_add_habit_dialog(self):
        """Open dialog to create new habit."""
        dialog = AddHabitDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            habit_name, description = dialog.get_values()
            if habit_name.strip():
                try:
                    habit = self.habit_service.create_habit(
                        name=habit_name.strip(),
                        description=description.strip() if description else None
                    )
                    self.habits.append(habit)
                    # Initialize completion tracking for new habit
                    self.completions[habit.id] = {}
                    self._build_grid()
                    self._update_stats()
                    self.habitAdded.emit(habit)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create habit: {str(e)}")
    
    def _open_delete_habit_dialog(self):
        """Open dialog to delete a habit with dropdown selection."""
        if not self.habits:
            QMessageBox.information(self, "No Habits", "No habits to delete.")
            return
        
        dialog = DeleteHabitDialog(self.habits, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_habit = dialog.get_selected_habit()
            if selected_habit:
                self._delete_habit(selected_habit.id)
    
    def _delete_habit(self, habit_id: int):
        """Delete a habit."""
        reply = QMessageBox.warning(
            self,
            "Delete Habit",
            "Are you sure you want to delete this habit? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.habit_service.delete_habit(habit_id)
                self.habits = [h for h in self.habits if h.id != habit_id]
                del self.completions[habit_id]
                self._build_grid()
                self._update_stats()
                self.habitDeleted.emit(habit_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete habit: {str(e)}")
    
    def toggle_completion(self, habit_id: int, target_date: str):
        """Toggle habit completion for a date."""
        try:
            target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
            today = date.today()
            
            # Only allow today and future
            if target_date_obj < today:
                return
            
            # Check current state
            is_completed = self.completions.get(habit_id, {}).get(target_date, False)
            
            if is_completed:
                # Unmark
                self.habit_service.unmark_complete(habit_id, target_date_obj)
                self.completions[habit_id][target_date] = False
            else:
                # Mark
                self.habit_service.mark_complete(habit_id, target_date_obj)
                self.completions[habit_id][target_date] = True
            
            self._build_grid()
            self._update_stats()
            
        except Exception as e:
            print(f"Error toggling completion: {e}")
    
    def _update_stats(self):
        """Update statistics display."""
        if not self.habits:
            self.stats_label.setText("No habits yet. Create one to get started! 🎯")
            return
        
        today = date.today()
        today_str = today.isoformat()
        
        # Count today's completions
        today_completed = sum(
            1 for habit_id in self.completions
            if self.completions[habit_id].get(today_str, False)
        )
        
        # Calculate streaks
        streaks = []
        for habit in self.habits:
            streak = self._calculate_streak(habit.id)
            streaks.append(streak)
        
        avg_streak = sum(streaks) / len(streaks) if streaks else 0
        
        stats_text = (
            f"📊 Today: {today_completed}/{len(self.habits)} completed | "
            f"🔥 Average Streak: {avg_streak:.1f} days | "
            f"🎯 Total Habits: {len(self.habits)}"
        )
        self.stats_label.setText(stats_text)
    
    def _calculate_streak(self, habit_id: int) -> int:
        """Calculate current streak for a habit."""
        completions = self.completions.get(habit_id, {})
        
        # Start from yesterday and count backwards
        current = date.today() - timedelta(days=1)
        streak = 0
        
        while True:
            if completions.get(current.isoformat(), False):
                streak += 1
                current -= timedelta(days=1)
            else:
                break
        
        return streak


class AddHabitDialog(QDialog):
    """Dialog to create a new habit."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Add New Habit")
        self.setMinimumWidth(400)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Form
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.name_field = QLineEdit()
        self.name_field.setPlaceholderText("e.g., Morning Exercise, Read, Meditate")
        self.name_field.setStyleSheet(self._get_field_style())
        form.addRow("Habit Name:", self.name_field)
        
        self.description_field = QLineEdit()
        self.description_field.setPlaceholderText("e.g., 30 minutes of cardio (optional)")
        self.description_field.setStyleSheet(self._get_field_style())
        form.addRow("Description:", self.description_field)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("✅ Create Habit")
        save_btn.setStyleSheet(self._get_button_style())
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet(self._get_cancel_button_style())
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _get_field_style(self) -> str:
        """Get style for input fields."""
        return """
            QLineEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 2px solid #3e3e3e;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #c69749;
            }
        """
    
    def _get_button_style(self) -> str:
        """Get style for save button."""
        return """
            QPushButton {
                background-color: #4ade80;
                color: #1e1e1e;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #22c55e;
            }
        """
    
    def _get_cancel_button_style(self) -> str:
        """Get style for cancel button."""
        return """
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """
    
    def get_values(self) -> tuple:
        """Get form values."""
        return self.name_field.text(), self.description_field.text()


class DeleteHabitDialog(QDialog):
    """Dialog for selecting a habit to delete."""
    
    def __init__(self, habits: List[Habit], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Delete Habit")
        self.setMinimumWidth(300)
        self.habits = habits
        self.selected_habit = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Build dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Label
        label = QLabel("Select a habit to delete:")
        label.setStyleSheet("font-size: 13px;")
        layout.addWidget(label)
        
        # Dropdown
        self.habit_combo = QComboBox()
        self.habit_combo.setStyleSheet("""
            QComboBox {
                background-color: #404040;
                color: #d4d4d4;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                image: none;
            }
        """)
        
        for habit in self.habits:
            self.habit_combo.addItem(habit.name, habit.id)
        
        layout.addWidget(self.habit_combo)
        
        # Warning label
        warning = QLabel("⚠️ This cannot be undone.")
        warning.setStyleSheet("color: #fbbf24; font-size: 12px;")
        layout.addWidget(warning)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._get_cancel_button_style())
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        delete_btn.clicked.connect(self.accept)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
    
    def _get_cancel_button_style(self) -> str:
        """Get style for cancel button."""
        return """
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """
    
    def get_selected_habit(self) -> Optional[Habit]:
        """Get the selected habit from the combo box."""
        current_index = self.habit_combo.currentIndex()
        if current_index >= 0:
            return self.habits[current_index]
        return None
