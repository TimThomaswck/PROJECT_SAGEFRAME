"""View model for notes management.

Provides a Qt-friendly interface for notes operations with signals.
"""

from typing import List, Optional
from PySide6.QtCore import QObject, Signal

from app.database import SessionLocal
from app.modules.notes.models import Note, NoteCreate, NoteUpdate
from app.modules.notes.services import NotesService


class NotesViewModel(QObject):
    """ViewModel for notes with Qt signals.
    
    Signals:
        note_created: Emitted when a note is created (note_id, title)
        note_updated: Emitted when a note is updated (note_id, title)
        note_deleted: Emitted when a note is deleted (note_id)
        notes_loaded: Emitted when notes list is refreshed
        error_occurred: Emitted when an error occurs (error_message)
    """
    
    note_created = Signal(int, str)  # note_id, title
    note_updated = Signal(int, str)  # note_id, title
    note_deleted = Signal(int)       # note_id
    notes_loaded = Signal()
    error_occurred = Signal(str)     # error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = SessionLocal()
        self._service = NotesService(self._db)
        self._current_note_id: Optional[int] = None
        self._notes_cache: List[Note] = []
    
    @property
    def current_note_id(self) -> Optional[int]:
        """Get current note ID."""
        return self._current_note_id
    
    @current_note_id.setter
    def current_note_id(self, note_id: Optional[int]):
        """Set current note ID."""
        self._current_note_id = note_id
    
    def create_note(self, title: str, content: str = "", color: str = "default", 
                   is_pinned: bool = False) -> Optional[int]:
        """Create a new note.
        
        Args:
            title: Note title
            content: Note content (markdown)
            color: Note color
            is_pinned: Whether note is pinned
            
        Returns:
            Created note ID or None on error
        """
        try:
            note_data = NoteCreate(
                title=title,
                content=content,
                color=color,
                is_pinned=is_pinned
            )
            note = self._service.create_note(note_data)
            self.note_created.emit(note.id, note.title)
            return note.id
        except Exception as e:
            error_msg = f"Failed to create note: {str(e)}"
            print(f"[NotesViewModel] {error_msg}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(error_msg)
            return None
    
    def get_note(self, note_id: int) -> Optional[Note]:
        """Get a note by ID.
        
        Args:
            note_id: Note ID
            
        Returns:
            Note object or None
        """
        try:
            return self._service.get_note(note_id)
        except Exception as e:
            self.error_occurred.emit(f"Failed to get note: {str(e)}")
            return None
    
    def list_notes(self, include_archived: bool = False, 
                  pinned_only: bool = False) -> List[Note]:
        """List all notes.
        
        Args:
            include_archived: Include archived notes
            pinned_only: Only return pinned notes
            
        Returns:
            List of Note objects
        """
        try:
            notes = self._service.list_notes(
                include_archived=include_archived,
                pinned_only=pinned_only
            )
            self._notes_cache = notes
            self.notes_loaded.emit()
            return notes
        except Exception as e:
            self.error_occurred.emit(f"Failed to list notes: {str(e)}")
            return []
    
    def update_note(self, note_id: int, **kwargs) -> bool:
        """Update a note.
        
        Args:
            note_id: Note ID
            **kwargs: Fields to update (title, content, color, is_pinned, is_archived)
            
        Returns:
            True if updated, False on error
        """
        try:
            note_data = NoteUpdate(**kwargs)
            note = self._service.update_note(note_id, note_data)
            if note:
                self.note_updated.emit(note.id, note.title)
                return True
            return False
        except Exception as e:
            self.error_occurred.emit(f"Failed to update note: {str(e)}")
            return False
    
    def delete_note(self, note_id: int) -> bool:
        """Delete a note.
        
        Args:
            note_id: Note ID
            
        Returns:
            True if deleted, False on error
        """
        try:
            if self._service.delete_note(note_id):
                self.note_deleted.emit(note_id)
                return True
            return False
        except Exception as e:
            self.error_occurred.emit(f"Failed to delete note: {str(e)}")
            return False
    
    def search_notes(self, query: str) -> List[Note]:
        """Search notes by title or content.
        
        Args:
            query: Search query
            
        Returns:
            List of matching Note objects
        """
        try:
            return self._service.search_notes(query)
        except Exception as e:
            self.error_occurred.emit(f"Search failed: {str(e)}")
            return []
    
    def toggle_pin(self, note_id: int) -> bool:
        """Toggle pin status of a note.
        
        Args:
            note_id: Note ID
            
        Returns:
            True if toggled, False on error
        """
        note = self.get_note(note_id)
        if note:
            new_pinned = not bool(note.is_pinned)
            return self.update_note(note_id, is_pinned=new_pinned)
        return False
    
    def toggle_archive(self, note_id: int) -> bool:
        """Toggle archive status of a note.
        
        Args:
            note_id: Note ID
            
        Returns:
            True if toggled, False on error
        """
        note = self.get_note(note_id)
        if note:
            new_archived = not bool(note.is_archived)
            return self.update_note(note_id, is_archived=new_archived)
        return False
    
    def get_backlinks(self, note_id: int) -> List[Note]:
        """Get all notes that link to this note.
        
        Args:
            note_id: Note ID
            
        Returns:
            List of Note objects
        """
        try:
            return self._service.get_backlinks(note_id)
        except Exception as e:
            self.error_occurred.emit(f"Failed to get backlinks: {str(e)}")
            return []
    
    def get_linked_notes(self, note_id: int) -> List[Note]:
        """Get all notes this note links to.
        
        Args:
            note_id: Note ID
            
        Returns:
            List of Note objects
        """
        try:
            return self._service.get_linked_notes(note_id)
        except Exception as e:
            self.error_occurred.emit(f"Failed to get linked notes: {str(e)}")
            return []
    
    def refresh(self):
        """Refresh the notes list."""
        self.list_notes()
    
    def __del__(self):
        """Close database session on cleanup."""
        if hasattr(self, '_db'):
            self._db.close()
