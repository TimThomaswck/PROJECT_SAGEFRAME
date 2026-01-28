"""Pydantic models for extraction output validation."""

from typing import Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class ExtractionOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    raw_text: Optional[str] = Field(default=None)
    structured_fields: Optional[Dict] = Field(default=None)
    mode: str
    provider: Optional[str] = None
    version: int = 1
