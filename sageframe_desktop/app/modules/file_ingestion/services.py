"""Services for file import and asynchronous extraction."""

import asyncio
import mimetypes
from typing import Optional, Dict, Any
import keyring

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.modules.file_ingestion.models import ImportedFile, ExtractionResult
from app.modules.file_ingestion.storage import store_imported_file
from app.modules.file_ingestion.extraction.pdf_extractor import extract_text_from_pdf, has_selectable_text, rasterize_pdf_first_page
from app.modules.file_ingestion.extraction.schemas import ExtractionOutput
from app.modules.file_ingestion.extraction.ocr_clients import GoogleVisionClient
from app.modules.file_ingestion.extraction.field_parser import parse_bill_fields


class FileImportService:
    def __init__(self, session: Optional[Session] = None):
        self._session = session or SessionLocal()
        self._owns_session = session is None

    def close(self):
        if self._owns_session and self._session:
            self._session.close()

    def import_file(self, src_path: str) -> ImportedFile:
        # Validate file type
        mime, _ = mimetypes.guess_type(src_path)
        if not mime or not any(mime.startswith(prefix) for prefix in ("image/", "application/pdf")):
            raise ValueError("Unsupported file type. Only images and PDFs are allowed.")

        stored_path, file_name, ingest_uuid = store_imported_file(src_path)
        imported = ImportedFile(
            original_path=src_path,
            stored_path=stored_path,
            file_name=file_name,
            mime_type=mime,
            ingest_uuid=ingest_uuid,
        )
        self._session.add(imported)
        self._session.commit()
        self._session.refresh(imported)
        return imported


class ExtractionService:
    """Async extraction queue service to avoid blocking UI."""

    def __init__(self, max_concurrent_jobs: int = 2):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent_jobs)
        self.workers_running = False
        self.worker_tasks = []
        # UI callbacks can be attached by view models
        self.on_extraction_started = None
        self.on_extraction_completed = None
        self.on_extraction_failed = None

    async def start_workers(self, num_workers: int = 2):
        if self.workers_running:
            return
        self.workers_running = True
        for i in range(num_workers):
            task = asyncio.create_task(self._worker(f"extraction-worker-{i}"))
            self.worker_tasks.append(task)

    async def stop_workers(self):
        self.workers_running = False
        await self.queue.join()
        for t in self.worker_tasks:
            t.cancel()
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()

    async def _worker(self, worker_id: str):
        while self.workers_running:
            try:
                job = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                try:
                    await self._process_job(job)
                finally:
                    self.queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def submit_extraction(self, imported_file_id: int, mode: Optional[str] = None):
        await self.queue.put({"imported_file_id": imported_file_id, "mode": mode})

    async def _process_job(self, job: Dict[str, Any]):
        db = SessionLocal()
        try:
            print(f"[Extraction] Processing job: {job}")
            imported = db.query(ImportedFile).filter(ImportedFile.id == job["imported_file_id"]).first()
            if not imported:
                print(f"[Extraction] ImportedFile {job['imported_file_id']} not found")
                return
            if self.on_extraction_started:
                # Call callback safely from async context
                loop = asyncio.get_event_loop()
                loop.call_soon_threadsafe(self.on_extraction_started, imported.id)
            
            print(f"[Extraction] Starting extraction for {imported.file_name}, mode: {job.get('mode')}")

            output: Optional[ExtractionOutput] = None

            # Determine mode
            mode = job.get("mode") or "note"  # Default to "note" if not specified
            
            raw_text = None
            structured_fields = None
            provider = None
            
            # Get Google Vision API key
            api_key = None
            try:
                api_key = keyring.get_password("sageframe_file_ingestion", "google_vision")
            except Exception:
                pass
            
            if not api_key:
                print(f"[Extraction] Google Vision API key not configured")
                raise Exception("Google Vision API key is required for OCR")
            
            try:
                # Handle PDF files
                if imported.mime_type == "application/pdf":
                    # Try extracting text first (for selectable PDFs)
                    if has_selectable_text(imported.stored_path):
                        raw_text = extract_text_from_pdf(imported.stored_path)
                        provider = "pypdf2"
                        print(f"[Extraction] Extracted text from selectable PDF")
                    else:
                        # Rasterize PDF and use Google Vision OCR
                        import os
                        try:
                            temp_img = rasterize_pdf_first_page(imported.stored_path)
                            async with GoogleVisionClient(api_key) as client:
                                raw_text = await client.extract_text(temp_img)
                            # Clean up temp file
                            try:
                                os.unlink(temp_img)
                            except Exception:
                                pass
                            provider = "google_vision"
                            print(f"[Extraction] Google Vision extracted text from PDF")
                        except Exception as e:
                            print(f"[Extraction] PDF rasterization/OCR failed: {e}")
                            raw_text = None
                else:
                    # Image files - use Google Vision OCR directly
                    async with GoogleVisionClient(api_key) as client:
                        raw_text = await client.extract_text(imported.stored_path)
                    provider = "google_vision"
                    print(f"[Extraction] Google Vision extracted text from image")
            
            except Exception as e:
                print(f"[Extraction] Error during extraction: {e}")
                import traceback
                traceback.print_exc()
                raw_text = None

            
            # Parse structured fields for bill mode
            if mode == "bill" and raw_text:
                structured_fields = parse_bill_fields(raw_text)
            
            output = ExtractionOutput(
                raw_text=raw_text or None,
                structured_fields=structured_fields,
                mode=mode,
                provider=provider,
                version=1,
            )

            # Save result (overwrite versioning simplified)
            result = ExtractionResult(
                imported_file_id=imported.id,
                raw_text=output.raw_text,
                structured_fields=output.structured_fields,
                mode=output.mode,
                provider=output.provider,
                version=1,
            )
            db.add(result)
            db.commit()
            db.refresh(result)
            
            print(f"[Extraction] Extraction completed, result ID: {result.id}")

            if self.on_extraction_completed:
                # Call callback safely from async context
                loop = asyncio.get_event_loop()
                loop.call_soon_threadsafe(self.on_extraction_completed, imported.id, result.id)
        except Exception as e:
            print(f"[Extraction] Error during extraction: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            if self.on_extraction_failed:
                # Call callback safely from async context
                loop = asyncio.get_event_loop()
                loop.call_soon_threadsafe(self.on_extraction_failed, job.get("imported_file_id"), "Extraction failed")
        finally:
            db.close()
