"""Service layer for notes management.

Handles CRUD operations and backlink management for notes.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import re

from sqlalchemy.orm import Session
from app.modules.notes.models import Note, NoteCreate, NoteUpdate, note_links


class NotesService:
    """Service for managing notes with markdown and backlink support."""
    
    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session
    
    def create_note(self, note_data: NoteCreate) -> Note:
        """Create a new note.
        
        Args:
            note_data: Note creation schema
            
        Returns:
            Created Note object
        """
        note = Note(
            title=note_data.title,
            content=note_data.content or "",
            color=note_data.color,
            is_pinned=1 if note_data.is_pinned else 0,
            is_archived=1 if note_data.is_archived else 0
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        
        # Auto-detect and create backlinks
        if note.content:
            self._auto_create_backlinks(note)
        
        return note
    
    def get_note(self, note_id: int) -> Optional[Note]:
        """Get a note by ID.
        
        Args:
            note_id: Note ID
            
        Returns:
            Note object or None
        """
        return self.db.query(Note).filter(Note.id == note_id).first()
    
    def list_notes(
        self,
        include_archived: bool = False,
        pinned_only: bool = False
    ) -> List[Note]:
        """List all notes with optional filters.
        
        Args:
            include_archived: Include archived notes
            pinned_only: Only return pinned notes
            
        Returns:
            List of Note objects
        """
        query = self.db.query(Note)
        
        if not include_archived:
            query = query.filter(Note.is_archived == 0)
        
        if pinned_only:
            query = query.filter(Note.is_pinned == 1)
        
        # Order: pinned first, then by updated date descending
        query = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc())
        
        return query.all()
    
    def update_note(self, note_id: int, note_data: NoteUpdate) -> Optional[Note]:
        """Update a note.
        
        Args:
            note_id: Note ID
            note_data: Note update schema
            
        Returns:
            Updated Note object or None
        """
        note = self.get_note(note_id)
        if not note:
            return None
        
        update_dict = note_data.model_dump(exclude_unset=True)
        
        # Convert boolean to int for SQLite
        if 'is_pinned' in update_dict:
            update_dict['is_pinned'] = 1 if update_dict['is_pinned'] else 0
        if 'is_archived' in update_dict:
            update_dict['is_archived'] = 1 if update_dict['is_archived'] else 0
        
        for key, value in update_dict.items():
            setattr(note, key, value)
        
        self.db.commit()
        self.db.refresh(note)
        
        # Update backlinks if content changed
        if 'content' in update_dict:
            self._update_backlinks(note)
        
        return note
    
    def delete_note(self, note_id: int) -> bool:
        """Delete a note.
        
        Args:
            note_id: Note ID
            
        Returns:
            True if deleted, False if not found
        """
        note = self.get_note(note_id)
        if not note:
            return False
        
        self.db.delete(note)
        self.db.commit()
        return True
    
    def search_notes(self, query: str) -> List[Note]:
        """Search notes by title or content.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching Note objects
        """
        search_pattern = f"%{query}%"
        return self.db.query(Note).filter(
            (Note.title.ilike(search_pattern)) | (Note.content.ilike(search_pattern))
        ).filter(Note.is_archived == 0).all()
    
    def get_backlinks(self, note_id: int) -> List[Note]:
        """Get all notes that link to this note.
        
        Args:
            note_id: Note ID
            
        Returns:
            List of Note objects that link to this note
        """
        note = self.get_note(note_id)
        if not note:
            return []
        
        return list(note.backlinked_from)
    
    def get_linked_notes(self, note_id: int) -> List[Note]:
        """Get all notes that this note links to.
        
        Args:
            note_id: Note ID
            
        Returns:
            List of Note objects this note links to
        """
        note = self.get_note(note_id)
        if not note:
            return []
        
        return list(note.linked_notes.all())
    
    def create_backlink(self, source_note_id: int, target_note_id: int) -> bool:
        """Create a backlink from source note to target note.
        
        Args:
            source_note_id: ID of note containing the link
            target_note_id: ID of note being linked to
            
        Returns:
            True if created, False if either note not found or link exists
        """
        source = self.get_note(source_note_id)
        target = self.get_note(target_note_id)
        
        if not source or not target or source_note_id == target_note_id:
            return False
        
        # Check if link already exists
        if target in source.linked_notes.all():
            return False
        
        source.linked_notes.append(target)
        self.db.commit()
        return True
    
    def remove_backlink(self, source_note_id: int, target_note_id: int) -> bool:
        """Remove a backlink.
        
        Args:
            source_note_id: ID of note containing the link
            target_note_id: ID of note being linked to
            
        Returns:
            True if removed, False if not found
        """
        source = self.get_note(source_note_id)
        target = self.get_note(target_note_id)
        
        if not source or not target:
            return False
        
        if target in source.linked_notes.all():
            source.linked_notes.remove(target)
            self.db.commit()
            return True
        
        return False
    
    def _auto_create_backlinks(self, note: Note):
        """Auto-detect and create backlinks based on [[Note Title]] syntax.
        
        Args:
            note: Note object to scan for backlinks
        """
        if not note.content:
            return
        
        # Find all [[Note Title]] patterns
        backlink_pattern = r'\[\[([^\]]+)\]\]'
        matches = re.findall(backlink_pattern, note.content)
        
        for title in matches:
            # Find note with matching title
            target_note = self.db.query(Note).filter(
                Note.title.ilike(title.strip())
            ).first()
            
            if target_note and target_note.id != note.id:
                # Create backlink if it doesn't exist
                if target_note not in note.linked_notes.all():
                    note.linked_notes.append(target_note)
        
        if matches:
            self.db.commit()
    
    def _update_backlinks(self, note: Note):
        """Update backlinks when note content changes.
        
        Args:
            note: Note object with updated content
        """
        # Remove all existing links
        note.linked_notes.clear()
        self.db.commit()
        
        # Re-create backlinks from current content
        self._auto_create_backlinks(note)
