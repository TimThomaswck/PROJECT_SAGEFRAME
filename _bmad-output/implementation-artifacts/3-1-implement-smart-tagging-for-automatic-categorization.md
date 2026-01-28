# Story 3.1: Implement Smart Tagging for Automatic Categorization

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Epic Context

**Epic 3: Effortless Information Capture & Curation**

Users can quickly and easily capture various forms of information—from unstructured thoughts to structured data in bills and notes—and have it intelligently organized, enriched, and made actionable for future retrieval and task management.

This epic covers:
- Smart tagging for automatic categorization (THIS STORY)
- Automatically enrich tagged content from external sources (Story 3.2)
- Import and extract information from bills and notes (Story 3.3)
- Tags & smart filters with AND/OR logic (Story 3.4)

## Story

As a user,
I want to use smart tags (e.g., `@movie`, `@book`) when capturing information,
so that my content is automatically categorized and easily retrievable.

## Acceptance Criteria

1. **Given** I am capturing information (e.g., in the quick-capture inbox),  
   **When** I type a predefined smart tag format (e.g., `@tag: content` or just `@tag`),  
   **Then** the system recognizes and highlights the smart tag.

2. **Given** information containing smart tags is saved,  
   **When** I later view or search my captured information,  
   **Then** the smart tags facilitate filtering, categorization, or searching for content associated with that tag.

3. **Given** a smart tag is recognized,  
   **Then** the system stores the tag and its associated content in a structured way that supports later enrichment (Story 3.2).

4. **Given** I am entering smart tags,  
   **Then** the input experience is responsive and fluid (NFR1: <100ms visual feedback, NFR2: <200ms UI transitions).

## Business Value & Context

**Primary User Need:** Users need a fast, frictionless way to categorize unstructured information while capturing it, without breaking their flow or manually selecting categories.

**Why This Matters:**
- Enables the foundation for Story 3.2 (automatic enrichment from external sources)
- Makes later retrieval and filtering possible (Story 3.4: smart filters)
- Aligns with the "empathetic co-pilot" experience - the system learns from user tagging patterns
- Reduces cognitive load during capture moments

**Related FRs:**
- FR15: Quick-capture inbox for unstructured information
- FR16: Smart tags for automatic categorization and enrichment
- FR39: Tags and smart filters with AND/OR logic

## Tasks / Subtasks

