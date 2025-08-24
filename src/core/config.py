"""
Configuration management for the RivalSearch Agent.

Handles environment variables, settings validation, and configuration defaults.
Supports multiple LLM providers through environment variable configuration.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AgentConfig(BaseModel):
    """Configuration for the RivalSearch Agent with multi-provider support."""
    
    model_config = ConfigDict(
        env_prefix="RIVAL_SEARCH_",
        case_sensitive=False,
        validate_assignment=True,
        extra="ignore"
    )
    
    # MCP Server Configuration (STDIO Transport)
    # Using local STDIO transport - no URL needed
    mcp_server_path: str = Field(
        default="RivalSearchMCP/src/server.py",
        description="Path to the local MCP server script"
    )
    
    mcp_timeout: float = Field(
        default=30.0,
        description="Timeout for MCP server requests in seconds"
    )
    
    # Model Configuration - Supports the 6 specified providers
    model_name: str = Field(
        default="grok:grok-3-mini",
        description="Name of the model to use (format: provider:model)"
    )
    
    # Provider-specific API keys and configuration
    # OpenAI
    openai_api_key: Optional[str] = Field(
        default=None,
        description="API key for OpenAI models"
    )
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="API key for Anthropic models"
    )
    
    # Google (Gemini)
    google_api_key: Optional[str] = Field(
        default=None,
        description="API key for Google Gemini models"
    )
    google_vertex_ai: bool = Field(
        default=False,
        description="Whether to use Google Vertex AI instead of Generative Language API"
    )
    google_cloud_project: Optional[str] = Field(
        default=None,
        description="Google Cloud project ID for Vertex AI"
    )
    google_cloud_location: Optional[str] = Field(
        default=None,
        description="Google Cloud location for Vertex AI (e.g., us-central1)"
    )
    
    # Grok (xAI)
    grok_api_key: Optional[str] = Field(
        default=None,
        description="API key for Grok models"
    )
    
    # DeepSeek
    deepseek_api_key: Optional[str] = Field(
        default=None,
        description="API key for DeepSeek models"
    )
    
    # Ollama
    ollama_base_url: Optional[str] = Field(
        default="http://localhost:11434/v1",
        description="Base URL for Ollama server"
    )
    
    # Database Configuration
    database_url: Optional[str] = Field(
        default=None,
        description="Database URL for conversation memory storage"
    )

    # Agent Instructions
    instructions: str = Field(
        default="""<instructions>
You are the RivalSearch Agent, a specialized research and analysis assistant with access to powerful MCP server tools and RAG (Retrieval-Augmented Generation) capabilities.

## Available Tools and Usage Guidelines:

### RAG (Retrieval-Augmented Generation) Tools:
- **search_documents_tool**: Search through uploaded documents for relevant information
  - Use for: Finding specific information, answering questions about uploaded content, retrieving context from documents
  - Guidelines: Use when users ask about uploaded documents or when you need to reference specific content from their files
  - Parameters: query (search term), session_id (current session)

- **list_documents_tool**: List all documents uploaded in the current session
  - Use for: Understanding what documents are available, providing overview of uploaded content
  - Guidelines: Use to inform users about available documents or when they ask what files they've uploaded
  - Parameters: session_id (current session)

- **delete_documents_tool**: Remove documents from the current session
  - Use for: Cleaning up uploaded documents, removing outdated or irrelevant files
  - Guidelines: Use when users want to remove specific documents or clear their session
  - Parameters: session_id (current session), file_name (optional, specific file to delete)

### Content Retrieval Tools:
- **retrieve_content**: Enhanced content retrieval with support for single/multiple resources and image extraction
  - Use for: Extracting comprehensive information from URLs, documents, or multiple resources
  - Guidelines: Focus on accuracy, completeness, and well-structured content without HTML
  - Parameters: resource (URL/string), limit (default 5), extract_images (default False)

- **stream_content**: Real-time streaming content retrieval
  - Use for: Monitoring live data streams and extracting real-time insights
  - Guidelines: Monitor streams for relevant information, extract key data points and patterns
  - Parameters: url (streaming source)

### Website Analysis Tools:
- **traverse_website**: Comprehensive website exploration and analysis
  - Use for: Systematic website exploration in research, documentation, or mapping modes
  - Guidelines: Explore systematically, extract key information from multiple pages, provide structured analysis
  - Parameters: url, mode (research/docs/map), max_pages (default 5)

### Search Tools:
- **google_search**: Comprehensive Google search with result analysis
  - Use for: Finding relevant information, analyzing search result quality and patterns
  - Guidelines: Analyze relevance, extract key information, identify patterns in results and metadata
  - Parameters: query, num_results (default 10)

