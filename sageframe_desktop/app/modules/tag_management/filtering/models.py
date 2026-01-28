"""Filter data models and operators for tag-based filtering."""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class FilterOperator(str, Enum):
    """Logical operators for combining filter rules."""
    AND = "and"
    OR = "or"


class FilterRule(BaseModel):
    """Single filter rule (e.g., 'has tag @movie')."""
    tag_name: str = Field(..., description="Tag name to filter by")
    include: bool = Field(True, description="True = must have tag, False = must NOT have tag")


class FilterGroup(BaseModel):
    """Group of filter rules with operator."""
    rules: List[FilterRule] = Field(default_factory=list)
    operator: FilterOperator = Field(FilterOperator.AND, description="How to combine rules in this group")


class TagFilter(BaseModel):
    """Complete filter with nested groups."""
    groups: List[FilterGroup] = Field(default_factory=list)
    group_operator: FilterOperator = Field(FilterOperator.OR, description="How to combine groups")
    
    def is_empty(self) -> bool:
        """Check if filter has no rules."""
        return not self.groups or all(not g.rules for g in self.groups)
