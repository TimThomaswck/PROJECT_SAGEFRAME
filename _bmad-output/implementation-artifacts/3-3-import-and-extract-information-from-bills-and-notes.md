# Story 3.3: Import and Extract Information from Bills and Notes

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Epic Context

**Epic 3: Effortless Information Capture & Curation**

Users can quickly and easily capture various forms of information—from unstructured thoughts to structured data in bills and notes—and have it intelligently organized, enriched, and made actionable for future retrieval and task management.

This epic covers:
- Smart tagging for automatic categorization (Story 3.1 - COMPLETED)
- Automatically enrich tagged content from external sources (Story 3.2 - COMPLETED)
- Import and extract information from bills and notes (THIS STORY)
- Tags & smart filters with AND/OR logic (Story 3.4)

## Story

As a user,
I can import a bill or note (image/PDF) and have SageFrame extract key info and store it, with one-click actions to create tasks.

## Acceptance Criteria

1. **Given** the user is in the application,  
   **When** they initiate file import via drag/drop or a file picker,  
   **Then** the import works for supported file types (.png, .jpg, .pdf).

2. **Given** a file is imported,  
   **When** the import is complete,  
   **Then** the original file is stored locally (e.g., under `data/ingest/<uuid>/original.ext`) and is viewable later.

3. **Given** a file is imported,  
   **When** the extraction process runs,  
   **Then** it does not freeze the UI (runs in a separate thread/asynchronously).

4. **Given** a PDF with selectable text is imported,  
   **When** the extraction runs,  
   **Then** the text is extracted locally without an API call.

5. **Given** an image-based file or PDF without selectable text is imported,  
   **When** the extraction runs,  
   **Then** an external API is used for OCR and data extraction, returning structured JSON.

6. **Given** the extraction is complete,  
   **When** the results are displayed,  
   **Then** the extracted information is shown to the user and is editable.

7. **Given** the extracted information is displayed,  
   **When** the user clicks the \"Create task\" action,  
   **Then** a new task is created using the extracted information.

8. **Given** the user re-runs extraction on the same file,  
   **When** the extraction completes,  
   **Then** it overwrites or versions the previous results, avoiding duplication.

## Business Value & Context

**Primary User Need:** Users need to quickly capture information from physical or digital documents (bills, receipts, handwritten notes, images) without manual data entry.

**Why This Matters:**
- Eliminates tedious manual data entry from bills, receipts, and notes
- Enables seamless transition from analog to digital workflows
- Creates actionable tasks from extracted information (e.g., "Pay electric bill by July 15")
- Supports the "effortless information capture" goal of Epic 3
- Provides foundation for future AI-powered insights from document patterns

**Related FRs:**
- FR18: Import bills or notes (image/PDF) into the application
- FR19: Extract key information (raw text, entities, suggested tasks) from imported files
- FR30: One-click actions on extracted information (e.g., create task)

## Tasks / Subtasks

