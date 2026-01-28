"""Tag enrichment module for external API integration.

This module provides automatic enrichment of tagged content from external APIs:
- TMDB for movies/films
- Google Books for books/novels
"""

from app.modules.tag_enrichment.api_clients import (
    TMDBClient,
    GoogleBooksClient,
    TMDBMovieResponse,
    GoogleBooksResponse,
)

from app.modules.tag_enrichment.enrichment_service import (
    EnrichmentService,
    EnrichmentStatus,
    EnrichmentJob,
)

from app.modules.tag_enrichment.view_models import (
    EnrichmentViewModel,
    EnrichmentDisplay,
)

from app.modules.tag_enrichment.integration import (
    TagEnrichmentIntegration,
)

__all__ = [
    "TMDBClient",
    "GoogleBooksClient",
    "TMDBMovieResponse",
    "GoogleBooksResponse",
    "EnrichmentService",
    "EnrichmentStatus",
    "EnrichmentJob",
    "EnrichmentViewModel",
    "EnrichmentDisplay",
    "TagEnrichmentIntegration",
]
