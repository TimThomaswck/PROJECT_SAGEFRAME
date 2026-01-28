# Story 3.4: Tags & Smart Filters

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Epic Context

**Epic 3: Effortless Information Capture & Curation**

Users can quickly and easily capture various forms of information—from unstructured thoughts to structured data in bills and notes—and have it intelligently organized, enriched, and made actionable for future retrieval and task management.

This epic covers:
- Smart tagging for automatic categorization (Story 3.1 - COMPLETED)
- Automatically enrich tagged content from external sources (Story 3.2 - COMPLETED)
- Import and extract information from bills and notes (Story 3.3 - COMPLETED)
- Tags & smart filters with AND/OR logic (THIS STORY - FINAL)

## Story

As a user,
I want to use tags and smart filters with AND/OR logic,
so that I can organize and find my information more effectively.

## Acceptance Criteria

1. **Given** I am creating or editing a note or task,  
   **When** I choose to add tags,  
   **Then** I can add one or more tags.

2. **Given** I am viewing my notes or tasks,  
   **When** I choose to filter,  
   **Then** I can filter them by one or more tags.

3. **Given** I am filtering,  
   **When** I apply multiple filters,  
   **Then** I can use AND/OR logic to combine them.

4. _(Note: This does not include a full rule engine, just simple filtering logic)._

## Business Value & Context

**Primary User Need:** Users need powerful yet simple filtering capabilities to find information quickly across tasks, notes, and captured items.

**Why This Matters:**
- Completes the "Effortless Information Capture & Curation" epic by making information easily retrievable
- Enables users to organize large volumes of captured information
- Supports both simple (single tag) and complex (AND/OR) filtering use cases
- Builds on tag foundation from Story 3.1
- Makes enriched content from Story 3.2 and extracted bills from Story 3.3 searchable

**Related FRs:**
- FR15: Quick-capture inbox for unstructured information (needs filtering)
- FR16: Smart tags for automatic categorization (provides tags to filter by)
- FR39: Tags and smart filters with AND/OR logic

## Tasks / Subtasks