- [ ] Implement file import UI (AC: #1)
  - [ ] Create drag-and-drop zone widget (PySide6)
  - [ ] Implement file picker dialog for manual selection
  - [ ] Add file type validation (.png, .jpg, .pdf)
  - [ ] Create import button and visual feedback (loading states)
  
- [ ] Build file storage system (AC: #2)
  - [ ] Design local file storage structure (`data/ingest/<uuid>/`)
  - [ ] Implement file storage service (copy imported file to local storage)
  - [ ] Create database model for imported files (`imported_files` table)
  - [ ] Add file viewer widget for displaying original file
  
- [ ] Implement PDF text extraction (AC: #4)
  - [ ] Integrate PDF library (e.g., PyPDF2, pdfplumber) for local text extraction
  - [ ] Detect if PDF has selectable text
  - [ ] Extract text from text-based PDFs locally (no API call)
  
- [ ] Implement image/OCR extraction (AC: #5)
  - [ ] Integrate external OCR APIs per architecture (Azure Invoice, OpenAI Vision, Google Cloud Vision)
  - [ ] Implement extraction mode selection ("Bill/Invoice" vs "Note/Image")
  - [ ] Build API client wrappers for each provider
  - [ ] Parse and validate API responses (enforce JSON schema)
  
- [ ] Build async extraction pipeline (AC: #3, #5, #8)
  - [ ] Create async extraction worker (background thread)
  - [ ] Implement extraction queue system (don't block UI)
  - [ ] Add progress indicators (loading states)
  - [ ] Handle extraction versioning (overwrite vs. keep history)
  
- [ ] Create extraction results data model (AC: #6)
  - [ ] Design `extraction_results` table for storing extracted data
  - [ ] Create Pydantic models for structured extraction output
  - [ ] Implement JSON schema validation for API responses
  
- [ ] Build extraction results UI (AC: #6, #7)
  - [ ] Create extraction results display widget (editable fields)
  - [ ] Implement "Create Task" button with one-click task creation
  - [ ] Show raw text and structured fields separately
  - [ ] Add manual editing capability for extracted data
  
- [ ] Testing and validation (AC: all)
  - [ ] Unit tests for file storage service
  - [ ] Unit tests for PDF text extraction
  - [ ] Integration tests for full import-extract-display flow
  - [ ] Mock external APIs for testing
  - [ ] Test async processing and UI responsiveness
  - [ ] Edge case tests (corrupted files, unsupported formats, API failures)

## Dev Notes

### Architecture Compliance

**Data Architecture:**
- SQLAlchemy ORM for database interactions
- Pydantic models for extraction result validation
- Alembic for database migrations
- SQLite for local storage (local-first)

**File Ingestion Architecture (from architecture.md):**
Per architecture document section "File Ingestion and Extraction Pipeline":

1. User drops file (image/PDF) into app
2. Original file stored locally for recoverability
3. Extraction step runs asynchronously
4. Extracted output (text + structured fields) saved
5. User offered actions (e.g., "create task")

**Extraction Strategy (from architecture.md):**
- **If PDF has selectable text:** Extract locally (no API call)
- **Else (image or image-based PDF):** Use external APIs

**API Choices (from architecture.md):**
- **"Bill/Invoice" mode:** Azure Invoice Model for specialized extraction
- **"Note/Image" mode:** OpenAI Vision for general-purpose extraction
- **General OCR:** Google Cloud Vision OCR as fallback

**Schema Discipline:**
- Enforce strict JSON schema for all API outputs
- Validate schema before saving to database (prevent data corruption)

**Frontend Architecture:**
- Follow MVVM pattern with PySide6
- Use Qt Signals & Slots for extraction events (e.g., `extractionCompleted`, `extractionFailed`)
- Atomic Design for file import and results display components
- Async loading states (per architecture: contextual loading indicators)

**Naming Conventions (CRITICAL):**
- Database: `snake_case` (tables: `imported_files`, `extraction_results`, columns: `file_path`, `extraction_data`)
- Python code: PEP 8 (functions: `extract_from_pdf()`, classes: `FileImportService`)
- Signals: `verbNoun` camelCase (e.g., `fileImported`, `extractionCompleted`, `taskCreated`)

### Performance Requirements (NFR1, NFR2, NFR3)

- **File import must not block UI** - Use async file I/O or background thread
- **Extraction must be asynchronous** - Show loading indicator, don't freeze UI
- **Visual feedback <100ms** - Show import confirmation immediately
- **File storage must be secure** - Use OS-level permissions, isolate from other apps (NFR3)
- **Large file handling** - Support PDFs/images up to 10MB without performance degradation

### Project Structure Notes

Create new module for file ingestion:

```
src/modules/file_ingestion/
  ├── __init__.py
  ├── models.py             # SQLAlchemy models for imported_files, extraction_results
  ├── services.py           # FileImportService, ExtractionService
  ├── storage.py            # File storage logic (copy to data/ingest/<uuid>/)
  ├── extraction/
  │   ├── __init__.py
  │   ├── pdf_extractor.py      # Local PDF text extraction (PyPDF2/pdfplumber)
  │   ├── ocr_clients.py        # API clients for Azure, OpenAI, Google Vision
  │   ├── schemas.py            # Pydantic models for extraction output validation
  │   └── workers.py            # Async extraction workers
  ├── views.py              # PySide6 widgets for drag-drop, file viewer, results display
  ├── signals.py            # File ingestion signals
  └── tests/
      ├── test_file_import.py
      ├── test_pdf_extractor.py
      ├── test_ocr_clients.py
      └── test_extraction_service.py
```

Integrate with existing `task_management` module for "Create Task" functionality.

### Data Model Design

**`imported_files` table:**
```sql
id                  INTEGER PRIMARY KEY
file_uuid           TEXT NOT NULL UNIQUE  -- UUID for storage path
original_filename   TEXT NOT NULL         -- User's original filename
file_type           TEXT NOT NULL         -- 'pdf', 'png', 'jpg'
file_path           TEXT NOT NULL         -- Relative path: data/ingest/<uuid>/original.ext
file_size_bytes     INTEGER NOT NULL
import_mode         TEXT NOT NULL         -- 'bill_invoice' or 'note_image'
import_source       TEXT NOT NULL         -- 'drag_drop' or 'file_picker'
imported_at         TEXT NOT NULL         -- ISO 8601 UTC
created_by_user     TEXT NOT NULL         -- User identifier (for future multi-user)
```

**`extraction_results` table:**
```sql
id                      INTEGER PRIMARY KEY
imported_file_id        INTEGER NOT NULL      -- FK to imported_files.id
extraction_status       TEXT NOT NULL         -- 'pending', 'in_progress', 'completed', 'failed'
extraction_method       TEXT NOT NULL         -- 'local_pdf' or API provider name (e.g., 'azure_invoice', 'openai_vision')
raw_text                TEXT                  -- Full extracted text
structured_data         TEXT                  -- JSON blob of structured fields
suggested_tasks         TEXT                  -- JSON array of suggested tasks
error_message           TEXT                  -- Error details if failed
extraction_version      INTEGER DEFAULT 1     -- Version number for re-extraction
extracted_at            TEXT                  -- ISO 8601 UTC (when extraction completed)
created_at              TEXT NOT NULL         -- ISO 8601 UTC
updated_at              TEXT NOT NULL         -- ISO 8601 UTC

UNIQUE(imported_file_id, extraction_version)
```

**Structured data JSON example (for bill/invoice):**
```json
{
  "document_type": "bill",
  "vendor": "Acme Electric Company",
  "total_amount": 125.50,
  "currency": "USD",
  "due_date": "2026-02-15",
  "invoice_number": "INV-2026-001234",
  "line_items": [
    {"description": "Electricity usage", "amount": 100.00},
    {"description": "Service fee", "amount": 25.50}
  ]
}
```

**Suggested tasks JSON example:**
```json
[
  {
    "title": "Pay Acme Electric Bill",
    "description": "Invoice INV-2026-001234 for $125.50",
    "due_date": "2026-02-15",
    "priority": "high",
    "tags": ["@bill", "@finance"]
  }
]
```

### File Storage Strategy

**Local Storage Structure:**
```
PROJECT_ROOT/
└── data/
    └── ingest/
        └── <uuid>/              # Unique folder per imported file
            ├── original.ext     # Original imported file (unchanged)
            ├── metadata.json    # Optional: Import metadata
            └── thumbnails/      # Optional: Generated thumbnails
                └── preview.png
```

**UUID Generation:**
- Use Python's `uuid.uuid4()` for unique folder names
- Store UUID in `imported_files.file_uuid` column
- File path construction: `data/ingest/{file_uuid}/original.{ext}`

**File Security:**
- Set restrictive file permissions (owner read/write only)
- Validate file types before storage (check magic bytes, not just extension)
- Sanitize filenames to prevent path traversal attacks

### PDF Text Extraction (Local)

**Library Selection:**
- **Primary:** `pdfplumber` (more robust, better text extraction)
- **Fallback:** `PyPDF2` (lightweight, faster for simple PDFs)

**Detection Logic:**
```python
def has_selectable_text(pdf_path: str) -> bool:
    """Check if PDF has extractable text."""
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:3]:  # Check first 3 pages
            text = page.extract_text()
            if text and len(text.strip()) > 50:  # Minimum text threshold
                return True
    return False
```

**Extraction Implementation:**
```python
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from text-based PDF."""
    import pdfplumber
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n\n".join(full_text)
```

### External API Integration (OCR)

**Azure Invoice Model (for Bill/Invoice mode):**
- **Endpoint:** Azure Form Recognizer `prebuilt-invoice` model
- **Capabilities:** Specialized for invoices - extracts vendor, total, line items, dates
- **Output:** Structured JSON with high confidence scores
- **Rate Limit:** TBD based on user's Azure plan
- **API Key Storage:** Windows Credential Manager via `keyring` library

**OpenAI Vision (for Note/Image mode):**
- **Endpoint:** OpenAI GPT-4 Vision API
- **Capabilities:** General-purpose vision model - extracts text, entities, context
- **Output:** Natural language description + structured JSON (via prompt engineering)
- **Rate Limit:** TBD based on user's OpenAI plan
- **API Key Storage:** Windows Credential Manager via `keyring` library

**Google Cloud Vision OCR (fallback):**
- **Endpoint:** Google Vision API Document Text Detection
- **Capabilities:** General OCR - extracts text from any image
- **Output:** Plain text (requires post-processing for structured data)
- **Rate Limit:** 1000 requests/month free tier
- **API Key Storage:** Windows Credential Manager via `keyring` library

**Schema Enforcement (CRITICAL per architecture):**
All API responses must be validated against Pydantic schemas:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class LineItem(BaseModel):
    description: str
    amount: float

class InvoiceExtractionResult(BaseModel):
    document_type: str = "bill"
    vendor: Optional[str] = None
    total_amount: Optional[float] = None
    currency: str = "USD"
    due_date: Optional[str] = None  # ISO 8601 format
    invoice_number: Optional[str] = None
    line_items: List[LineItem] = []

# Validate API response before saving:
result = InvoiceExtractionResult(**api_response)
```

### Async Extraction Pipeline

**Processing Flow:**
1. User imports file → `FileImportService.import_file()`
2. File stored locally → `StorageService.store_file()`
3. Create `imported_files` database record
4. Emit `fileImported` signal
5. Queue extraction job → `ExtractionService.queue_extraction()`
6. Background worker picks up job → `ExtractionWorker.process()`
7. Worker determines extraction method (local PDF vs. OCR API)
8. Worker performs extraction (local or API call)
9. Worker validates result with Pydantic schema
10. Worker saves to `extraction_results` table
11. Emit `extractionCompleted` signal
12. UI updates to show extracted data

**Async Implementation:**
- Use Python's `threading` or `asyncio` for background processing
- Use Qt's `QThread` for UI-safe threading
- Implement queue with `queue.Queue` or `asyncio.Queue`
- Show contextual loading indicator during extraction (per architecture)

### One-Click Task Creation (AC #7)

**Integration with Task Management:**
- Use existing task creation service from Epic 2 (Story 2.2)
- Pre-populate task fields from extracted data:
  - **Title:** From `suggested_tasks[0].title` or `vendor` + "bill"
  - **Description:** From `suggested_tasks[0].description` or formatted extraction data
  - **Due Date:** From `due_date` field in structured data
  - **Tags:** Auto-tag with `@bill` or `@invoice`
  - **Priority:** Based on due date proximity (high if due soon)

**Task Creation Flow:**
1. User clicks "Create Task" button in extraction results UI
2. `TaskCreationService.create_task_from_extraction(extraction_result_id)`
3. Load extraction data from database
4. Parse suggested tasks or structure data into task format
5. Create task using task management service
6. Emit `taskCreated` signal
7. UI navigates to newly created task or shows confirmation

### Re-Extraction and Versioning (AC #8)

**Versioning Strategy:**
- Each re-extraction increments `extraction_version` in `extraction_results` table
- Keep previous extraction versions for history/comparison
- UI shows latest version by default, allow user to view older versions
- Option to "Overwrite" (delete old versions) or "Keep History"

**Re-Extraction Triggers:**
- User clicks "Re-Extract" button in file viewer
- User changes `import_mode` (Bill/Invoice ↔ Note/Image)
- Extraction failed and user retries

### Error Handling

**File Import Errors:**
- Unsupported file type → Show user-friendly error dialog
- File too large (>10MB) → Warn user, offer to proceed anyway
- Read permission denied → Prompt OS permission request
- Corrupted file → Show error, save original file anyway for manual recovery

**Extraction Errors:**
- Local PDF extraction fails → Fall back to OCR API
- API timeout/failure → Retry with exponential backoff (per NFR8)
- Invalid API response → Log error, show user-friendly message
- No text detected → Mark as completed but empty result

**Task Creation Errors:**
- Task service unavailable → Show error, allow manual retry
- Invalid task data → Validate before creation, show validation errors

**Global Error Handling:**
- Integrate with architecture's global error handler
- Log all errors to local debugging log
- Display user-friendly error dialogs (non-technical language)

### Testing Standards

**Unit Tests:**
- Test file storage service (UUID generation, path construction)
- Test PDF text extraction (mock PDF files)
- Test OCR API clients (mock API responses)
- Test Pydantic schema validation (valid and invalid data)
- Test async extraction worker (queue processing)

**Integration Tests:**
- Test full import-extract-display flow with real files
- Use test database and test file storage directory
- Mock external APIs to avoid API costs during testing

**Performance Tests:**
- Validate async processing doesn't block UI
- Test large file handling (10MB PDFs)
- Test extraction queue under load (multiple files)

**Edge Case Tests:**
- Empty PDF (no text, no images)
- Corrupted image file
- PDF with mix of text and images
- API rate limit exceeded
- Network offline during extraction

### Security & Privacy

**API Key Security:**
- Store API keys in Windows Credential Manager via `keyring` library
- Never log or display API keys
- Require user to provide their own API keys (privacy-preserving)
- Validate API keys before making requests

**File Security:**
- Validate file types (check magic bytes, not just extension)
- Sanitize filenames to prevent path traversal
- Set restrictive file permissions (owner only)
- Isolate user data (per NFR3: data isolation)

**Privacy Considerations:**
- File contents sent to external APIs (Azure, OpenAI, Google)
- Inform user in settings about data sharing with external providers
- Provide option to use local extraction only (disable OCR APIs)
- No file data persisted on external servers (API calls are one-time)

### UI/UX Considerations

**Empathetic Co-Pilot Tone:**
- Extraction should feel magical and effortless
- Use encouraging messages ("Extracting information for you...")
- Non-intrusive error messages ("Oops, I couldn't read that file. Want to try again?")

**Drag-and-Drop UX:**
- Large, clear drop zone with visual feedback on hover
- Show file preview after drop (thumbnail or icon)
- Support multiple file formats (PDF, PNG, JPG)

**Extraction Results Display:**
- Show raw text and structured fields side-by-side
- Make extracted fields editable (user can correct errors)
- Highlight key information (vendor, total, due date)
- Provide clear "Create Task" CTA button

**Accessibility:**
- Keyboard navigation for file picker
- Screen reader support for extraction results
- High contrast for loading indicators

### Common LLM Mistakes to AVOID

- ❌ Don't make synchronous file I/O - always use async or background threads
- ❌ Don't block the UI thread during extraction
- ❌ Don't expose API keys in logs, error messages, or UI
- ❌ Don't store unvalidated API responses - always use Pydantic schemas
- ❌ Don't forget to handle extraction failures gracefully
- ❌ Don't re-extract unnecessarily - implement versioning properly
- ❌ Don't ignore file security - validate types, sanitize filenames, restrict permissions
- ❌ Don't forget to test with real files (not just mock data)
- ❌ Don't use OCR APIs for text-based PDFs - extract locally first
- ❌ Don't forget NFR1/NFR2 - UI must remain responsive

### References

- [Source: architecture.md#File Ingestion and Extraction Pipeline] - Complete extraction strategy, API choices, schema discipline
- [Source: architecture.md#Data Architecture] - SQLAlchemy + Pydantic + Alembic
- [Source: architecture.md#Frontend Architecture] - MVVM + Atomic Design + Signals & Slots
- [Source: architecture.md#AI/ML Integration Architecture#API Key Security] - Keyring library for secure API key storage
- [Source: architecture.md#Process Patterns] - Global error handling and loading states
- [Source: architecture.md#Naming Patterns] - Database and code naming conventions
- [Source: epics.md#Epic 3] - Full epic context
- [Source: epics.md#Story 3.3 Acceptance Criteria] - Original acceptance criteria
- [Source: epics.md#NFR1, NFR2, NFR3] - Performance and security requirements
- [Source: epics.md#NFR8, NFR9] - Integration failure handling and retry logic

### Future Enhancements (Post-MVP)

- Support more file formats (DOCX, TXT, HEIC)
- Implement batch file import (drag-drop folder)
- Add file preview/viewer within app (no external app needed)
- Implement smart cropping for images (auto-detect document boundaries)
- Add confidence scores for extracted fields (show low-confidence fields highlighted)
- Implement learning from user corrections (improve extraction over time)
- Add export functionality (export extracted data to CSV/JSON)

## Dev Agent Record

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent during implementation_

### Completion Notes List

_To be filled by dev agent with implementation learnings_

### File List

_To be filled by dev agent with all files created/modified_
