"""
RivalSearch Agent - Modular AI agent with RAG capabilities.

A powerful, embeddable AI agent that can be used as:
- CLI tool for direct interaction
- API server for HTTP integration  
- Python library for embedding in other systems
"""

from .core.agent import RivalSearchAgent
from .core.config import AgentConfig
from .core.exceptions import AgentInitializationError

__version__ = "1.0.0"
__author__ = "RivalSearch Team"

# Main exports
__all__ = [
    "RivalSearchAgent",
    "AgentConfig", 
    "AgentInitializationError"
]
