"""
Custom exceptions for the RivalSearch Agent with retry capabilities.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone


class RivalSearchError(Exception):
    """Base exception for RivalSearch Agent errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc)


class RetryableError(RivalSearchError):
    """Exception that indicates an operation should be retried."""
    
    def __init__(
        self, 
        message: str, 
        retry_after: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.retry_after = retry_after  # Seconds to wait before retry


class MCPConnectionError(RetryableError):
    """Error connecting to MCP server."""
    pass


class AgentInitializationError(RivalSearchError):
    """Error during agent initialization."""
    pass


class MCPTimeoutError(RetryableError):
    """MCP server request timeout."""
    pass


class ToolExecutionError(RetryableError):
    """Error during tool execution."""
    
    def __init__(
        self, 
        message: str, 
        tool_name: str,
        retry_after: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, retry_after, details)
        self.tool_name = tool_name


class StreamingError(RetryableError):
    """Error during streaming operations."""
    pass


class ConfigurationError(RivalSearchError):
    """Non-retryable configuration error."""
    pass


class ValidationError(RivalSearchError):
    """Non-retryable validation error."""
    pass


class RateLimitError(RetryableError):
    """Rate limit exceeded - should retry with backoff."""
    
    def __init__(
        self, 
        message: str, 
        retry_after: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, retry_after, details)
        # Default retry_after for rate limits if not specified
        if self.retry_after is None:
            self.retry_after = 60.0  # 1 minute default