# Story 3.2: Automatically Enrich Tagged Content from External Sources

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Epic Context

**Epic 3: Effortless Information Capture & Curation**

Users can quickly and easily capture various forms of information—from unstructured thoughts to structured data in bills and notes—and have it intelligently organized, enriched, and made actionable for future retrieval and task management.

This epic covers:
- Smart tagging for automatic categorization (Story 3.1 - COMPLETED)
- Automatically enrich tagged content from external sources (THIS STORY)
- Import and extract information from bills and notes (Story 3.3)
- Tags & smart filters with AND/OR logic (Story 3.4)

## Story

As a user,
I want content tagged with smart tags (e.g., `@movie`, `@book`) to be automatically enriched with relevant metadata from external sources,
so that I have more complete and useful information without manual effort.

## Acceptance Criteria

1. **Given** information containing a recognized smart tag (e.g., `@movie: Inception`) is saved (from Story 3.1),  
   **When** the system processes this tagged content,  
   **Then** it automatically queries an appropriate external source (e.g., a movie database API for `@movie` tags).

2. **Given** an external source is successfully queried,  
   **Then** relevant metadata (e.g., director, cast, release year for a movie) is retrieved and associated with the captured information.

3. **Given** the enriched metadata is available,  
   **Then** it is displayed alongside the original captured information when viewed (e.g., in a details panel or popup).

4. **Given** an external source query fails or returns no data,  
   **Then** the system gracefully handles the failure, possibly logging the error without disrupting the user experience, and does not display incomplete or incorrect enrichment.

## Business Value & Context

**Primary User Need:** Users should have rich, contextual information about tagged items automatically, without having to manually look up details.

**Why This Matters:**
- Transforms simple tags into knowledge-rich information automatically
- Reduces manual effort to add context (director, ratings, publication info, etc.)
- Makes captured information more useful and actionable
- Differentiates SageFrame from basic note-taking apps
- Aligns with "empathetic co-pilot" by proactively providing helpful context

**Related FRs:**
- FR16: Smart tags for automatic categorization and enrichment
- FR17: Automatically enrich tagged content with metadata from external sources

## Tasks / Subtasks