- [ ] Implement tag recognition system (AC: #1, #3)
  - [ ] Create tag parser to detect `@tag` and `@tag: content` patterns
  - [ ] Create syntax highlighter for PySide6 text input widgets
  - [ ] Implement real-time tag detection as user types (<100ms feedback per NFR1)
  
- [ ] Design and implement tag data model (AC: #2, #3)
  - [ ] Create SQLAlchemy models for `tags` and `tagged_items` tables
  - [ ] Implement many-to-many relationship between tags and captured information
  - [ ] Add migration script using Alembic
  
- [ ] Build tag storage and retrieval service (AC: #2, #3)
  - [ ] Implement service layer for tag CRUD operations
  - [ ] Create methods for associating tags with captured items
  - [ ] Implement tag-based search and filtering functionality
  
- [ ] Create tag UI components (AC: #1, #4)
  - [ ] Build tag input widget with real-time highlighting
  - [ ] Create tag display/badge components (Atomic Design: atoms)
  - [ ] Implement tag autocomplete/suggestion system
  
- [ ] Implement tag categorization logic (AC: #2)
  - [ ] Create categorization service that groups items by tags
  - [ ] Implement tag-based filtering for quick-capture inbox view
  
- [ ] Testing and performance validation (AC: #4)
  - [ ] Unit tests for tag parser and recognition
  - [ ] Integration tests for tag storage and retrieval
  - [ ] Performance tests to ensure <100ms visual feedback
  - [ ] UI tests for tag highlighting and display

## Dev Notes

### Architecture Compliance

**Data Architecture:**
- Use SQLAlchemy ORM for all database interactions
- Implement Pydantic models for data validation at service layer
- Use Alembic for database migrations
- SQLite as local database (per architecture: local-first)

**Frontend Architecture:**
- Follow MVVM pattern with PySide6
- Apply Atomic Design principles for tag UI components
- Use Qt Signals & Slots for event communication (naming: `verbNoun` e.g., `tagRecognized`, `tagCreated`)
- Implement tag highlighting with QSyntaxHighlighter or similar Qt mechanisms

**Naming Conventions (CRITICAL):**
- Database: `snake_case` (table: `tags`, columns: `tag_name`, `created_at`, etc.)
- Python code: PEP 8 (functions: `parse_tags()`, classes: `TagParser`)
- API endpoints (if needed): plural nouns `/tags`, parameters: `snake_case`
- Signals: `verbNoun` camelCase (e.g., `tagCreated`, `tagDeleted`)

### Performance Requirements (NFR1, NFR2)

- **Tag recognition must be <100ms** - Use regex-based parsing, not external API calls
- **UI highlighting must be instant** - Implement using Qt's native QSyntaxHighlighter
- **Tag storage must be async** - Don't block UI thread when saving tags
- **Search/filtering must be <200ms** - Use SQLite indexes on `tag_name` column

### Project Structure Notes

Based on architecture, organize by feature. Create a new `tag_management` module:

```
src/modules/tag_management/
  ├── models.py         # SQLAlchemy models for tags
  ├── services.py       # Tag CRUD and categorization logic
  ├── parsers.py        # Tag parsing and recognition
  ├── views.py          # PySide6 widgets for tag input/display
  ├── signals.py        # Tag-related signals definitions
  └── tests/
      ├── test_models.py
      ├── test_services.py
      ├── test_parsers.py
      └── test_views.py
```

Integrate with existing quick-capture module (if it exists from Epic 1) or create it now.

### Smart Tag Format Specification

Support these patterns:
1. **Simple tag:** `@movie` - Tag with no content, just categorization
2. **Tag with content:** `@movie: Inception` - Tag with associated entity/title
3. **Tags in context:** `Watched @movie: Inception last night, amazing!` - Tags within free-form text

**Parser Requirements:**
- Must handle multiple tags in single input
- Case-insensitive tag detection (e.g., `@Movie` = `@movie`)
- Trim whitespace around tag names
- Support basic alphanumeric tags (no special characters except hyphens/underscores)

### Data Model Design

**`tags` table:**
```sql
id              INTEGER PRIMARY KEY
tag_name        TEXT NOT NULL UNIQUE  -- e.g., 'movie', 'book'
category        TEXT                  -- optional grouping (for future use)
created_at      TEXT NOT NULL         -- ISO 8601 UTC
```

**`tagged_items` table (junction table):**
```sql
id              INTEGER PRIMARY KEY
tag_id          INTEGER NOT NULL      -- FK to tags.id
item_id         INTEGER NOT NULL      -- FK to captured_items.id (or similar)
content         TEXT                  -- optional tag-specific content (e.g., "Inception")
created_at      TEXT NOT NULL         -- ISO 8601 UTC

UNIQUE(tag_id, item_id)
```

**Note:** The `item_id` will reference whatever table stores quick-capture inbox items. If that table doesn't exist, this story may need to create it or depend on another story.

### Integration with Future Stories

**Story 3.2 Preparation (Enrichment):**
- Store tag content (`@movie: Inception`) in `tagged_items.content` column
- This will be used by Story 3.2 to query external APIs (movie database, book database, etc.)

**Story 3.4 Preparation (Smart Filters):**
- Implement efficient tag-based query methods in service layer
- Create indexes to support AND/OR filtering operations

### Error Handling

- Global error handler for database errors (per architecture)
- User-friendly messages if tag parsing fails (shouldn't happen with robust regex)
- Graceful handling of duplicate tags (use UNIQUE constraint, catch errors)

### Testing Standards

- Use `pytest` for all tests
- Follow architecture: separate unit tests for each module
- Integration tests for tag-to-database round-trip
- Performance tests must validate NFR1/NFR2 compliance
- Mock database for unit tests, use test database for integration tests

### Security & Privacy

- Local-first storage (all tags stored in local SQLite database)
- No external API calls in this story (enrichment is Story 3.2)
- User data isolation per NFR3

### References

- [Source: architecture.md#Data Architecture] - SQLAlchemy + Alembic usage
- [Source: architecture.md#Frontend Architecture] - MVVM + Atomic Design
- [Source: architecture.md#Naming Patterns] - Database and code naming conventions
- [Source: architecture.md#Process Patterns] - Global error handling and loading states
- [Source: epics.md#Epic 3] - Full epic context and story dependencies
- [Source: epics.md#Story 3.1 Acceptance Criteria] - Original acceptance criteria
- [Source: epics.md#Additional Requirements] - PEP 8 compliance, Python-only stack

### Key Implementation Considerations

**UI/UX Considerations:**
- Tag highlighting color scheme should match the minimalist aesthetic
- Use subtle, non-intrusive visual indicators (consistent with "empathetic co-pilot" tone)
- Consider accessibility (high contrast, keyboard navigation)

**Future-Proofing:**
- Design tag system to be extensible for future tag types
- Consider tag synonyms (e.g., `@film` = `@movie`) in future iterations
- Leave hooks for tag analytics and learning user patterns

**Common LLM Mistakes to AVOID:**
- ❌ Don't reinvent tag parsing - use Python's built-in `re` module
- ❌ Don't create separate tables for each tag type - use a polymorphic approach
- ❌ Don't block the UI thread with database writes - use async patterns
- ❌ Don't forget to create database indexes for performance
- ❌ Don't ignore the MVVM pattern - separate UI logic from business logic
- ❌ Don't use external libraries for simple regex parsing
- ❌ Don't forget Alembic migrations for schema changes

## Dev Agent Record

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent during implementation_

### Completion Notes List

_To be filled by dev agent with implementation learnings_

### File List

_To be filled by dev agent with all files created/modified_
