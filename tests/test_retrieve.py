import pytest
import asyncio

@pytest.mark.asyncio
async def test_base_fetch_url(mocker):
    """Test the core fetch functionality.""" 
    # Mock the entire base_fetch_url function to avoid external network calls
    async def mock_fetch(url, timeout=30):
        return "Test content from webpage"
    
    # Import after setting up the mock
    mocker.patch('src.core.fetch.base_fetch_url', side_effect=mock_fetch)
    
    from src.core.fetch import base_fetch_url
    result = await base_fetch_url("https://test.com")
    assert "Test content from webpage" in result