- [ ] Design enrichment data model (AC: #2, #3)
  - [ ] Extend tag system database schema for enrichment metadata
  - [ ] Create `tag_enrichments` table to store external metadata
  - [ ] Add migration using Alembic
  
- [ ] Implement enrichment service layer (AC: #1, #2, #4)
  - [ ] Create `EnrichmentService` class with async API calls
  - [ ] Build tag-to-API mapping system (e.g., `@movie` → TMDB API, `@book` → Google Books API)
  - [ ] Implement retry logic and error handling (per NFR8, NFR9)
  - [ ] Add caching for enrichment results (reduce API calls)
  
- [ ] Integrate external API providers (AC: #1, #2)
  - [ ] Research and select appropriate APIs (TMDB for movies, Google Books for books, etc.)
  - [ ] Implement API client wrapper classes for each provider
  - [ ] Handle API authentication (API keys storage per architecture: keyring library)
  - [ ] Parse and validate API responses (use Pydantic models)
  
- [ ] Build enrichment trigger system (AC: #1)
  - [ ] Create background worker for async enrichment processing
  - [ ] Trigger enrichment when tagged item is saved
  - [ ] Implement queue system to avoid blocking UI thread
  
- [ ] Create enrichment display UI (AC: #3)
  - [ ] Design enrichment detail panel/popup widget (Atomic Design)
  - [ ] Build metadata display components (movie poster, book cover, ratings, etc.)
  - [ ] Implement expandable/collapsible enrichment section
  
- [ ] Implement error handling and fallback (AC: #4)
  - [ ] Gracefully handle API failures (timeout, rate limits, auth errors)
  - [ ] Log errors locally for debugging
  - [ ] Show user-friendly messages when enrichment fails
  - [ ] Implement manual retry mechanism
  
- [ ] Testing and validation (AC: all)
  - [ ] Unit tests for API client wrappers
  - [ ] Integration tests for enrichment service
  - [ ] Mock external APIs for testing
  - [ ] Test error scenarios and retry logic
  - [ ] Performance tests for async processing

## Dev Notes

### Architecture Compliance

**Data Architecture:**
- Use SQLAlchemy ORM for enrichment metadata storage
- Pydantic models for API response validation
- Alembic for database migrations
- SQLite for local storage (local-first principle)

**API Integration Pattern:**
- User-provided API keys (per architecture: privacy-preserving, no backend needed)
- Async API calls (don't block UI thread per NFR1/NFR2)
- Caching strategy: Store enrichment results locally to minimize API calls
- Retry logic: Implement exponential backoff (per NFR8)

**Frontend Architecture:**
- Follow MVVM pattern with PySide6
- Use Qt Signals & Slots for enrichment status updates (e.g., `enrichmentCompleted`, `enrichmentFailed`)
- Atomic Design for enrichment display components
- Async loading indicators (per architecture: contextual loading states)

**Naming Conventions (CRITICAL):**
- Database: `snake_case` (tables: `tag_enrichments`, columns: `enrichment_data`, `api_provider`)
- Python code: PEP 8 (functions: `enrich_tag()`, classes: `EnrichmentService`)
- Signals: `verbNoun` camelCase (e.g., `enrichmentCompleted`, `enrichmentFailed`)

### Performance Requirements (NFR1, NFR2, NFR8, NFR9)

- **Enrichment must be asynchronous** - Do NOT block UI while fetching metadata
- **Show loading indicator** - User must see visual feedback during enrichment
- **Timeout for API calls** - Max 5 seconds per API request
- **Retry logic** - Exponential backoff (1s, 2s, 4s) for failed requests
- **Cache enrichment results** - Don't re-fetch data for same tag content
- **Graceful degradation** - If API fails, core functionality still works

### Project Structure Notes

Extend the `tag_management` module from Story 3.1:

```
src/modules/tag_management/
  ├── models.py         # Extended with enrichments table
  ├── services.py       # Extended with EnrichmentService
  ├── enrichment/       # NEW: Enrichment-specific code
  │   ├── __init__.py
  │   ├── api_clients.py    # API wrapper classes
  │   ├── providers.py      # Provider definitions and mapping
  │   ├── cache.py          # Enrichment caching logic
  │   └── workers.py        # Background workers for async enrichment
  ├── parsers.py        # (from Story 3.1)
  ├── views.py          # Extended with enrichment display widgets
  ├── signals.py        # Extended with enrichment signals
  └── tests/
      ├── test_enrichment_service.py
      ├── test_api_clients.py
      └── test_enrichment_cache.py
```

Also integrate with settings module for API key management (per architecture).

### External API Selection

**Recommended APIs (Free/Freemium tiers available):**

1. **@movie tags:**
   - **The Movie Database (TMDB):** https://www.themoviedb.org/documentation/api
   - Free tier: 40 requests/10 seconds
   - Data: Title, director, cast, ratings, poster, synopsis, release date

2. **@book tags:**
   - **Google Books API:** https://developers.google.com/books/docs/v1/using
   - Free tier: 1000 requests/day
   - Data: Title, author, publisher, ISBN, cover, description, ratings

3. **@restaurant tags (optional/future):**
   - **Google Places API** or **Yelp Fusion API**
   - Data: Name, address, rating, photos, hours

4. **@person tags (optional/future):**
   - **Wikipedia API** for basic biographical info
   - Free, no limits

**API Key Storage:**
- Use `keyring` library (per architecture: Windows Credential Manager)
- Fallback to encrypted .env file with restrictive permissions
- API key management UI in settings module
- Never hardcode or commit API keys to version control

### Data Model Design

**Extend `tagged_items` table (from Story 3.1):**
```sql
-- No changes needed, but ensure `content` column exists for tag-specific content
```

**NEW `tag_enrichments` table:**
```sql
id                  INTEGER PRIMARY KEY
tagged_item_id      INTEGER NOT NULL      -- FK to tagged_items.id
api_provider        TEXT NOT NULL         -- e.g., 'tmdb', 'google_books'
enrichment_data     TEXT NOT NULL         -- JSON blob of metadata
fetch_status        TEXT NOT NULL         -- 'pending', 'completed', 'failed'
error_message       TEXT                  -- Error details if failed
fetched_at          TEXT                  -- ISO 8601 UTC (when enrichment succeeded/failed)
created_at          TEXT NOT NULL         -- ISO 8601 UTC
updated_at          TEXT NOT NULL         -- ISO 8601 UTC

UNIQUE(tagged_item_id) -- One enrichment per tagged item
```

**Enrichment data JSON structure example (for `@movie: Inception`):**
```json
{
  "title": "Inception",
  "year": 2010,
  "director": "Christopher Nolan",
  "cast": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Ellen Page"],
  "rating": 8.8,
  "poster_url": "https://image.tmdb.org/...",
  "synopsis": "A thief who steals corporate secrets...",
  "genres": ["Action", "Sci-Fi", "Thriller"]
}
```

### Enrichment Workflow

**Process Flow:**
1. User saves tagged item (e.g., `@movie: Inception`) → Triggers from Story 3.1
2. `EnrichmentService` detects new tagged item with enrichable tag
3. Service queues enrichment job (async background worker)
4. Worker determines API provider based on tag type (`@movie` → TMDB)
5. Worker calls external API with tag content (`Inception`)
6. Worker parses and validates API response (Pydantic)
7. Worker stores enrichment data in `tag_enrichments` table
8. Worker emits `enrichmentCompleted` signal
9. UI updates to show enriched metadata

**Error Flow:**
1. API call fails (timeout, rate limit, auth error, no results)
2. Worker implements retry logic with exponential backoff
3. After max retries (3 attempts), mark as `failed` in database
4. Log error details to local debugging log
5. Emit `enrichmentFailed` signal
6. UI shows subtle error indicator (non-intrusive per "empathetic co-pilot")
7. Provide manual retry button in enrichment panel

### Integration with Story 3.1

**Dependencies:**
- Requires `tags` and `tagged_items` tables from Story 3.1
- Uses tag parser to extract tag type and content
- Subscribes to tag creation signals to trigger enrichment

**Coordination Points:**
- Enrichment should trigger automatically when tagged item is saved
- Don't enrich tags without content (e.g., `@movie` alone, only `@movie: Inception`)
- Handle tag updates: If user edits tag content, re-fetch enrichment

### Security & Privacy

**API Key Security:**
- Store API keys in Windows Credential Manager via `keyring` library
- Require user to provide their own API keys (privacy-preserving, no central backend)
- Validate API keys before making requests
- Provide clear UI for API key management in settings

**Privacy Considerations:**
- User data (tag content) is sent to external APIs - inform user in settings
- No personally identifiable information should be sent without user consent
- Cache enrichment results to minimize external API calls
- Provide option to disable automatic enrichment (manual trigger only)

**Rate Limiting:**
- Respect API provider rate limits (implement client-side rate limiting)
- Use caching aggressively to stay within free tier limits
- Implement queue system to avoid bursting API calls
- Provide user feedback if rate limit is reached

### Error Handling (per NFR8, NFR9)

**Retry Logic:**
- Automatic retry with exponential backoff: 1s, 2s, 4s (max 3 attempts)
- If all retries fail, mark as `failed` and log error
- Provide manual retry button in UI

**Error Scenarios:**
1. **API timeout:** Retry with longer timeout
2. **Rate limit exceeded:** Wait and retry (respect retry-after header)
3. **Authentication failure:** Prompt user to check API key in settings
4. **No results found:** Mark as completed but no enrichment (valid state)
5. **Invalid API response:** Log error, don't crash, show user-friendly message
6. **Network offline:** Gracefully fail, allow manual retry later

**Global Error Handling:**
- Integrate with architecture's global error handler
- Log all errors to local debugging log (for user/dev troubleshooting)
- Display user-friendly error dialogs (non-technical language)

### Testing Standards

**Unit Tests:**
- Mock all external API calls (don't hit real APIs during tests)
- Test API client wrappers for each provider
- Test enrichment service logic (queue, retry, error handling)
- Test Pydantic validation for API responses

**Integration Tests:**
- Test end-to-end enrichment flow (tag creation → enrichment → display)
- Use test database for integration tests
- Mock external APIs but test real database interactions

**Performance Tests:**
- Validate async processing doesn't block UI
- Test caching effectiveness (second request should be instant)
- Test queue system under high load (many tags enriched simultaneously)

**Edge Case Tests:**
- No API key configured
- Invalid API key
- API returns empty results
- API returns malformed JSON
- Network offline during enrichment

### UI/UX Considerations

**Empathetic Co-Pilot Tone:**
- Enrichment should be subtle and non-intrusive
- Don't interrupt user flow with enrichment notifications
- Use passive loading indicators (e.g., subtle spinner in tag badge)
- Only show errors if user explicitly views enrichment panel

**Enrichment Display:**
- Collapsed by default, expandable on click
- Show key metadata prominently (poster/cover, title, rating)
- Provide "Show More" to expand full details
- Include "Refresh" button for manual retry if enrichment failed

**Accessibility:**
- Alt text for images (posters, covers)
- Keyboard navigation for enrichment panel
- Screen reader support for enriched metadata

### Common LLM Mistakes to AVOID

- ❌ Don't make synchronous API calls - always use async (asyncio or threading)
- ❌ Don't block the UI thread while waiting for enrichment
- ❌ Don't expose API keys in logs, error messages, or UI
- ❌ Don't fail silently - provide user feedback for errors
- ❌ Don't re-fetch enrichment data unnecessarily - implement caching
- ❌ Don't ignore rate limits - respect API provider limits
- ❌ Don't hardcode API endpoints or provider logic - make it extensible
- ❌ Don't forget to validate external API responses with Pydantic
- ❌ Don't ignore NFR8/NFR9 - implement proper retry and manual intervention
- ❌ Don't forget to test error scenarios (timeout, auth failure, no results)

### References

- [Source: architecture.md#Data Architecture] - SQLAlchemy + Pydantic + Alembic
- [Source: architecture.md#Frontend Architecture] - MVVM + Atomic Design + Signals & Slots
- [Source: architecture.md#AI/ML Integration Architecture#API Key Security] - Keyring library for secure API key storage
- [Source: architecture.md#Process Patterns] - Global error handling and loading states
- [Source: architecture.md#Naming Patterns] - Database and code naming conventions
- [Source: epics.md#Epic 3] - Full epic context and story dependencies
- [Source: epics.md#Story 3.2 Acceptance Criteria] - Original acceptance criteria
- [Source: epics.md#NFR8, NFR9] - Integration failure handling and retry logic

### Future Enhancements (Post-MVP)

- Support more tag types (`@podcast`, `@article`, `@recipe`)
- Implement tag synonym mapping (e.g., `@film` = `@movie`)
- Add user-configurable enrichment preferences (which APIs to use)
- Implement enrichment analytics (cache hit rate, API call costs)
- Add bulk enrichment for existing tagged items
- Provide alternative API providers for same tag type (fallback options)

## Dev Agent Record

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent during implementation_

### Completion Notes List

_To be filled by dev agent with implementation learnings_

### File List

_To be filled by dev agent with all files created/modified_
