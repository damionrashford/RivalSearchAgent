import pytest
import asyncio
from src.core.fetch import base_fetch_url, batch_rival_retrieve, stream_fetch

@pytest.mark.asyncio
async def test_base_fetch_url(mocker):
    # Mock httpx response
    mock_response = mocker.Mock()
    mock_response.text = "<html>Test</html>"
    mock_response.status_code = 200
    mock_response.headers = {'content-type': 'text/html'}
    
    # Mock AsyncClient
    mock_client = mocker.AsyncMock()
    mock_client.get = mocker.AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=None)
    
    mocker.patch('httpx.AsyncClient', return_value=mock_client)
    mocker.patch('src.core.bypass.select_ua', return_value="Mozilla/5.0")
    mocker.patch('src.core.bypass.select_proxy', return_value=None)
    mocker.patch('src.core.multi_modal.process_images_ocr', return_value=[])
    mocker.patch('random.random', return_value=0.5)  # Ensure we don't use cloudscraper
    
    content = await base_fetch_url("https://test.com")
    assert "Test" in content

@pytest.mark.asyncio
async def test_batch_rival_retrieve(mocker):
    mocker.patch('httpx.get', return_value=mocker.Mock(text="Test content"))
    urls = ["https://a.com", "https://b.com"]
    contents = await batch_rival_retrieve(urls, {})
    assert len(contents) == 2

@pytest.mark.asyncio
async def test_stream_fetch(mocker):
    # Create a mock websocket that returns chunks
    mock_ws = mocker.AsyncMock()
    mock_ws.recv = mocker.AsyncMock(return_value="chunk")
    
    # Create async context manager
    mock_connect = mocker.AsyncMock()
    mock_connect.__aenter__ = mocker.AsyncMock(return_value=mock_ws)
    mock_connect.__aexit__ = mocker.AsyncMock(return_value=None)
    
    mocker.patch('websockets.connect', return_value=mock_connect)
    content = await stream_fetch("ws://test")
    assert "chunk" in content
