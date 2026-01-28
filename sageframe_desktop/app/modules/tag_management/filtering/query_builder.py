"""Query builder for tag-based filtering with AND/OR logic."""

from typing import Any
from sqlalchemy import and_, or_, exists, select
from sqlalchemy.orm import Query

from app.modules.tag_management.models import Tag, TaggedItem
from app.modules.tag_management.filtering.models import TagFilter, FilterOperator, FilterRule


class FilterQueryBuilder:
    """Build SQLAlchemy queries from filter rules."""
    
    def apply_filter(self, base_query: Query, tag_filter: TagFilter, item_model: Any) -> Query:
        """Apply filter to existing query.
        
        Args:
            base_query: Base SQLAlchemy query to filter
            tag_filter: Filter configuration
            item_model: The model being filtered (Task, ImportedFile, etc.)
            
        Returns:
            Filtered query
        """
        if tag_filter.is_empty():
            return base_query
        
        # Build conditions for each group
        group_conditions = []
        for group in tag_filter.groups:
            if not group.rules:
                continue
                
            if group.operator == FilterOperator.AND:
                condition = self._build_and_condition(group.rules, item_model)
            else:  # OR
                condition = self._build_or_condition(group.rules, item_model)
            
            group_conditions.append(condition)
        
        if not group_conditions:
            return base_query
        
        # Combine groups with group_operator
        if tag_filter.group_operator == FilterOperator.AND:
            final_condition = and_(*group_conditions)
        else:  # OR
            final_condition = or_(*group_conditions)
        
        return base_query.filter(final_condition)
    
    def _build_and_condition(self, rules: list[FilterRule], item_model: Any):
        """Build AND condition for rules (all tags must match)."""
        conditions = []
        for rule in rules:
            condition = self._build_tag_exists(rule.tag_name, item_model)
            if not rule.include:
                condition = ~condition  # Negate for exclusion
            conditions.append(condition)
        return and_(*conditions)
    
    def _build_or_condition(self, rules: list[FilterRule], item_model: Any):
        """Build OR condition for rules (any tag can match)."""
        conditions = []
        for rule in rules:
            condition = self._build_tag_exists(rule.tag_name, item_model)
            if not rule.include:
                condition = ~condition
            conditions.append(condition)
        return or_(*conditions)
    
    def _build_tag_exists(self, tag_name: str, item_model: Any):
        """Build EXISTS subquery for tag matching."""
        return exists(
            select(1).where(
                and_(
                    TaggedItem.item_id == item_model.id,
                    TaggedItem.tag_id == Tag.id,
                    Tag.tag_name == tag_name.lower().strip()
                )
            )
        )
