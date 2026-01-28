"""Tag enrichment service with async queue and caching.

This module provides the EnrichmentService which:
- Manages async enrichment jobs with a queue system
- Handles API key management via keyring
- Implements local caching to minimize API calls
- Triggers enrichment when tagged items are saved
- Signals enrichment status changes to the UI
"""

import asyncio
import json
import logging
import keyring
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import SessionLocal
from app.modules.tag_management.models import TagEnrichment, TaggedItem, Tag
from app.modules.tag_enrichment.api_clients import TMDBClient, GoogleBooksClient

logger = logging.getLogger(__name__)

# Keyring service name for storing API keys
KEYRING_SERVICE = "sageframe_tag_enrichment"


class EnrichmentStatus(Enum):
    """Enrichment status enumeration."""
    PENDING = "pending"
    FETCHING = "fetching"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EnrichmentJob:
    """Represents an enrichment job in the queue."""
    
    tagged_item_id: int
    tag_name: str
    content: Optional[str]
    api_provider: str
    retry_count: int = 0
    max_retries: int = 3


class EnrichmentService:
    """Service for managing tag enrichment from external APIs.
    
    Features:
    - Async queue-based processing
    - Exponential backoff retry (1s, 2s, 4s)
    - Local caching of enrichment results
    - Keyring-based API key storage
    - Qt signal callbacks for UI updates
    """
    
    # Tag-to-API-provider mapping
    PROVIDER_MAPPING = {
        "movie": "tmdb",
        "film": "tmdb",
        "book": "google_books",
        "novel": "google_books",
    }
    
    def __init__(self, max_concurrent_jobs: int = 3):
        """Initialize enrichment service.
        
        Args:
            max_concurrent_jobs: Maximum concurrent API requests
        """
        self.max_concurrent_jobs = max_concurrent_jobs
        self.queue: asyncio.Queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent_jobs)
        self.workers_running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # Callbacks for UI updates (will be set by view model)
        self.on_enrichment_started = None
        self.on_enrichment_completed = None
        self.on_enrichment_failed = None
    
    def set_api_key(self, provider: str, api_key: str) -> None:
        """Store API key securely in keyring.
        
        Args:
            provider: API provider name ('tmdb', 'google_books')
            api_key: API key to store
        """
        try:
            keyring.set_password(KEYRING_SERVICE, provider, api_key)
            logger.info(f"API key stored for provider: {provider}")
        except Exception as e:
            logger.error(f"Failed to store API key for {provider}: {e}")
            raise
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Retrieve API key from keyring.
        
        Args:
            provider: API provider name ('tmdb', 'google_books')
        
        Returns:
            API key or None if not found
        """
        try:
            api_key = keyring.get_password(KEYRING_SERVICE, provider)
            return api_key
        except Exception as e:
            logger.error(f"Failed to retrieve API key for {provider}: {e}")
            return None
    
    def clear_api_key(self, provider: str) -> None:
        """Clear API key from keyring.
        
        Args:
            provider: API provider name ('tmdb', 'google_books')
        """
        try:
            keyring.delete_password(KEYRING_SERVICE, provider)
            logger.info(f"API key cleared for provider: {provider}")
        except Exception as e:
            logger.warning(f"Failed to clear API key for {provider}: {e}")
    
    def _get_provider_for_tag(self, tag_name: str) -> Optional[str]:
        """Get API provider for a tag type.
        
        Args:
            tag_name: Tag name (e.g., 'movie', 'book')
        
        Returns:
            Provider name or None if tag type not supported
        """
        return self.PROVIDER_MAPPING.get(tag_name.lower())
    
    def _has_cached_enrichment(self, db: Session, tagged_item_id: int, provider: str) -> bool:
        """Check if enrichment is already cached.
        
        Args:
            db: Database session
            tagged_item_id: TaggedItem ID
            provider: API provider name
        
        Returns:
            True if cached enrichment exists and is not failed
        """
        enrichment = db.query(TagEnrichment).filter(
            and_(
                TagEnrichment.tagged_item_id == tagged_item_id,
                TagEnrichment.api_provider == provider,
                TagEnrichment.fetch_status.in_(["completed", "pending", "fetching"])
            )
        ).first()
        return enrichment is not None
    
    async def enrich_tagged_item(self, tagged_item_id: int) -> None:
        """Trigger enrichment for a tagged item.
        
        This method:
        1. Checks if enrichment is needed and not cached
        2. Determines the API provider from the tag type
        3. Queues the enrichment job
        
        Args:
            tagged_item_id: ID of TaggedItem to enrich
        """
        db = SessionLocal()
        try:
            # Get tagged item with tag
            tagged_item = db.query(TaggedItem).filter(
                TaggedItem.id == tagged_item_id
            ).first()
            
            if not tagged_item:
                logger.warning(f"TaggedItem not found: {tagged_item_id}")
                return
            
            # Don't enrich if no content (e.g., @movie without a title)
            if not tagged_item.content:
                logger.debug(f"Skipping enrichment for tag without content: {tagged_item_id}")
                return
            
            # Get tag name
            tag = tagged_item.tag
            if not tag:
                logger.warning(f"Tag not found for TaggedItem: {tagged_item_id}")
                return
            
            tag_name = tag.tag_name
            
            # Determine provider
            provider = self._get_provider_for_tag(tag_name)
            if not provider:
                logger.debug(f"No enrichment provider for tag: {tag_name}")
                return
            
            # Check if already cached
            if self._has_cached_enrichment(db, tagged_item_id, provider):
                logger.debug(f"Enrichment already cached for {tagged_item_id} from {provider}")
                return
            
            # Queue enrichment job
            job = EnrichmentJob(
                tagged_item_id=tagged_item_id,
                tag_name=tag_name,
                content=tagged_item.content,
                api_provider=provider
            )
            await self.queue.put(job)
            logger.info(f"Queued enrichment job: {tagged_item_id} ({tag_name}:{tagged_item.content})")
        
        finally:
            db.close()
    
    async def _process_enrichment_job(self, job: EnrichmentJob) -> None:
        """Process a single enrichment job.
        
        Args:
            job: EnrichmentJob to process
        """
        db = SessionLocal()
        try:
            async with self.semaphore:
                # Callback: enrichment started
                if self.on_enrichment_started:
                    self.on_enrichment_started(job.tagged_item_id, job.api_provider)
                
                # Mark as fetching
                enrichment = db.query(TagEnrichment).filter(
                    and_(
                        TagEnrichment.tagged_item_id == job.tagged_item_id,
                        TagEnrichment.api_provider == job.api_provider
                    )
                ).first()
                
                if enrichment:
                    enrichment.fetch_status = EnrichmentStatus.FETCHING.value
                    db.commit()
                
                # Get API key
                api_key = self.get_api_key(job.api_provider)
                if not api_key:
                    error_msg = f"API key not configured for {job.api_provider}"
                    logger.error(error_msg)
                    await self._mark_enrichment_failed(job, error_msg)
                    if self.on_enrichment_failed:
                        self.on_enrichment_failed(job.tagged_item_id, error_msg)
                    return
                
                # Fetch enrichment
                enrichment_data = await self._fetch_enrichment(job, api_key)
                
                if enrichment_data:
                    await self._save_enrichment(job, enrichment_data)
                    logger.info(f"Enrichment completed: {job.tagged_item_id}")
                    if self.on_enrichment_completed:
                        self.on_enrichment_completed(job.tagged_item_id, enrichment_data)
                else:
                    if job.retry_count < job.max_retries:
                        job.retry_count += 1
                        delay = min(2 ** job.retry_count, 8)  # Exponential backoff: 1, 2, 4, 8s
                        logger.warning(f"Enrichment failed. Retrying in {delay}s... (attempt {job.retry_count}/{job.max_retries})")
                        await asyncio.sleep(delay)
                        await self.queue.put(job)
                    else:
                        error_msg = "Enrichment failed after max retries"
                        await self._mark_enrichment_failed(job, error_msg)
                        if self.on_enrichment_failed:
                            self.on_enrichment_failed(job.tagged_item_id, error_msg)
        
        except Exception as e:
            logger.error(f"Error processing enrichment job: {e}", exc_info=True)
            error_msg = f"Unexpected error during enrichment: {str(e)}"
            await self._mark_enrichment_failed(job, error_msg)
            if self.on_enrichment_failed:
                self.on_enrichment_failed(job.tagged_item_id, error_msg)
        
        finally:
            db.close()
    
    async def _fetch_enrichment(self, job: EnrichmentJob, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch enrichment data from external API.
        
        Args:
            job: EnrichmentJob with content to enrich
            api_key: API key for the provider
        
        Returns:
            Enrichment data dict or None if failed
        """
        try:
            if job.api_provider == "tmdb":
                async with TMDBClient(api_key) as client:
                    return await client.enrich_movie(job.content)
            
            elif job.api_provider == "google_books":
                async with GoogleBooksClient(api_key) as client:
                    return await client.enrich_book(job.content)
            
            else:
                logger.error(f"Unknown API provider: {job.api_provider}")
                return None
        
        except Exception as e:
            logger.error(f"Error fetching enrichment from {job.api_provider}: {e}", exc_info=True)
            return None
    
    async def _save_enrichment(self, job: EnrichmentJob, enrichment_data: Dict[str, Any]) -> None:
        """Save enrichment data to database.
        
        Args:
            job: EnrichmentJob
            enrichment_data: Enrichment data dict to save
        """
        db = SessionLocal()
        try:
            enrichment = db.query(TagEnrichment).filter(
                and_(
                    TagEnrichment.tagged_item_id == job.tagged_item_id,
                    TagEnrichment.api_provider == job.api_provider
                )
            ).first()
            
            if not enrichment:
                enrichment = TagEnrichment(
                    tagged_item_id=job.tagged_item_id,
                    api_provider=job.api_provider
                )
                db.add(enrichment)
            
            enrichment.enrichment_data = enrichment_data
            enrichment.fetch_status = EnrichmentStatus.COMPLETED.value
            enrichment.fetched_at = datetime.now(timezone.utc)
            enrichment.error_message = None
            
            db.commit()
        
        except Exception as e:
            logger.error(f"Error saving enrichment: {e}")
            db.rollback()
        
        finally:
            db.close()
    
    async def _mark_enrichment_failed(self, job: EnrichmentJob, error_msg: str) -> None:
        """Mark enrichment as failed with error message.
        
        Args:
            job: EnrichmentJob
            error_msg: Error message
        """
        db = SessionLocal()
        try:
            enrichment = db.query(TagEnrichment).filter(
                and_(
                    TagEnrichment.tagged_item_id == job.tagged_item_id,
                    TagEnrichment.api_provider == job.api_provider
                )
            ).first()
            
            if not enrichment:
                enrichment = TagEnrichment(
                    tagged_item_id=job.tagged_item_id,
                    api_provider=job.api_provider
                )
                db.add(enrichment)
            
            enrichment.fetch_status = EnrichmentStatus.FAILED.value
            enrichment.error_message = error_msg
            
            db.commit()
        
        except Exception as e:
            logger.error(f"Error marking enrichment as failed: {e}")
            db.rollback()
        
        finally:
            db.close()
    
    async def start_workers(self, num_workers: int = 2) -> None:
        """Start background worker tasks.
        
        Args:
            num_workers: Number of concurrent workers
        """
        if self.workers_running:
            logger.warning("Workers already running")
            return
        
        self.workers_running = True
        for i in range(num_workers):
            task = asyncio.create_task(self._worker(f"enrichment-worker-{i}"))
            self.worker_tasks.append(task)
        
        logger.info(f"Started {num_workers} enrichment workers")
    
    async def stop_workers(self) -> None:
        """Stop all background worker tasks."""
        self.workers_running = False
        
        # Wait for queue to be processed
        await self.queue.join()
        
        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for all tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        logger.info("Stopped all enrichment workers")
    
    async def _worker(self, worker_id: str) -> None:
        """Worker coroutine that processes enrichment jobs.
        
        Args:
            worker_id: Unique worker identifier
        """
        logger.info(f"Worker {worker_id} started")
        try:
            while self.workers_running:
                try:
                    # Get job with timeout to allow graceful shutdown
                    job = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                    
                    try:
                        await self._process_enrichment_job(job)
                    finally:
                        self.queue.task_done()
                
                except asyncio.TimeoutError:
                    # No job available, continue waiting
                    continue
                
                except asyncio.CancelledError:
                    break
        
        finally:
            logger.info(f"Worker {worker_id} stopped")
    
    async def manual_retry_enrichment(self, tagged_item_id: int, provider: str) -> None:
        """Manually retry failed enrichment.
        
        Args:
            tagged_item_id: TaggedItem ID
            provider: API provider name
        """
        db = SessionLocal()
        try:
            # Get tagged item
            tagged_item = db.query(TaggedItem).filter(
                TaggedItem.id == tagged_item_id
            ).first()
            
            if not tagged_item:
                logger.warning(f"TaggedItem not found: {tagged_item_id}")
                return
            
            # Clear previous enrichment
            enrichment = db.query(TagEnrichment).filter(
                and_(
                    TagEnrichment.tagged_item_id == tagged_item_id,
                    TagEnrichment.api_provider == provider
                )
            ).first()
            
            if enrichment:
                db.delete(enrichment)
                db.commit()
            
            # Re-queue for enrichment
            await self.enrich_tagged_item(tagged_item_id)
        
        finally:
            db.close()
