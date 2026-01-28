# Task Detail View Fix - Implementation Summary

## Issue Description
When clicking on tasks in the Projects view, no detail window was appearing. Similarly, clicking tasks in the Tasks list view wasn't displaying the task details properly.

## Root Cause
The `TaskViewWidget` was being displayed using the `.show()` method which creates a standalone window, but it wasn't appearing properly as it was just a `QWidget` without proper window management.

## Solution Implemented
Modified all task detail view openings to wrap the `TaskViewWidget` in a proper `QDialog` container. This ensures the task details appear as modal dialogs that are properly managed by the Qt window system.

### Files Modified
- [app/main_window.py](sageframe_desktop/app/main_window.py)

### Changes Made

#### 1. Project View Task Details (Lines 1258-1278)
**Function**: `_open_project_view` → `open_task_view` (nested function)

**Before**:
```python
def open_task_view(item):
    task_id = item.data(Qt.ItemDataRole.UserRole)
    if task_id:
        from app.modules.tasks.views import TaskViewWidget
        task_view = TaskViewWidget(view_model=self.task_view_model, parent=dialog)
        task_view.set_task_id(task_id)
        task_view.show()
```

**After**:
```python
def open_task_view(item):
    task_id = item.data(Qt.ItemDataRole.UserRole)
    if task_id:
        from app.modules.tasks.views import TaskViewWidget
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        # Create a dialog to contain the task view
        task_dialog = QDialog(dialog)
        task_dialog.setWindowTitle(self.tr("Task Details"))
        task_dialog.setMinimumSize(600, 500)
        
        task_layout = QVBoxLayout()
        task_view = TaskViewWidget(view_model=self.task_view_model, parent=task_dialog)
        task_view.set_task_id(task_id)
        task_layout.addWidget(task_view)
        
        task_dialog.setLayout(task_layout)
        task_dialog.exec()
```

#### 2. Task List Double-Click Handler (Lines 1567-1583)
**Function**: `_on_task_double_clicked`

**Before**:
```python
def _on_task_double_clicked(self, item):
    """Handle task list item double-click (AC#2)."""
    task_id = item.data(Qt.ItemDataRole.UserRole)
    if task_id:
        # Open task view widget
        view_widget = TaskViewWidget(view_model=self.task_view_model, parent=self)
        view_widget.set_task_id(task_id)
        view_widget.show()
```

**After**:
```python
def _on_task_double_clicked(self, item):
    """Handle task list item double-click (AC#2)."""
    task_id = item.data(Qt.ItemDataRole.UserRole)
    if task_id:
        # Open task view widget in a dialog
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        task_dialog = QDialog(self)
        task_dialog.setWindowTitle(self.tr("Task Details"))
        task_dialog.setMinimumSize(600, 500)
        
        task_layout = QVBoxLayout()
        view_widget = TaskViewWidget(view_model=self.task_view_model, parent=task_dialog)
        view_widget.set_task_id(task_id)
        task_layout.addWidget(view_widget)
        
        task_dialog.setLayout(task_layout)
        task_dialog.exec()
```

#### 3. Task Single-Click Handler (Lines 1594-1610)
**Function**: `_on_task_clicked`

**Before**:
```python
def _on_task_clicked(self, item):
    """Open task details for editing on single click."""
    task_id = item.data(Qt.ItemDataRole.UserRole)
    if not task_id:
        return
    view_widget = TaskViewWidget(view_model=self.task_view_model, parent=self)
    view_widget.set_task_id(task_id)
    view_widget.show()
```

**After**:
```python
def _on_task_clicked(self, item):
    """Open task details for editing on single click."""
    task_id = item.data(Qt.ItemDataRole.UserRole)
    if not task_id:
        return
    # Open task view widget in a dialog
    from PySide6.QtWidgets import QDialog, QVBoxLayout
    task_dialog = QDialog(self)
    task_dialog.setWindowTitle(self.tr("Task Details"))
    task_dialog.setMinimumSize(600, 500)
    
    task_layout = QVBoxLayout()
    view_widget = TaskViewWidget(view_model=self.task_view_model, parent=task_dialog)
    view_widget.set_task_id(task_id)
    task_layout.addWidget(view_widget)
    
    task_dialog.setLayout(task_layout)
    task_dialog.exec()
```

## Testing Instructions

### 1. Test Task Details in Projects View
1. Launch the SageFrame Desktop application
2. Navigate to the "Projects" view
3. Double-click on any project to open the project details
4. In the "Tasks in this project:" section, double-click on any task
5. **Expected**: A modal dialog should appear showing the task details including:
   - Task title
   - Description
   - Status
   - Due date
   - Project information
   - Edit, Delete, and Close buttons

### 2. Test Task Details in Tasks List View
1. Navigate to the "Tasks" view
2. Double-click on any task in the task list
3. **Expected**: Same modal dialog as above should appear

### 3. Test Task Details from Single-Click (if enabled)
1. In the Tasks view, single-click on a task
2. **Expected**: Task details dialog should appear (if this functionality is enabled)

## Benefits
- **Consistent UI behavior**: All task detail views now use the same modal dialog approach
- **Better UX**: Modal dialogs properly focus user attention on the task being viewed
- **Proper window management**: Qt handles the dialog lifecycle correctly
- **Parent-child relationships**: Dialogs are properly parented to their calling windows

## Technical Notes
- All dialogs are modal (`exec()`) which blocks interaction with the parent window
- Minimum size of 600x500 ensures adequate space for task information
- Dialog parent is set to the calling window/dialog for proper window hierarchy
- Layout uses QVBoxLayout with the TaskViewWidget as the only child

## Git Commit
```
commit 8724fc9
Author: [Your Name]
Date: [Current Date]

Fix task detail view display in project and tasks views - wrap TaskViewWidget in dialogs
```

## Status
✅ **COMPLETED** - All three task view opening scenarios now properly display task details in modal dialogs.
