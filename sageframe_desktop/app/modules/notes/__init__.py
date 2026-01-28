"""Notes module for Google Keep-style note management."""

from app.modules.notes.models import Note, NoteLink
from app.modules.notes.services import NotesService
from app.modules.notes.view_models import NotesViewModel

__all__ = ["Note", "NoteLink", "NotesService", "NotesViewModel"]
