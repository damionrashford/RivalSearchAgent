import pytest
import asyncio
from src.server import mcp

def test_fastmcp_server_exists():
    """Test that FastMCP server instance is created."""
    assert mcp is not None
    assert mcp.name == "rival-search"

@pytest.mark.asyncio  
async def test_tools_registered():
    """Test that tools are properly registered with FastMCP."""
    # Test that we can access tool modules
    from src.tools import web_tools, reasoning_tools, data_tools
    
    # Verify modules exist and have register functions
    assert hasattr(web_tools, 'register_web_tools')
    assert hasattr(reasoning_tools, 'register_reasoning_tools') 
    assert hasattr(data_tools, 'register_data_tools')
    
    # Verify they are callable
    assert callable(web_tools.register_web_tools)
    assert callable(reasoning_tools.register_reasoning_tools)
    assert callable(data_tools.register_data_tools)
    
    # Verify that the mcp instance exists and is configured
    assert mcp is not None
    assert mcp.name == "rival-search"
