#!/usr/bin/env python3
"""Test quick-add task and note creation functionality."""

import sys
import os
from datetime import datetime
from pathlib import Path

# Set up environment to prevent QApplication issues
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.tasks.services import TaskService
from app.modules.notes.services import NotesService
from app.modules.notes.models import NoteCreate
from app.database import init_db, get_db

def test_quick_add_task():
    """Test quick-add task creation with date."""
    print("Testing quick-add task creation...")
    init_db()
    
    service = TaskService()
    
    # Test task creation with date
    task = service.create_task(
        title="Test Quick-Add Task",
        priority="medium",
        status="todo",
        due_date=datetime(2026, 2, 1)
    )
    
    if task:
        print("✓ Task created successfully!")
        print(f"  - Title: {task.title}")
        print(f"  - Priority: {task.priority}")
        print(f"  - Status: {task.status}")
        print(f"  - Due Date: {task.due_date}")
        return True
    else:
        print("✗ Task creation failed!")
        return False

def test_quick_add_note():
    """Test quick-add note creation."""
    print("\nTesting quick-add note creation...")
    
    session = get_db()
    service = NotesService(session)
    
    # Test note creation
    note_data = NoteCreate(
        title="Test Quick-Add Note",
        content="This is a test note from quick-add dialog"
    )
    note = service.create_note(note_data)
    
    if note:
        print("✓ Note created successfully!")
        print(f"  - Title: {note.title}")
        print(f"  - Content: {note.content}")
        return True
    else:
        print("✗ Note creation failed!")
        return False

if __name__ == "__main__":
    try:
        task_ok = test_quick_add_task()
        note_ok = test_quick_add_note()
        
        if task_ok and note_ok:
            print("\n✅ All quick-add tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
