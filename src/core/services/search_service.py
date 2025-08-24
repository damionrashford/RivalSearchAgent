"""
Search service for the RivalSearch Agent.

Provides business logic and caching for search operations.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from collections import OrderedDict

from ..agent import RivalSearchAgent
from ..models.schemas import SearchRequest, SearchResponse
from ..utils.logging import get_logger
from ..utils.validation import validate_query, sanitize_query

logger = get_logger(__name__)


class SearchService:
    """Service for managing search operations with caching and optimization."""
    
    def __init__(self, agent: RivalSearchAgent, cache_size: int = 100, cache_ttl: int = 3600):
        """Initialize the search service.
        
        Args:
            agent: RivalSearch Agent instance
            cache_size: Maximum number of cached results
            cache_ttl: Cache time-to-live in seconds
        """
        self.agent = agent
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        
        logger.info(f"Search service initialized with cache size {cache_size} and TTL {cache_ttl}s")
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Perform a search with caching and optimization.
        
        Args:
            request: Search request parameters
            
        Returns:
            Search results
        """
        try:
            # Validate and sanitize query
            sanitized_query = sanitize_query(request.query)
            if not validate_query(sanitized_query):
                return SearchResponse(
                    success=False,
                    results=[],
                    total_results=0,
                    query=request.query,
                    error="Invalid query format"
                )
            
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = self._get_from_cache(cache_key)
            
            if cached_result:
                logger.info(f"Returning cached result for query: {sanitized_query}")
                return cached_result
            
            # Perform search
            logger.info(f"Performing search for: {sanitized_query}")
            response = await self.agent.search(request)
            
            # Cache successful results
            if response.success:
                self._add_to_cache(cache_key, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Search service error: {e}")
            return SearchResponse(
                success=False,
                results=[],
                total_results=0,
                query=request.query,
                error=str(e)
            )
    
    async def batch_search(self, requests: List[SearchRequest]) -> List[SearchResponse]:
        """Perform multiple searches concurrently.
        
        Args:
            requests: List of search requests
            
        Returns:
            List of search responses
        """
        try:
            logger.info(f"Performing batch search with {len(requests)} requests")
            
            # Create tasks for concurrent execution
            tasks = [self.search(request) for request in requests]
            
            # Execute concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            processed_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.error(f"Batch search error for request {i}: {response}")
                    processed_responses.append(SearchResponse(
                        success=False,
                        results=[],
                        total_results=0,
                        query=requests[i].query,
                        error=str(response)
                    ))
                else:
                    processed_responses.append(response)
            
            return processed_responses
            
        except Exception as e:
            logger.error(f"Batch search service error: {e}")
            return [
                SearchResponse(
                    success=False,
                    results=[],
                    total_results=0,
                    query=req.query,
                    error=str(e)
                )
                for req in requests
            ]
    
    async def search_with_fallback(self, request: SearchRequest) -> SearchResponse:
        """Perform search with fallback strategies.
        
        Args:
            request: Search request parameters
            
        Returns:
            Search results with fallback handling
        """
        try:
            # Try original search
            response = await self.search(request)
            
            if response.success and response.results:
                return response
            
            # Fallback: try with different parameters
            logger.info(f"Original search failed, trying fallback for: {request.query}")
            
            fallback_request = SearchRequest(
                query=request.query,
                num_results=min(request.num_results * 2, 20),
                lang=request.lang,
                region=request.region,
                safe="off"  # Try without safe search
            )
            
            fallback_response = await self.search(fallback_request)
            
            if fallback_response.success and fallback_response.results:
                logger.info("Fallback search successful")
                return fallback_response
            
            # Final fallback: return original response with error info
            return response
            
        except Exception as e:
            logger.error(f"Search with fallback error: {e}")
            return SearchResponse(
                success=False,
                results=[],
                total_results=0,
                query=request.query,
                error=f"Search failed with fallback: {str(e)}"
            )
    
    def _generate_cache_key(self, request: SearchRequest) -> str:
        """Generate a cache key for the search request.
        
        Args:
            request: Search request
            
        Returns:
            Cache key string
        """
        # Create a deterministic cache key
        key_parts = [
            request.query.lower().strip(),
            str(request.num_results),
            request.lang,
            request.safe,
            request.region or "default"
        ]
        return "|".join(key_parts)
    
    def _get_from_cache(self, cache_key: str) -> Optional[SearchResponse]:
        """Get a result from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached response if valid, None otherwise
        """
        if cache_key not in self._cache:
            return None
        
        cached_item = self._cache[cache_key]
        
        # Check if cache entry is expired
        if datetime.now(timezone.utc) > cached_item['expires_at']:
            del self._cache[cache_key]
            return None
        
        # Move to end (LRU)
        self._cache.move_to_end(cache_key)
        
        logger.debug(f"Cache hit for key: {cache_key}")
        return cached_item['response']
    
    def _add_to_cache(self, cache_key: str, response: SearchResponse) -> None:
        """Add a result to cache.
        
        Args:
            cache_key: Cache key
            response: Search response to cache
        """
        # Remove oldest entry if cache is full
        if len(self._cache) >= self.cache_size:
            self._cache.popitem(last=False)
        
        # Add new entry
        self._cache[cache_key] = {
            'response': response,
            'expires_at': datetime.now(timezone.utc) + timedelta(seconds=self.cache_ttl),
            'created_at': datetime.now(timezone.utc)
        }
        
        logger.debug(f"Cached result for key: {cache_key}")
    
    def clear_cache(self) -> None:
        """Clear the search cache."""
        self._cache.clear()
        logger.info("Search cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics dictionary
        """
        now = datetime.now(timezone.utc)
        valid_entries = sum(
            1 for item in self._cache.values()
            if now <= item['expires_at']
        )
        
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self._cache) - valid_entries,
            'cache_size': self.cache_size,
            'cache_ttl': self.cache_ttl
        }