- [ ] Extend tagging system for tasks and notes (AC: #1)
  - [ ] Add tag support to task model (if not already present from Epic 2)
  - [ ] Add tag support to note/captured items model (from Story 3.1)
  - [ ] Create tag input widget for task and note editing UIs
  - [ ] Implement tag autocomplete (suggest existing tags)
  
- [ ] Design filter query builder (AC: #2, #3)
  - [ ] Create filter data model (filter rules with AND/OR operators)
  - [ ] Implement filter query parser (convert UI input to SQL queries)
  - [ ] Build SQLAlchemy query generation for tag-based filtering
  
- [ ] Build filter UI components (AC: #2, #3)
  - [ ] Create filter panel widget (Atomic Design: organism)
  - [ ] Implement tag selector with multi-select
  - [ ] Add AND/OR operator toggle buttons
  - [ ] Show active filters and allow removal (filter chips)
  
- [ ] Implement filter execution service (AC: #2, #3)
  - [ ] Create `FilterService` for executing filter queries
  - [ ] Implement AND logic (all tags must match)
  - [ ] Implement OR logic (any tag can match)
  - [ ] Support nested AND/OR combinations (e.g., "(A AND B) OR C")
  
- [ ] Integrate filters with existing views (AC: #2)
  - [ ] Add filter panel to task list view
  - [ ] Add filter panel to notes/captured items view
  - [ ] Add filter panel to bill/document ingestion view (Story 3.3)
  - [ ] Persist filter state (remember user's last filter)
  
- [ ] Testing and validation (AC: all)
  - [ ] Unit tests for filter query builder
  - [ ] Unit tests for AND/OR logic
  - [ ] Integration tests for filtering across tasks, notes, and bills
  - [ ] UI tests for filter panel interactions
  - [ ] Performance tests for complex filters (many tags, large datasets)

## Dev Notes

### Architecture Compliance

**Data Architecture:**
- Use SQLAlchemy ORM for all tag-based queries
- Leverage existing many-to-many relationships from Story 3.1
- Create database indexes on tag columns for query performance
- Use SQLAlchemy's `and_()` and `or_()` for filter logic

**Frontend Architecture:**
- Follow MVVM pattern with PySide6
- Use Qt Signals & Slots for filter events (e.g., `filterApplied`, `filterCleared`)
- Atomic Design for filter panel (molecule: tag selector, organism: filter panel)
- Responsive UI updates when filters change (NFR1/NFR2)

**Naming Conventions (CRITICAL):**
- Database: `snake_case` (tables: `filter_presets`, columns: `filter_rules`)
- Python code: PEP 8 (functions: `apply_filter()`, classes: `FilterService`)
- Signals: `verbNoun` camelCase (e.g., `filterApplied`, `filterCleared`, `tagsUpdated`)

### Performance Requirements (NFR1, NFR2)

- **Filter application must be fast** - Target <200ms for query execution
- **UI must remain responsive** - Async filter execution if large datasets
- **Add database indexes** - Index `tag_name` column, junction table foreign keys
- **Optimize SQL queries** - Use SQLAlchemy's query optimization (eager loading, joins)
- **Cache filter results** - For frequently used filters

### Project Structure Notes

Extend the `tag_management` module from Stories 3.1-3.3:

```
src/modules/tag_management/
  ├── models.py             # (from Story 3.1) - Extended with filter models
  ├── services.py           # (from Story 3.1) - Extended with FilterService
  ├── filtering/            # NEW: Filtering-specific code
  │   ├── __init__.py
  │   ├── query_builder.py  # Build SQLAlchemy queries from filter rules
  │   ├── operators.py      # AND/OR operators and logic
  │   ├── presets.py        # Save/load filter presets (future)
  │   └── validators.py     # Validate filter rules
  ├── enrichment/           # (from Story 3.2)
  ├── views.py              # Extended with filter panel widgets
  ├── signals.py            # Extended with filter signals
  └── tests/
      ├── test_filter_query_builder.py
      ├── test_filter_operators.py
      └── test_filter_service.py
```

Also integrate with:
- `task_management` module (Epic 2) - Filter tasks by tags
- `file_ingestion` module (Story 3.3) - Filter bills/documents by tags

### Filter Data Model

**Filter Rule Structure (in-memory, can be persisted later):**
```python
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

class FilterOperator(str, Enum):
    AND = "and"
    OR = "or"

class FilterRule(BaseModel):
    """Single filter rule (e.g., 'has tag @movie')"""
    tag_name: str               # e.g., "movie", "book"
    include: bool = True        # True = must have tag, False = must NOT have tag

class FilterGroup(BaseModel):
    """Group of filter rules with operator"""
    rules: List[FilterRule]
    operator: FilterOperator = FilterOperator.AND

class Filter(BaseModel):
    """Complete filter with nested groups"""
    groups: List[FilterGroup]
    group_operator: FilterOperator = FilterOperator.OR  # How to combine groups
```

**Example Filter (Complex):**
```
Show items that:
  (have @movie AND have @watched) OR (have @book AND have @fiction)

Filter representation:
{
  "groups": [
    {
      "rules": [
        {"tag_name": "movie", "include": true},
        {"tag_name": "watched", "include": true}
      ],
      "operator": "and"
    },
    {
      "rules": [
        {"tag_name": "book", "include": true},
        {"tag_name": "fiction", "include": true}
      ],
      "operator": "and"
    }
  ],
  "group_operator": "or"
}
```

### Filter Query Builder

**SQLAlchemy Query Construction:**

```python
from sqlalchemy import and_, or_, exists
from sqlalchemy.orm import Session

class FilterQueryBuilder:
    """Build SQLAlchemy queries from filter rules."""
    
    def build_query(self, session: Session, base_query, filter: Filter):
        """Apply filter to existing query."""
        if not filter.groups:
            return base_query  # No filter, return all
        
        # Build subqueries for each group
        group_conditions = []
        for group in filter.groups:
            if group.operator == FilterOperator.AND:
                # All tags in group must match
                condition = self._build_and_condition(group.rules)
            else:  # OR
                # Any tag in group can match
                condition = self._build_or_condition(group.rules)
            group_conditions.append(condition)
        
        # Combine groups with group_operator
        if filter.group_operator == FilterOperator.AND:
            final_condition = and_(*group_conditions)
        else:  # OR
            final_condition = or_(*group_conditions)
        
        return base_query.filter(final_condition)
    
    def _build_and_condition(self, rules: List[FilterRule]):
        """Build AND condition for rules (all tags must match)."""
        conditions = []
        for rule in rules:
            # Check if item has this tag
            condition = exists().where(
                and_(
                    TaggedItem.item_id == Item.id,
                    Tag.id == TaggedItem.tag_id,
                    Tag.tag_name == rule.tag_name
                )
            )
            if not rule.include:
                condition = ~condition  # Negate for exclusion
            conditions.append(condition)
        return and_(*conditions)
    
    def _build_or_condition(self, rules: List[FilterRule]):
        """Build OR condition for rules (any tag can match)."""
        conditions = []
        for rule in rules:
            condition = exists().where(
                and_(
                    TaggedItem.item_id == Item.id,
                    Tag.id == TaggedItem.tag_id,
                    Tag.tag_name == rule.tag_name
                )
            )
            if not rule.include:
                condition = ~condition
            conditions.append(condition)
        return or_(*conditions)
```

### Filter UI Design

**Filter Panel Components:**

1. **Tag Selector (Molecule):**
   - Multi-select dropdown or tag chips
   - Autocomplete from existing tags
   - Visual indicator for selected tags

2. **Operator Toggle (Atom):**
   - Simple button toggle: "AND" / "OR"
   - Clear visual state (highlighted when active)

3. **Active Filter Chips (Molecule):**
   - Show currently applied filters as removable chips
   - Click chip to remove that filter rule
   - "Clear All" button to reset filters

4. **Filter Panel (Organism):**
   - Combines above components
   - Collapsible/expandable (don't clutter UI)
   - "Apply Filter" button (or auto-apply on change)
   - "Save Filter" button (for future filter presets)

**Visual Mockup (Text Representation):**
```
┌─────────────────────────────────────────┐
│ 🔍 Filter Tasks                         │
├─────────────────────────────────────────┤
│ Select Tags: [🏷️ @movie ▼] [ AND | OR ]│
│                                          │
│ Active Filters:                          │
│  [@movie ✕] AND [@watched ✕] [Clear All]│
│                                          │
│ [Apply Filter]   [Save Filter]          │
└─────────────────────────────────────────┘
```

### Integration with Existing Modules

**Task Management (Epic 2):**
- Add tag support to `Task` model (many-to-many with `tags` table)
- Integrate filter panel into task list view
- Filter tasks by tags (e.g., show all `@urgent` tasks)

**File Ingestion (Story 3.3):**
- Bills/documents already have tags from extraction
- Filter bills by tags (e.g., show all `@bill` or `@invoice`)
- Combine with date filters (e.g., bills from last month with tag `@utilities`)

**Captured Items (Story 3.1):**
- Quick-capture inbox items have tags
- Filter by tags to find specific notes/thoughts
- Combine with search (e.g., filter by `@idea` and search for "project")

### Database Optimization

**Required Indexes:**
```sql
-- Index on tag_name for fast tag lookups
CREATE INDEX idx_tags_tag_name ON tags(tag_name);

-- Index on junction table foreign keys for fast joins
CREATE INDEX idx_tagged_items_tag_id ON tagged_items(tag_id);
CREATE INDEX idx_tagged_items_item_id ON tagged_items(item_id);

-- Composite index for common query patterns
CREATE INDEX idx_tagged_items_tag_item ON tagged_items(tag_id, item_id);
```

**Query Optimization:**
- Use SQLAlchemy's `joinedload()` for eager loading
- Avoid N+1 queries when loading tags for multiple items
- Use `exists()` subqueries for efficient filtering

### Filter Presets (Future Enhancement)

**Database Model (for saving filters):**
```sql
CREATE TABLE filter_presets (
    id              INTEGER PRIMARY KEY,
    preset_name     TEXT NOT NULL UNIQUE,
    filter_rules    TEXT NOT NULL,    -- JSON blob of Filter model
    is_default      INTEGER DEFAULT 0, -- Boolean: is this the default filter?
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
```

**Usage:**
- Save frequently used filters as presets
- Quick access dropdown: "My Filters" → "Watched Movies", "Urgent Tasks"
- Share presets between devices (via cloud sync, future story)

### Error Handling

**Invalid Filter Rules:**
- Non-existent tag names → Filter returns empty results (valid state)
- Malformed filter rules → Validate with Pydantic before applying
- Query execution errors → Log error, show user-friendly message

**Performance Issues:**
- Very complex filters (>10 tags) → Warn user, suggest simplifying
- Large datasets (>10k items) → Use pagination, async loading
- Timeout queries (>5s) → Cancel query, suggest narrower filter

**Global Error Handling:**
- Integrate with architecture's global error handler
- Log filter errors to local debugging log
- Display user-friendly error dialogs

### Testing Standards

**Unit Tests:**
- Test filter query builder for AND logic
- Test filter query builder for OR logic
- Test nested AND/OR combinations
- Test tag inclusion and exclusion
- Test edge cases (empty filter, non-existent tags)

**Integration Tests:**
- Test filtering tasks by tags (end-to-end)
- Test filtering notes by tags
- Test filtering bills by tags
- Test filter persistence (save/load filter state)

**Performance Tests:**
- Benchmark query execution time (target <200ms)
- Test with large datasets (1000+ items, 50+ tags)
- Test complex filters (multiple groups, nested operators)

**UI Tests:**
- Test filter panel interactions (select tags, toggle operators)
- Test active filter chips (remove individual filters, clear all)
- Test filter application (results update correctly)

### Security & Privacy

**No External Dependencies:**
- All filtering happens locally (no external API calls)
- User data stays on device (local-first per NFR3)

**Query Injection Prevention:**
- Use SQLAlchemy's parameterized queries (prevents SQL injection)
- Validate filter rules with Pydantic before building queries
- Sanitize tag names (no special SQL characters)

### UI/UX Considerations

**Empathetic Co-Pilot Tone:**
- Filters should feel empowering, not overwhelming
- Start with simple single-tag filters, introduce AND/OR gradually
- Provide helpful suggestions ("Try filtering by @urgent to see high-priority tasks")

**Discoverability:**
- Make filter panel easily accessible (toolbar button, keyboard shortcut)
- Show sample filters as suggestions for new users
- Provide visual feedback when filter is active (e.g., highlighted filter icon)

**Performance Perception:**
- Show loading indicator for complex filters
- Debounce filter input (wait 300ms after user stops typing before applying)
- Show result count ("Showing 12 items with @movie")

**Accessibility:**
- Keyboard navigation for filter panel (tab through inputs, Enter to apply)
- Screen reader support for filter status
- High contrast for active filters

### Common LLM Mistakes to AVOID

- ❌ Don't use string concatenation for SQL queries - always use SQLAlchemy
- ❌ Don't forget to create database indexes for tag columns
- ❌ Don't make filter queries synchronous if they might be slow - use async for large datasets
- ❌ Don't forget to validate filter rules before applying (use Pydantic)
- ❌ Don't implement a full rule engine - keep it simple (AND/OR only)
- ❌ Don't forget to test filter edge cases (empty filters, non-existent tags)
- ❌ Don't ignore performance - optimize queries with indexes and eager loading
- ❌ Don't make the filter UI complex - start simple, add complexity gradually
- ❌ Don't forget to integrate with all tagged entities (tasks, notes, bills)

### References

- [Source: architecture.md#Data Architecture] - SQLAlchemy ORM usage, indexing strategies
- [Source: architecture.md#Frontend Architecture] - MVVM + Atomic Design + Signals & Slots
- [Source: architecture.md#Naming Patterns] - Database and code naming conventions
- [Source: architecture.md#Process Patterns] - Global error handling and loading states
- [Source: epics.md#Epic 3] - Full epic context
- [Source: epics.md#Story 3.4 Acceptance Criteria] - Original acceptance criteria
- [Source: epics.md#Story 3.1] - Tag data model foundation
- [Source: epics.md#NFR1, NFR2] - Performance requirements (<200ms for queries)

### Future Enhancements (Post-MVP)

- Saved filter presets
- Filter by date ranges (e.g., bills from last month)
- Filter by enrichment metadata (e.g., movies with rating > 8)
- Filter by extraction confidence (e.g., bills with high extraction confidence)
- Combine filters with full-text search (e.g., filter by `@movie` AND search for "Nolan")
- Filter analytics (most used tags, most common filter combinations)
- Smart filter suggestions based on user's tagging patterns

## Dev Agent Record

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent during implementation_

### Completion Notes List

_To be filled by dev agent with implementation learnings_

### File List

_To be filled by dev agent with all files created/modified_
