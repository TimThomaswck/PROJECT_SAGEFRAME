"""Data models for notes functionality.

This module defines SQLAlchemy ORM models and Pydantic schemas for notes.
Supports markdown content and backlinks between notes.
"""

from typing import Optional, List
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

# Constants
MAX_TITLE_LENGTH = 1000  # Increased from 255 to accommodate extracted document titles
MAX_COLOR_LENGTH = 20

# Association table for note backlinks (many-to-many)
note_links = Table(
    'note_links',
    Base.metadata,
    Column('source_note_id', Integer, ForeignKey('notes.id', ondelete='CASCADE'), primary_key=True),
    Column('target_note_id', Integer, ForeignKey('notes.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime(timezone=True), nullable=False, default=func.now())
)


class NoteColor(str, Enum):
    """Predefined color options for notes (Google Keep style)."""
    DEFAULT = "default"     # White/light
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    TEAL = "teal"
    BLUE = "blue"
    PURPLE = "purple"
    PINK = "pink"
    BROWN = "brown"
    GRAY = "gray"


class Note(Base):
    """SQLAlchemy model for notes.
    
    Stores note content in markdown format and supports backlinks to other notes.
    """
    
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(MAX_TITLE_LENGTH), nullable=False)  # Increased to accommodate extracted content
    content = Column(Text, nullable=True)  # Markdown content - unlimited
    color = Column(String(MAX_COLOR_LENGTH), nullable=False, default='default')
    is_pinned = Column(Integer, nullable=False, default=0)  # SQLite doesn't have boolean
    is_archived = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Backlinks: notes that this note links to
    linked_notes = relationship(
        'Note',
        secondary=note_links,
        primaryjoin=id == note_links.c.source_note_id,
        secondaryjoin=id == note_links.c.target_note_id,
        backref='backlinked_from',
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}', pinned={self.is_pinned})>"


# Pydantic Schemas

class NoteBase(BaseModel):
    """Base note schema with common fields."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    title: str = Field(..., max_length=MAX_TITLE_LENGTH)
    content: Optional[str] = Field(None)  # No limit - can be very long markdown
    color: str = Field(default='default', max_length=MAX_COLOR_LENGTH)
    is_pinned: bool = False
    is_archived: bool = False


class NoteCreate(NoteBase):
    """Schema for creating a new note."""
    pass


class NoteUpdate(BaseModel):
    """Schema for updating a note."""
    title: Optional[str] = Field(None, max_length=MAX_TITLE_LENGTH)
    content: Optional[str] = Field(None)  # No limit
    color: Optional[str] = Field(None, max_length=MAX_COLOR_LENGTH)
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None


class NoteRead(NoteBase):
    """Schema for reading a note with all fields."""
    id: int
    created_at: datetime
    updated_at: datetime
    linked_note_ids: List[int] = []
    
    model_config = ConfigDict(from_attributes=True)


class NoteLink(BaseModel):
    """Schema for creating a backlink between notes."""
    source_note_id: int
    target_note_id: int
