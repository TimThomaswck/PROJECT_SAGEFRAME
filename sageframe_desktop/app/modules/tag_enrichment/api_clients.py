"""API client wrappers for external enrichment services.

This module provides async wrappers for TMDB and Google Books APIs,
with built-in retry logic, rate limiting, and error handling.

Clients automatically:
- Retry with exponential backoff (1s, 2s, 4s)
- Validate API responses with Pydantic
- Include proper error handling and logging
- Respect rate limits
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import aiohttp
from pydantic import BaseModel, Field, field_validator, ConfigDict

logger = logging.getLogger(__name__)


class TMDBMovieResponse(BaseModel):
    """Pydantic model for TMDB movie search response."""
    
    model_config = ConfigDict(extra="allow")
    
    id: int
    title: str
    overview: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    genres: List[Dict[str, Any]] = Field(default_factory=list)
    runtime: Optional[int] = None
    director: Optional[str] = None
    cast: Optional[List[str]] = None
    
    @field_validator('vote_average', mode='before')
    @classmethod
    def validate_rating(cls, v):
        """Normalize rating to 0-10 scale."""
        if v is not None and v > 0:
            return round(v, 1)
        return v


class GoogleBooksResponse(BaseModel):
    """Pydantic model for Google Books API response."""
    
    model_config = ConfigDict(extra="allow")
    
    id: str
    title: str
    subtitle: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    description: Optional[str] = None
    isbn_10: Optional[str] = None
    isbn_13: Optional[str] = None
    page_count: Optional[int] = None
    average_rating: Optional[float] = None
    rating_count: Optional[int] = None
    image_url: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    
    @field_validator('average_rating', mode='before')
    @classmethod
    def validate_rating(cls, v):
        """Normalize rating to 0-5 scale."""
        if v is not None and v > 0:
            return round(v, 1)
        return v


class APIClient(ABC):
    """Abstract base class for API clients."""
    
    def __init__(self, api_key: str, timeout: int = 10, max_retries: int = 3):
        """Initialize API client.
        
        Args:
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts (total 3 = 1s, 2s, 4s)
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = ""
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def search(self, query: str) -> Optional[Dict[str, Any]]:
        """Search for content using the API."""
        pass
    
    @abstractmethod
    async def fetch_details(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed metadata for a result."""
        pass
    
    async def _request_with_retry(
        self, 
        method: str, 
        url: str, 
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request with exponential backoff retry logic.
        
        Args:
            method: HTTP method (GET, POST)
            url: Request URL
            params: Query parameters
            headers: Request headers
        
        Returns:
            JSON response or None if all retries failed
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        retry_delays = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.request(
                    method, 
                    url, 
                    params=params, 
                    headers=headers
                ) as response:
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', retry_delays[attempt]))
                        logger.warning(f"Rate limited. Waiting {retry_after}s before retry.")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # Handle authentication errors
                    if response.status == 401:
                        logger.error("Authentication failed. Check API key.")
                        return None
                    
                    # Handle server errors with retry
                    if response.status >= 500:
                        if attempt < self.max_retries - 1:
                            delay = retry_delays[attempt]
                            logger.warning(f"Server error {response.status}. Retrying in {delay}s...")
                            await asyncio.sleep(delay)
                            continue
                        return None
                    
                    # Handle client errors (no retry)
                    if response.status >= 400:
                        logger.error(f"Client error {response.status}: {response.reason}")
                        return None
                    
                    # Success
                    return await response.json()
            
            except asyncio.TimeoutError:
                last_error = "Request timeout"
                if attempt < self.max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning(f"Timeout. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
            
            except aiohttp.ClientError as e:
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning(f"Connection error: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
            
            except Exception as e:
                logger.error(f"Unexpected error during request: {e}")
                return None
        
        logger.error(f"All {self.max_retries} retry attempts failed. Last error: {last_error}")
        return None


class TMDBClient(APIClient):
    """TMDB (The Movie Database) API client.
    
    Provides movie search and detail fetching with automatic retry logic.
    Free tier: 40 requests per 10 seconds
    """
    
    def __init__(self, api_key: str, timeout: int = 10, max_retries: int = 3):
        """Initialize TMDB client.
        
        Args:
            api_key: TMDB API key (get from https://www.themoviedb.org/settings/api)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(api_key, timeout, max_retries)
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w200"
    
    async def search(self, query: str) -> Optional[Dict[str, Any]]:
        """Search for a movie by title.
        
        Args:
            query: Movie title to search for
        
        Returns:
            First search result or None if not found
        """
        url = f"{self.base_url}/search/movie"
        params = {
            "api_key": self.api_key,
            "query": query,
            "page": "1"
        }
        
        response = await self._request_with_retry("GET", url, params=params)
        if response and response.get("results"):
            return response["results"][0]
        return None
    
    async def fetch_details(self, movie_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed movie information.
        
        Args:
            movie_id: TMDB movie ID
        
        Returns:
            Movie details or None if fetch failed
        """
        url = f"{self.base_url}/movie/{movie_id}"
        params = {
            "api_key": self.api_key,
            "append_to_response": "credits"
        }
        
        response = await self._request_with_retry("GET", url, params=params)
        return response
    
    async def enrich_movie(self, title: str) -> Optional[Dict[str, Any]]:
        """Search and enrich movie data (convenience method).
        
        Args:
            title: Movie title
        
        Returns:
            Enriched movie data or None
        """
        # Search for movie
        search_result = await self.search(title)
        if not search_result:
            logger.warning(f"Movie not found: {title}")
            return None
        
        movie_id = search_result.get("id")
        if not movie_id:
            return None
        
        # Fetch detailed information
        details = await self.fetch_details(str(movie_id))
        if not details:
            return None
        
        # Extract director and cast from credits
        director = None
        cast = []
        
        if "credits" in details:
            crew = details["credits"].get("crew", [])
            directors = [c for c in crew if c.get("job") == "Director"]
            if directors:
                director = directors[0].get("name")
            
            cast_list = details["credits"].get("cast", [])
            cast = [c.get("name") for c in cast_list[:5]]  # Top 5 cast members
        
        # Build enrichment data
        enrichment = {
            "id": details.get("id"),
            "title": details.get("title"),
            "overview": details.get("overview"),
            "release_date": details.get("release_date"),
            "rating": details.get("vote_average"),
            "vote_count": details.get("vote_count"),
            "runtime": details.get("runtime"),
            "director": director,
            "cast": cast,
            "genres": [g.get("name") for g in details.get("genres", [])],
            "poster_url": f"{self.image_base_url}{details['poster_path']}" if details.get("poster_path") else None,
            "tmdb_url": f"https://www.themoviedb.org/movie/{movie_id}",
            "api_provider": "tmdb",
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            TMDBMovieResponse(**enrichment)
            return enrichment
        except ValidationError as e:
            logger.error(f"Validation error for movie enrichment: {e}")
            return None


class GoogleBooksClient(APIClient):
    """Google Books API client.
    
    Provides book search and detail fetching.
    Free tier: 1000 requests per day
    """
    
    def __init__(self, api_key: str, timeout: int = 10, max_retries: int = 3):
        """Initialize Google Books client.
        
        Args:
            api_key: Google Books API key
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(api_key, timeout, max_retries)
        self.base_url = "https://www.googleapis.com/books/v1"
    
    async def search(self, query: str) -> Optional[Dict[str, Any]]:
        """Search for a book by title or ISBN.
        
        Args:
            query: Book title or ISBN
        
        Returns:
            First search result or None if not found
        """
        url = f"{self.base_url}/volumes"
        params = {
            "q": query,
            "key": self.api_key,
            "maxResults": "1"
        }
        
        response = await self._request_with_retry("GET", url, params=params)
        if response and response.get("items"):
            return response["items"][0]
        return None
    
    async def fetch_details(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed book information.
        
        Args:
            book_id: Google Books ID
        
        Returns:
            Book details or None if fetch failed
        """
        url = f"{self.base_url}/volumes/{book_id}"
        params = {"key": self.api_key}
        
        response = await self._request_with_retry("GET", url, params=params)
        return response
    
    async def enrich_book(self, title: str) -> Optional[Dict[str, Any]]:
        """Search and enrich book data (convenience method).
        
        Args:
            title: Book title
        
        Returns:
            Enriched book data or None
        """
        # Search for book
        search_result = await self.search(title)
        if not search_result:
            logger.warning(f"Book not found: {title}")
            return None
        
        book_id = search_result.get("id")
        if not book_id:
            return None
        
        # Extract volume info
        volume_info = search_result.get("volumeInfo", {})
        
        # Extract ISBNs
        isbn_10 = None
        isbn_13 = None
        for identifier in volume_info.get("industryIdentifiers", []):
            if identifier.get("type") == "ISBN_10":
                isbn_10 = identifier.get("identifier")
            elif identifier.get("type") == "ISBN_13":
                isbn_13 = identifier.get("identifier")
        
        # Get cover image
        image_url = None
        if "imageLinks" in volume_info:
            image_url = volume_info["imageLinks"].get("thumbnail")
        
        # Build enrichment data
        enrichment = {
            "id": book_id,
            "title": volume_info.get("title"),
            "subtitle": volume_info.get("subtitle"),
            "authors": volume_info.get("authors", []),
            "publisher": volume_info.get("publisher"),
            "published_date": volume_info.get("publishedDate"),
            "description": volume_info.get("description"),
            "isbn_10": isbn_10,
            "isbn_13": isbn_13,
            "page_count": volume_info.get("pageCount"),
            "categories": volume_info.get("categories", []),
            "average_rating": volume_info.get("averageRating"),
            "rating_count": volume_info.get("ratingsCount"),
            "image_url": image_url,
            "google_books_url": volume_info.get("previewLink"),
            "api_provider": "google_books",
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            GoogleBooksResponse(**enrichment)
            return enrichment
        except ValidationError as e:
            logger.error(f"Validation error for book enrichment: {e}")
            return None
