"""
RivalSearch Agent using Pydantic AI with MCP integration.

This module provides a RivalSearch Agent that connects to external MCP servers
and provides enhanced frontend integration through standard Pydantic AI.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.providers.grok import GrokProvider
from pydantic_ai.providers.ollama import OllamaProvider

from .config import AgentConfig
from .exceptions import AgentInitializationError

# Add RivalSearchMCP to Python path for import resolution
rival_search_mcp_path = Path(__file__).parent.parent.parent / "src" / "RivalSearchMCP" / "src"
if str(rival_search_mcp_path) not in sys.path:
    sys.path.insert(0, str(rival_search_mcp_path))

logger = logging.getLogger(__name__)


class RivalSearchState(BaseModel):
    """State model for RivalSearch Agent sessions."""
    
    session_id: str = Field(default="", description="Session identifier")
    thread_id: str = Field(default="", description="Thread ID")
    last_activity: str = Field(default="", description="Last activity timestamp")
    tool_status: Dict[str, str] = Field(default_factory=dict, description="Tool status tracking")


class RivalSearchAgent:
    """RivalSearch Agent using Pydantic AI with MCP integration."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the RivalSearch Agent with configuration."""
        self.config = config
        self._agent: Optional[Agent] = None
        self._mcp_server: Optional[MCPServerStdio] = None
        self._connected = False
        
        logger.info(f"Initializing RivalSearch Agent with MCP server: {config.mcp_server_path}")
    
    def _create_model(self):
        """Create the appropriate model based on the provider configuration."""
        provider = self.config.model_name.split(':')[0] if ':' in self.config.model_name else 'grok'
        model_name = self.config.model_name.split(':')[1] if ':' in self.config.model_name else self.config.model_name
        
        if provider == 'openai':
            provider_instance = OpenAIProvider(api_key=self.config.openai_api_key)
            return OpenAIModel(model_name, provider=provider_instance)
        
        elif provider == 'anthropic':
            provider_instance = AnthropicProvider(api_key=self.config.anthropic_api_key)
            return AnthropicModel(model_name, provider=provider_instance)
        
        elif provider in ['google-gla', 'google-vertex']:
            if self.config.google_vertex_ai or provider == 'google-vertex':
                # Use Vertex AI
                provider_instance = GoogleProvider(
                    vertexai=True,
                    project=self.config.google_cloud_project,
                    location=self.config.google_cloud_location
                )
            else:
                # Use Generative Language API
                provider_instance = GoogleProvider(api_key=self.config.google_api_key)
            return GoogleModel(model_name, provider=provider_instance)
        
        elif provider == 'grok':
            provider_instance = GrokProvider(api_key=self.config.grok_api_key)
            return OpenAIModel(model_name, provider=provider_instance)
        
        elif provider == 'deepseek':
            provider_instance = DeepSeekProvider(api_key=self.config.deepseek_api_key)
            return OpenAIModel(model_name, provider=provider_instance)
        
        elif provider == 'ollama':
            provider_instance = OllamaProvider(base_url=self.config.ollama_base_url)
            return OpenAIModel(model_name, provider=provider_instance)
        
        else:
            # Fallback to simple model name format for backward compatibility
            return self.config.model_name

    async def initialize(self):
        """Initialize the Pydantic AI Agent with MCP integration."""
        try:
            # Validate provider configuration first
            self.config.validate_provider_configuration()
            
            # Create MCP server using STDIO transport for local integration
            self._mcp_server = MCPServerStdio(
                command='python',
                args=['server.py'],  # Just the filename since cwd is set to the src directory
                cwd=str(rival_search_mcp_path),  # Use RivalSearchMCP src directory
                env=None  # Inherit environment variables
            )
            
            # Create the appropriate model based on provider
            model = self._create_model()
            
            # Create the agent with MCP server as a toolset
            self._agent = Agent(
                model=model,
                instructions=self.config.instructions,
                toolsets=[self._mcp_server]
            )
            
            # Register custom tools
            self._register_tools()
            
            # Mark as connected (connection will be established when needed)
            self._connected = True
            
            logger.info(f"RivalSearch Agent initialized successfully with model: {self.config.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize RivalSearch Agent: {e}")
            raise AgentInitializationError(f"Agent initialization failed: {e}")
    
    async def _ensure_connection(self):
        """Ensure MCP server is connected via async context manager."""
        if not hasattr(self, '_agent_context'):
            self._agent_context = self._agent.__aenter__()
            await self._agent_context
    
    def _register_tools(self):
        """No custom tools - agent only uses MCP server tools."""
        # The agent should only have access to tools provided by the MCP server
        # No custom tools should be registered
        pass
    async def run(self, user_input: str, session_id: str = "", thread_id: str = "") -> str:
        """Run the agent with user input and return response."""
        if not self._agent:
            raise AgentInitializationError("Agent not initialized")
        
        try:
            # Ensure MCP server is connected
            await self._ensure_connection()
            
            # Initialize memory service if database URL is available
            memory_service = None
            if hasattr(self.config, 'database_url') and self.config.database_url:
                from .services.memory_service import CompleteMemoryService
                memory_service = CompleteMemoryService(self.config.database_url)
                
                # Create session if it doesn't exist
                if session_id:
                    await memory_service.create_session(session_id)
                
                # Get complete conversation history
                message_history = await memory_service.get_conversation_as_pydantic_messages(session_id)
                
                # Add user message to history
                await memory_service.add_message(session_id, 'user', user_input)
            else:
                message_history = []
            
            # Create state context
            state = RivalSearchState(
                session_id=session_id,
                thread_id=thread_id,
                last_activity=datetime.now(timezone.utc).isoformat()
            )
            
            # Run the agent with complete conversation history
            result = await self._agent.run(user_input, deps=state, message_history=message_history)
            
            # Store assistant response in memory
            if memory_service and session_id:
                await memory_service.add_message(session_id, 'assistant', result.output)
            
            return result.output
                
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            raise
    
    async def run_stream(self, user_input: str, session_id: str = "", thread_id: str = ""):
        """Run the agent with streaming response."""
        if not self._agent:
            raise AgentInitializationError("Agent not initialized")
        
        try:
            # Ensure MCP server is connected
            await self._ensure_connection()
            
            # Initialize memory service if database URL is available
            memory_service = None
            if hasattr(self.config, 'database_url') and self.config.database_url:
                from .services.memory_service import CompleteMemoryService
                memory_service = CompleteMemoryService(self.config.database_url)
                
                # Create session if it doesn't exist
                if session_id:
                    await memory_service.create_session(session_id)
                
                # Get complete conversation history FOR THIS SESSION ONLY
                message_history = await memory_service.get_conversation_as_pydantic_messages(session_id)
                
                # Add user message to history
                await memory_service.add_message(session_id, 'user', user_input)
            else:
                message_history = []
            
            # Create state context
            state = RivalSearchState(
                session_id=session_id,
                thread_id=thread_id,
                last_activity=datetime.now(timezone.utc).isoformat()
            )
            
            # Run the agent with streaming and SESSION-ISOLATED message history
            full_response = ""
            async with self._agent.run_stream(user_input, deps=state, message_history=message_history) as response:
                async for text in response.stream_text():
                    full_response += text
                    yield text
            
            # Store assistant response in memory
            if memory_service and session_id:
                await memory_service.add_message(session_id, 'assistant', full_response)
                
        except Exception as e:
            logger.error(f"Error running agent stream: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self._mcp_server:
            # The MCP server connection will be managed by Pydantic AI
            self._connected = False
    
    @property
    def agent(self) -> Agent:
        """Get the underlying Pydantic AI agent."""
        return self._agent
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to MCP server."""
        return self._connected