### Analysis Tools:
- **analyze_content**: Content analysis with multiple analysis types
  - Use for: Extracting insights from content using general, sentiment, technical, or business analysis
  - Guidelines: Extract key insights, provide structured analysis, generate actionable recommendations
  - Parameters: content, analysis_type (general/sentiment/technical/business)

- **research_topic**: End-to-end research workflow
  - Use for: Comprehensive topic research with search, retrieval, analysis, and synthesis
  - Guidelines: Execute complete research workflow, provide structured results with actionable insights
  - Parameters: topic, max_sources (default 5)

## RAG Usage Guidelines:
1. **When to use RAG tools**: Use RAG tools when users ask questions about uploaded documents or when you need to reference specific content from their files
2. **Document search strategy**: Use search_documents_tool with specific, targeted queries to find the most relevant information
3. **Context integration**: When you find relevant document content, integrate it naturally into your responses while maintaining accuracy
4. **Document management**: Help users manage their uploaded documents by using list_documents_tool and delete_documents_tool when appropriate
5. **Citation**: When referencing document content, mention the source document and provide context about where the information came from

## Core Principles:
1. Always use the appropriate tools for research and analysis tasks
2. Prioritize RAG tools when users ask about uploaded documents
3. Follow the specific guidelines for each tool when using them
4. Be direct, accurate, and actionable in your responses
5. Structure complex responses with clear sections and bullet points
6. Provide source citations and data-backed insights
7. Focus on delivering value through comprehensive analysis
8. Always complete your responses fully - do not cut off mid-sentence
9. When using tools, consider the context and choose the most appropriate parameters
10. Integrate document content naturally while maintaining accuracy and providing proper attribution
</instructions>""",
        description="System instructions for the agent"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level for the agent"
    )
    
    # Database Configuration
    database_url: Optional[str] = Field(
        default=None,
        description="Database URL for conversation memory storage"
    )
    
    # Performance Configuration
    max_concurrent_requests: int = Field(
        default=5,
        description="Maximum number of concurrent requests to MCP server"
    )
    
    request_timeout: int = Field(
        default=30,
        description="Timeout for requests in seconds"
    )
    
    # Retry Configuration
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests"
    )
    
    tool_retries: int = Field(
        default=2,
        description="Maximum number of retries for tool calls"
    )
    
    output_retries: int = Field(
        default=2,
        description="Maximum number of retries for output validation"
    )
    
    retry_delay: float = Field(
        default=1.0,
        description="Initial delay between retries in seconds"
    )
    
    max_retry_delay: float = Field(
        default=60.0,
        description="Maximum delay between retries in seconds"
    )
    
    retry_backoff_factor: float = Field(
        default=2.0,
        description="Exponential backoff multiplier for retry delays"
    )

    @field_validator('mcp_server_path', mode='before')
    @classmethod
    def validate_mcp_server_path(cls, v: str) -> str:
        """Validate and load MCP server path from environment if not provided."""
        if not v:
            v = os.getenv('RIVAL_SEARCH_MCP_SERVER_PATH', 'RivalSearchMCP/src/server.py')
        return v
    
    @model_validator(mode='before')
    @classmethod
    def validate_model_config(cls, values):
        """Validate and load model configuration from environment."""
        if isinstance(values, dict):
            # Check for model name override
            env_model = os.getenv('RIVAL_SEARCH_MODEL_NAME')
            if env_model:
                values['model_name'] = env_model
            
            # Load API keys from environment
            if 'openai_api_key' not in values or values['openai_api_key'] is None:
                values['openai_api_key'] = os.getenv('OPENAI_API_KEY') or os.getenv('RIVAL_SEARCH_OPENAI_API_KEY')
            
            if 'anthropic_api_key' not in values or values['anthropic_api_key'] is None:
                values['anthropic_api_key'] = os.getenv('ANTHROPIC_API_KEY') or os.getenv('RIVAL_SEARCH_ANTHROPIC_API_KEY')
            
            if 'google_api_key' not in values or values['google_api_key'] is None:
                values['google_api_key'] = os.getenv('GOOGLE_API_KEY') or os.getenv('RIVAL_SEARCH_GOOGLE_API_KEY')
            
            if 'google_vertex_ai' not in values or values['google_vertex_ai'] is None:
                env_val = os.getenv('GOOGLE_VERTEX_AI') or os.getenv('RIVAL_SEARCH_GOOGLE_VERTEX_AI')
                values['google_vertex_ai'] = env_val and env_val.lower() in ('true', '1', 'yes', 'on') if env_val else False
            
            if 'google_cloud_project' not in values or values['google_cloud_project'] is None:
                values['google_cloud_project'] = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('RIVAL_SEARCH_GOOGLE_CLOUD_PROJECT')
            
            if 'google_cloud_location' not in values or values['google_cloud_location'] is None:
                values['google_cloud_location'] = os.getenv('GOOGLE_CLOUD_LOCATION') or os.getenv('RIVAL_SEARCH_GOOGLE_CLOUD_LOCATION')
            
            if 'grok_api_key' not in values or values['grok_api_key'] is None:
                values['grok_api_key'] = os.getenv('GROK_API_KEY') or os.getenv('RIVAL_SEARCH_GROK_API_KEY')
            
            if 'deepseek_api_key' not in values or values['deepseek_api_key'] is None:
                values['deepseek_api_key'] = os.getenv('DEEPSEEK_API_KEY') or os.getenv('RIVAL_SEARCH_DEEPSEEK_API_KEY')
            
            if 'ollama_base_url' not in values or values['ollama_base_url'] is None:
                values['ollama_base_url'] = os.getenv('OLLAMA_BASE_URL') or os.getenv('RIVAL_SEARCH_OLLAMA_BASE_URL', 'http://localhost:11434/v1')
        
        return values

    @field_validator('openai_api_key', mode='before')
    @classmethod
    def validate_openai_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate and load OpenAI API key from environment."""
        if v is None:
            v = os.getenv('OPENAI_API_KEY') or os.getenv('RIVAL_SEARCH_OPENAI_API_KEY')
        return v

    @field_validator('anthropic_api_key', mode='before')
    @classmethod
    def validate_anthropic_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate and load Anthropic API key from environment."""
        if v is None:
            v = os.getenv('ANTHROPIC_API_KEY') or os.getenv('RIVAL_SEARCH_ANTHROPIC_API_KEY')
        return v

    @field_validator('google_api_key', mode='before')
    @classmethod
    def validate_google_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate and load Google API key from environment."""
        if v is None:
            v = os.getenv('GOOGLE_API_KEY') or os.getenv('RIVAL_SEARCH_GOOGLE_API_KEY')
        return v

    @field_validator('grok_api_key', mode='before')
    @classmethod
    def validate_grok_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate and load Grok API key from environment."""
        if v is None:
            v = os.getenv('GROK_API_KEY') or os.getenv('RIVAL_SEARCH_GROK_API_KEY')
        return v

    @field_validator('deepseek_api_key', mode='before')
    @classmethod
    def validate_deepseek_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate and load DeepSeek API key from environment."""
        if v is None:
            v = os.getenv('DEEPSEEK_API_KEY') or os.getenv('RIVAL_SEARCH_DEEPSEEK_API_KEY')
        return v

    @field_validator('ollama_base_url', mode='before')
    @classmethod
    def validate_ollama_base_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate and load Ollama base URL from environment."""
        if v is None:
            v = os.getenv('OLLAMA_BASE_URL') or os.getenv('RIVAL_SEARCH_OLLAMA_BASE_URL', 'http://localhost:11434/v1')
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator('max_concurrent_requests')
    @classmethod
    def validate_max_concurrent_requests(cls, v: int) -> int:
        """Validate max concurrent requests."""
        if v < 1 or v > 20:
            raise ValueError("max_concurrent_requests must be between 1 and 20")
        return v
    
    @field_validator('request_timeout')
    @classmethod
    def validate_request_timeout(cls, v: int) -> int:
        """Validate request timeout."""
        if v < 5 or v > 300:
            raise ValueError("request_timeout must be between 5 and 300 seconds")
        return v
    
    @field_validator('max_retries')
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        """Validate max retries."""
        if v < 0 or v > 10:
            raise ValueError("max_retries must be between 0 and 10")
        return v

    def get_required_api_key(self) -> str:
        """Get the required API key based on the selected model provider."""
        provider = self.model_name.split(':')[0] if ':' in self.model_name else 'grok'
        
        api_key_map = {
            'openai': self.openai_api_key,
            'anthropic': self.anthropic_api_key,
            'google-gla': self.google_api_key,
            'google-vertex': self.google_api_key,
            'grok': self.grok_api_key,
            'deepseek': self.deepseek_api_key,
            'ollama': None,  # Ollama doesn't require API key
        }
        
        api_key = api_key_map.get(provider)
        
        if api_key is None and provider != 'ollama':
            raise ValueError(f"API key required for provider '{provider}' but not found in environment variables")
        
        return api_key or ""

    def validate_provider_configuration(self) -> None:
        """Validate that the required configuration is available for the selected provider."""
        provider = self.model_name.split(':')[0] if ':' in self.model_name else 'grok'
        
        if provider == 'ollama':
            # Ollama doesn't require API key, but we should validate the base URL is accessible
            pass
        else:
            # For all other providers, validate API key is present
            api_key = self.get_required_api_key()
            if not api_key:
                raise ValueError(f"API key required for provider '{provider}' but not found")


def get_config() -> AgentConfig:
    """Get the agent configuration from environment variables."""
    return AgentConfig()
