"""Integration between TagService and EnrichmentService.

Hooks enrichment into the tagging workflow so that enrichment
automatically triggers when tagged items are saved.
"""

import asyncio
import logging
from typing import Optional

from app.modules.tag_management.services import TagService
from app.modules.tag_enrichment.enrichment_service import EnrichmentService

logger = logging.getLogger(__name__)


class TagEnrichmentIntegration:
    """Integrates tag management with enrichment service.
    
    Automatically triggers enrichment when:
    - A new tagged item is created with content
    - A tagged item's content is updated
    """
    
    def __init__(self, tag_service: TagService, enrichment_service: EnrichmentService):
        """Initialize integration.
        
        Args:
            tag_service: TagService instance
            enrichment_service: EnrichmentService instance
        """
        self.tag_service = tag_service
        self.enrichment_service = enrichment_service
    
    def enrich_on_tag_created(self, tagged_item_id: int) -> None:
        """Trigger enrichment when a tagged item is created.
        
        Args:
            tagged_item_id: ID of newly created TaggedItem
        """
        asyncio.create_task(self.enrichment_service.enrich_tagged_item(tagged_item_id))
    
    def enrich_on_tag_updated(self, tagged_item_id: int) -> None:
        """Trigger enrichment when a tagged item is updated.
        
        Args:
            tagged_item_id: ID of updated TaggedItem
        """
        asyncio.create_task(self.enrichment_service.enrich_tagged_item(tagged_item_id))
