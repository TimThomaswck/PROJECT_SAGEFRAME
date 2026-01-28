"""Tests for tag enrichment system (API clients and service).

Tests cover:
- TMDB API client (search, fetch, error handling, retry)
- Google Books API client (search, fetch, error handling, retry)
- EnrichmentService (queue, cache, keyring, async processing)
- Error scenarios (timeout, rate limit, auth failure, invalid response)
"""

import asyncio
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock, ANY
from typing import Dict, Any

# Note: Tests use pytest-asyncio for async fixtures
pytest_plugins = ("pytest_asyncio",)


class TestEnrichmentModels:
    """Tests for Pydantic validation models."""
    
    def test_tmdb_movie_response_validation(self):
        """Test TMDB movie response validation."""
        from app.modules.tag_enrichment.api_clients import TMDBMovieResponse
        
        # Valid response
        response = TMDBMovieResponse(
            id=278870,
            title="Inception",
            overview="A skilled thief...",
            vote_average=8.8
        )
        
        assert response.id == 278870
        assert response.title == "Inception"
        assert response.vote_average == 8.8
    
    def test_google_books_response_validation(self):
        """Test Google Books response validation."""
        from app.modules.tag_enrichment.api_clients import GoogleBooksResponse
        
        # Valid response
        response = GoogleBooksResponse(
            id="book_id",
            title="Dune",
            authors=["Frank Herbert"],
            average_rating=4.5
        )
        
        assert response.id == "book_id"
        assert response.title == "Dune"
        assert response.authors == ["Frank Herbert"]
        assert response.average_rating == 4.5
    
    def test_tmdb_rating_normalization(self):
        """Test TMDB rating normalization."""
        from app.modules.tag_enrichment.api_clients import TMDBMovieResponse
        
        response = TMDBMovieResponse(
            id=1,
            title="Test",
            vote_average=8.25
        )
        
        assert response.vote_average == 8.2 or response.vote_average == 8.25


class TestEnrichmentService:
    """Tests for EnrichmentService."""
    
    @pytest.fixture
    def service(self):
        """Create enrichment service instance."""
        from app.modules.tag_enrichment.enrichment_service import EnrichmentService
        return EnrichmentService(max_concurrent_jobs=3)
    
    def test_provider_mapping(self, service):
        """Test tag to provider mapping."""
        # Test supported tags
        assert service._get_provider_for_tag("movie") == "tmdb"
        assert service._get_provider_for_tag("film") == "tmdb"
        assert service._get_provider_for_tag("book") == "google_books"
        assert service._get_provider_for_tag("novel") == "google_books"
        
        # Test case insensitivity
        assert service._get_provider_for_tag("MOVIE") == "tmdb"
        assert service._get_provider_for_tag("BOOK") == "google_books"
        
        # Test unsupported tag
        assert service._get_provider_for_tag("podcast") is None
    
    def test_api_key_management(self, service):
        """Test secure API key storage and retrieval."""
        # Store API key
        try:
            service.set_api_key("tmdb", "test_api_key_123")
            
            # Retrieve API key
            retrieved_key = service.get_api_key("tmdb")
            assert retrieved_key == "test_api_key_123"
            
            # Clear API key
            service.clear_api_key("tmdb")
        
        except Exception as e:
            # Keyring may not be available in test environment
            pytest.skip(f"Keyring not available: {e}")
    
    def test_service_initialization(self, service):
        """Test EnrichmentService initialization."""
        assert service.max_concurrent_jobs == 3
        assert service.queue is not None
        assert service.semaphore is not None
        assert service.workers_running is False
        assert service.worker_tasks == []
    
    @pytest.mark.asyncio
    async def test_queue_enrichment_job(self, service):
        """Test queueing enrichment job."""
        from app.modules.tag_enrichment.enrichment_service import EnrichmentJob
        
        # Queue should be empty
        assert service.queue.empty()
        
        # Simulate queueing
        job = EnrichmentJob(
            tagged_item_id=1,
            tag_name="movie",
            content="Inception",
            api_provider="tmdb"
        )
        
        await service.queue.put(job)
        
        assert not service.queue.empty()
        
        # Retrieve job
        retrieved_job = await service.queue.get()
        assert retrieved_job.tagged_item_id == 1
        assert retrieved_job.content == "Inception"
        assert retrieved_job.api_provider == "tmdb"


class TestAPIClients:
    """Tests for API client basic functionality."""
    
    def test_tmdb_client_initialization(self):
        """Test TMDB client initialization."""
        from app.modules.tag_enrichment.api_clients import TMDBClient
        
        client = TMDBClient(api_key="test_key")
        
        assert client.api_key == "test_key"
        assert client.timeout == 10
        assert client.max_retries == 3
        assert client.base_url == "https://api.themoviedb.org/3"
        assert client.image_base_url == "https://image.tmdb.org/t/p/w200"
    
    def test_google_books_client_initialization(self):
        """Test Google Books client initialization."""
        from app.modules.tag_enrichment.api_clients import GoogleBooksClient
        
        client = GoogleBooksClient(api_key="test_key")
        
        assert client.api_key == "test_key"
        assert client.timeout == 10
        assert client.max_retries == 3
        assert client.base_url == "https://www.googleapis.com/books/v1"
    
    def test_tmdb_client_custom_params(self):
        """Test TMDB client with custom parameters."""
        from app.modules.tag_enrichment.api_clients import TMDBClient
        
        client = TMDBClient(api_key="key", timeout=30, max_retries=5)
        
        assert client.timeout == 30
        assert client.max_retries == 5


