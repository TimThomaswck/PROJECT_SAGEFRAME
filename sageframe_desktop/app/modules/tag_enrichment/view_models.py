"""View Model for tag enrichment UI integration.

Provides signals and methods for:
- Displaying enrichment status
- Managing enrichment lifecycle
- Handling enrichment data display
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Slot

from app.modules.tag_enrichment.enrichment_service import EnrichmentService, EnrichmentStatus
from app.database import SessionLocal
from app.modules.tag_management.models import TagEnrichment


@dataclass
class EnrichmentDisplay:
    """Data class for enrichment display in UI."""
    
    tagged_item_id: int
    api_provider: str
    status: str  # pending, fetching, completed, failed
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    fetched_at: Optional[str] = None


class EnrichmentViewModel(QObject):
    """ViewModel for tag enrichment functionality.
    
    Signals:
        enrichmentStarted: Emitted when enrichment begins (tagged_item_id, provider)
        enrichmentCompleted: Emitted when enrichment succeeds (tagged_item_id, data)
        enrichmentFailed: Emitted when enrichment fails (tagged_item_id, error_msg)
        enrichmentDataUpdated: Emitted when enrichment data changes (enrichment_display)
    """
    
    # Signals
    enrichmentStarted = Signal(int, str)  # tagged_item_id, provider
    enrichmentCompleted = Signal(int, dict)  # tagged_item_id, enrichment_data
    enrichmentFailed = Signal(int, str)  # tagged_item_id, error_message
    enrichmentDataUpdated = Signal(object)  # EnrichmentDisplay
    
    def __init__(self, enrichment_service: Optional[EnrichmentService] = None):
        """Initialize enrichment view model.
        
        Args:
            enrichment_service: EnrichmentService instance (or None to create one)
        """
        super().__init__()
        
        self.service = enrichment_service or EnrichmentService()
        
        # Register signal callbacks with service
        self.service.on_enrichment_started = self._on_enrichment_started
        self.service.on_enrichment_completed = self._on_enrichment_completed
        self.service.on_enrichment_failed = self._on_enrichment_failed
    
    def _on_enrichment_started(self, tagged_item_id: int, provider: str) -> None:
        """Handle enrichment start callback from service.
        
        Args:
            tagged_item_id: ID of tagged item being enriched
            provider: API provider name
        """
        self.enrichmentStarted.emit(tagged_item_id, provider)
        self._update_display(tagged_item_id, provider, EnrichmentStatus.FETCHING.value)
    
    def _on_enrichment_completed(self, tagged_item_id: int, enrichment_data: Dict[str, Any]) -> None:
        """Handle enrichment completion callback from service.
        
        Args:
            tagged_item_id: ID of tagged item
            enrichment_data: Enriched metadata dictionary
        """
        provider = enrichment_data.get("api_provider", "unknown")
        self.enrichmentCompleted.emit(tagged_item_id, enrichment_data)
        self._update_display(tagged_item_id, provider, EnrichmentStatus.COMPLETED.value, enrichment_data)
    
    def _on_enrichment_failed(self, tagged_item_id: int, error_message: str) -> None:
        """Handle enrichment failure callback from service.
        
        Args:
            tagged_item_id: ID of tagged item
            error_message: Error message
        """
        self.enrichmentFailed.emit(tagged_item_id, error_message)
        # Try to get provider from database
        db = SessionLocal()
        try:
            enrichment = db.query(TagEnrichment).filter(
                TagEnrichment.tagged_item_id == tagged_item_id
            ).first()
            provider = enrichment.api_provider if enrichment else "unknown"
        finally:
            db.close()
        
        self._update_display(tagged_item_id, provider, EnrichmentStatus.FAILED.value, error=error_message)
    
    def _update_display(
        self,
        tagged_item_id: int,
        provider: str,
        status: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """Update and emit enrichment display data.
        
        Args:
            tagged_item_id: ID of tagged item
            provider: API provider name
            status: Enrichment status
            data: Enrichment data (if completed)
            error: Error message (if failed)
        """
        display = EnrichmentDisplay(
            tagged_item_id=tagged_item_id,
            api_provider=provider,
            status=status,
            data=data,
            error=error,
            fetched_at=datetime.now(timezone.utc).isoformat() if data else None
        )
        self.enrichmentDataUpdated.emit(display)
    
    @Slot(int)
    def trigger_enrichment(self, tagged_item_id: int) -> None:
        """Trigger enrichment for a tagged item.
        
        Args:
            tagged_item_id: ID of TaggedItem to enrich
        """
        import asyncio
        
        # Create a task to run async enrichment
        asyncio.create_task(self.service.enrich_tagged_item(tagged_item_id))
    
    @Slot(int, str)
    def retry_enrichment(self, tagged_item_id: int, provider: str) -> None:
        """Manually retry failed enrichment.
        
        Args:
            tagged_item_id: ID of TaggedItem
            provider: API provider name
        """
        import asyncio
        
        asyncio.create_task(self.service.manual_retry_enrichment(tagged_item_id, provider))
    
    def set_api_key(self, provider: str, api_key: str) -> None:
        """Set API key for a provider.
        
        Args:
            provider: Provider name ('tmdb', 'google_books')
            api_key: API key to store
        """
        self.service.set_api_key(provider, api_key)
    
    def get_enrichment_data(self, tagged_item_id: int, provider: str) -> Optional[Dict[str, Any]]:
        """Get enrichment data for a tagged item.
        
        Args:
            tagged_item_id: ID of TaggedItem
            provider: API provider name
        
        Returns:
            Enrichment data dict or None
        """
        db = SessionLocal()
        try:
            enrichment = db.query(TagEnrichment).filter(
                TagEnrichment.tagged_item_id == tagged_item_id,
                TagEnrichment.api_provider == provider
            ).first()
            
            if enrichment and enrichment.fetch_status == EnrichmentStatus.COMPLETED.value:
                return enrichment.enrichment_data
            
            return None
        
        finally:
            db.close()
    
    def get_enrichment_status(self, tagged_item_id: int, provider: str) -> Optional[str]:
        """Get enrichment status for a tagged item.
        
        Args:
            tagged_item_id: ID of TaggedItem
            provider: API provider name
        
        Returns:
            Status string or None if not found
        """
        db = SessionLocal()
        try:
            enrichment = db.query(TagEnrichment).filter(
                TagEnrichment.tagged_item_id == tagged_item_id,
                TagEnrichment.api_provider == provider
            ).first()
            
            return enrichment.fetch_status if enrichment else None
        
        finally:
            db.close()
