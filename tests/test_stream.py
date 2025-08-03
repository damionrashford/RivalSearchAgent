import pytest
import asyncio
from src.core.fetch import stream_fetch

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