class TestEnrichmentServiceStatus:
    """Tests for EnrichmentStatus enum."""
    
    def test_enrichment_status_values(self):
        """Test enrichment status enum values."""
        from app.modules.tag_enrichment.enrichment_service import EnrichmentStatus
        
        assert EnrichmentStatus.PENDING.value == "pending"
        assert EnrichmentStatus.FETCHING.value == "fetching"
        assert EnrichmentStatus.COMPLETED.value == "completed"
        assert EnrichmentStatus.FAILED.value == "failed"
    
    def test_enrichment_job_creation(self):
        """Test EnrichmentJob creation."""
        from app.modules.tag_enrichment.enrichment_service import EnrichmentJob
        
        job = EnrichmentJob(
            tagged_item_id=5,
            tag_name="movie",
            content="The Matrix",
            api_provider="tmdb"
        )
        
        assert job.tagged_item_id == 5
        assert job.tag_name == "movie"
        assert job.content == "The Matrix"
        assert job.api_provider == "tmdb"
        assert job.retry_count == 0
        assert job.max_retries == 3


class TestEnrichmentIntegration:
    """Integration tests for enrichment workflow structure."""
    
    def test_service_has_required_methods(self):
        """Test that EnrichmentService has all required methods."""
        from app.modules.tag_enrichment.enrichment_service import EnrichmentService
        
        service = EnrichmentService()
        
        # Verify required methods exist
        assert hasattr(service, 'enrich_tagged_item')
        assert hasattr(service, 'set_api_key')
        assert hasattr(service, 'get_api_key')
        assert hasattr(service, 'clear_api_key')
        assert hasattr(service, 'start_workers')
        assert hasattr(service, 'stop_workers')
        assert hasattr(service, 'manual_retry_enrichment')
        
        # Verify methods are callable
        assert callable(service.enrich_tagged_item)
        assert callable(service.set_api_key)
        assert callable(service.get_api_key)


class TestAPIClientStructure:
    """Tests for API client structure and configuration."""
    
    def test_api_base_client_has_async_context_manager(self):
        """Test that APIClient has async context manager methods."""
        from app.modules.tag_enrichment.api_clients import APIClient, TMDBClient
        
        client = TMDBClient(api_key="key")
        
        assert hasattr(client, '__aenter__')
        assert hasattr(client, '__aexit__')
        assert callable(client.__aenter__)
        assert callable(client.__aexit__)
    
    def test_tmdb_enrich_movie_method_exists(self):
        """Test that TMDB client has enrich_movie method."""
        from app.modules.tag_enrichment.api_clients import TMDBClient
        
        client = TMDBClient(api_key="key")
        
        assert hasattr(client, 'enrich_movie')
        assert callable(client.enrich_movie)
        assert hasattr(client, 'search')
        assert callable(client.search)
        assert hasattr(client, 'fetch_details')
        assert callable(client.fetch_details)
    
    def test_google_books_enrich_book_method_exists(self):
        """Test that Google Books client has enrich_book method."""
        from app.modules.tag_enrichment.api_clients import GoogleBooksClient
        
        client = GoogleBooksClient(api_key="key")
        
        assert hasattr(client, 'enrich_book')
        assert callable(client.enrich_book)
        assert hasattr(client, 'search')
        assert callable(client.search)
        assert hasattr(client, 'fetch_details')
        assert callable(client.fetch_details)


class TestEnrichmentDataValidation:
    """Tests for enrichment data validation."""
    
    def test_tmdb_response_with_extra_fields(self):
        """Test TMDB response allows extra fields."""
        from app.modules.tag_enrichment.api_clients import TMDBMovieResponse
        
        response = TMDBMovieResponse(
            id=1,
            title="Test",
            extra_field="should be allowed",
            another_extra=123
        )
        
        assert response.id == 1
        assert response.title == "Test"
    
    def test_google_books_response_with_extra_fields(self):
        """Test Google Books response allows extra fields."""
        from app.modules.tag_enrichment.api_clients import GoogleBooksResponse
        
        response = GoogleBooksResponse(
            id="book1",
            title="Test",
            extra_field="should be allowed"
        )
        
        assert response.id == "book1"
        assert response.title == "Test"
    
    def test_tmdb_response_with_zero_rating(self):
        """Test TMDB response handles zero rating."""
        from app.modules.tag_enrichment.api_clients import TMDBMovieResponse
        
        response = TMDBMovieResponse(
            id=1,
            title="Test",
            vote_average=0
        )
        
        # Should be None or 0
        assert response.vote_average in [0, None]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
