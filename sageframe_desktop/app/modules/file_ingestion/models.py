"""SQLAlchemy models for file ingestion and extraction results."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class ImportedFile(Base):
    __tablename__ = "imported_files"

    id = Column(Integer, primary_key=True)
    original_path = Column(Text, nullable=False)
    stored_path = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(64), nullable=False)
    ingest_uuid = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship to extraction results
    extraction_results = relationship("ExtractionResult", back_populates="imported_file", cascade="all, delete-orphan")


class ExtractionResult(Base):
    __tablename__ = "extraction_results"

    id = Column(Integer, primary_key=True)
    imported_file_id = Column(Integer, ForeignKey("imported_files.id"), nullable=False)

    # Raw text extracted from the document
    raw_text = Column(Text, nullable=True)

    # Structured fields as JSON (e.g., {"amount": 123.45, "due_date": "2026-02-10"})
    structured_fields = Column(JSON, nullable=True)

    # Extraction metadata
    mode = Column(String(32), nullable=False)  # "pdf_text" | "ocr_bill" | "ocr_note" | "ocr_generic"
    provider = Column(String(64), nullable=True)  # e.g., "azure_invoice", "openai_vision", "google_vision"
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Backref
    imported_file = relationship("ImportedFile", back_populates="extraction_results")
