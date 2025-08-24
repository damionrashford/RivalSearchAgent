"""
Retry handler with exponential backoff for RivalSearch Agent.
"""

import asyncio
import random
from typing import Callable, TypeVar, Optional
from functools import wraps

from pydantic_ai import ModelRetry

from .exceptions import (
    RetryableError, MCPConnectionError, MCPTimeoutError, 
    ToolExecutionError, StreamingError, RateLimitError
)
from .config import AgentConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class RetryHandler:
    """Handles retry logic with exponential backoff and jitter."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.retryable_exceptions = (
            RetryableError,
            MCPConnectionError, 
            MCPTimeoutError,
            ToolExecutionError,
            StreamingError,
            RateLimitError,
            ConnectionError,
            TimeoutError,
            # Add common HTTP errors
            Exception  # We'll filter this more specifically in _is_retryable
        )
    
    def _is_retryable(self, exception: Exception) -> bool:
        """Check if an exception should trigger a retry."""
        if isinstance(exception, RetryableError):
            return True
        
        # Check common HTTP/network errors
        error_msg = str(exception).lower()
        retryable_patterns = [
            'timeout', 'connection', 'network', 'temporary', 
            'service unavailable', '502', '503', '504',
            'rate limit', 'too many requests'
        ]
        
        return any(pattern in error_msg for pattern in retryable_patterns)
    
    def _calculate_delay(
        self, 
        attempt: int, 
        retry_after: Optional[float] = None
    ) -> float:
        """Calculate retry delay with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number (1-based)
            retry_after: Specific delay requested (e.g., from Retry-After header)
            
        Returns:
            Delay in seconds
        """
        if retry_after is not None:
            return min(retry_after, self.config.max_retry_delay)
        
        # Exponential backoff: delay = base_delay * (backoff_factor ^ (attempt - 1))
        base_delay = self.config.retry_delay
        backoff_factor = self.config.retry_backoff_factor
        
        delay = base_delay * (backoff_factor ** (attempt - 1))
        
        # Add jitter (±25% of the delay)
        jitter_range = delay * 0.25
        jitter = random.uniform(-jitter_range, jitter_range)
        delay += jitter
        
        # Cap at maximum delay
        delay = min(delay, self.config.max_retry_delay)
        
        return max(0, delay)
    
    async def retry_async(
        self,
        func: Callable[..., T],
        *args,
        max_retries: Optional[int] = None,
        operation_name: str = "operation",
        **kwargs
    ) -> T:
        """Retry an async function with exponential backoff.
        
        Args:
            func: Async function to retry
            *args: Arguments to pass to func
            max_retries: Override default max retries
            operation_name: Name for logging
            **kwargs: Keyword arguments to pass to func
            
        Returns:
            Result from successful function call
            
        Raises:
            Last exception if all retries exhausted
        """
        max_attempts = (max_retries or self.config.max_retries) + 1
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(f"Attempting {operation_name} (attempt {attempt}/{max_attempts})")
                result = await func(*args, **kwargs)
                
                if attempt > 1:
                    logger.info(f"{operation_name} succeeded on attempt {attempt}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self._is_retryable(e):
                    logger.warning(f"{operation_name} failed with non-retryable error: {e}")
                    raise
                
                if attempt >= max_attempts:
                    logger.error(f"{operation_name} failed after {attempt} attempts: {e}")
                    raise
                
                # Calculate delay
                retry_after = getattr(e, 'retry_after', None)
                delay = self._calculate_delay(attempt, retry_after)
                
                logger.warning(
                    f"{operation_name} failed on attempt {attempt}/{max_attempts}: {e}. "
                    f"Retrying in {delay:.2f}s"
                )
                
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        raise last_exception or Exception(f"{operation_name} failed after all retries")
    
    def retry_sync(
        self,
        func: Callable[..., T],
        *args,
        max_retries: Optional[int] = None,
        operation_name: str = "operation",
        **kwargs
    ) -> T:
        """Retry a sync function with exponential backoff.
        
        Args:
            func: Function to retry
            *args: Arguments to pass to func
            max_retries: Override default max retries
            operation_name: Name for logging
            **kwargs: Keyword arguments to pass to func
            
        Returns:
            Result from successful function call
            
        Raises:
            Last exception if all retries exhausted
        """
        max_attempts = (max_retries or self.config.max_retries) + 1
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(f"Attempting {operation_name} (attempt {attempt}/{max_attempts})")
                result = func(*args, **kwargs)
                
                if attempt > 1:
                    logger.info(f"{operation_name} succeeded on attempt {attempt}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self._is_retryable(e):
                    logger.warning(f"{operation_name} failed with non-retryable error: {e}")
                    raise
                
                if attempt >= max_attempts:
                    logger.error(f"{operation_name} failed after {attempt} attempts: {e}")
                    raise
                
                # Calculate delay
                retry_after = getattr(e, 'retry_after', None)
                delay = self._calculate_delay(attempt, retry_after)
                
                logger.warning(
                    f"{operation_name} failed on attempt {attempt}/{max_attempts}: {e}. "
                    f"Retrying in {delay:.2f}s"
                )
                
                import time
                time.sleep(delay)
        
        # This should never be reached, but just in case
        raise last_exception or Exception(f"{operation_name} failed after all retries")


def with_retry(
    max_retries: Optional[int] = None,
    operation_name: Optional[str] = None
):
    """Decorator to add retry logic to async functions.
    
    Args:
        max_retries: Override default max retries
        operation_name: Name for logging (defaults to function name)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> T:
            # Extract retry handler from self (assumes it's an agent or service)
            retry_handler = getattr(self, '_retry_handler', None)
            if not retry_handler:
                # Fallback: call function directly if no retry handler
                return await func(self, *args, **kwargs)
            
            name = operation_name or func.__name__
            return await retry_handler.retry_async(
                func, self, *args,
                max_retries=max_retries,
                operation_name=name,
                **kwargs
            )
        
        return wrapper
    return decorator


def convert_to_model_retry(exception: Exception) -> ModelRetry:
    """Convert custom exceptions to Pydantic AI ModelRetry for tool compatibility.
    
    Args:
        exception: Exception to convert
        
    Returns:
        ModelRetry exception for Pydantic AI
    """
    if isinstance(exception, ToolExecutionError):
        return ModelRetry(f"Tool '{exception.tool_name}' failed: {exception.message}")
    elif isinstance(exception, RetryableError):
        return ModelRetry(exception.message)
    else:
        return ModelRetry(f"Retryable error: {str(exception)}")