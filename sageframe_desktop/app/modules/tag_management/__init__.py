"""Tag management module for smart tagging and categorization."""

from app.modules.tag_management.models import Tag, TaggedItem
from app.modules.tag_management.services import TagService
from app.modules.tag_management.parsers import TagParser

__all__ = ['Tag', 'TaggedItem', 'TagService', 'TagParser']
