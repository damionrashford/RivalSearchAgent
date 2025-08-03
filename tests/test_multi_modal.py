import pytest
from PIL import Image
from src.core.multi_modal import process_images_ocr
from bs4 import BeautifulSoup

@pytest.mark.asyncio
async def test_process_images_ocr(mocker):
    # Mock pytesseract
    mocker.patch('src.core.multi_modal.image_to_string', return_value="OCR text")
    
    # Mock httpx.AsyncClient
    mock_response = mocker.Mock()
    mock_response.content = b"\x89PNG\r\n\x1a\n"  # Minimal PNG header
    
    mock_client = mocker.AsyncMock()
    mock_client.get = mocker.AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=None)
    
    mocker.patch('httpx.AsyncClient', return_value=mock_client)
    
    # Mock PIL Image.open
    mock_image = mocker.Mock()
    mocker.patch('src.core.multi_modal.Image.open', return_value=mock_image)
    
    soup = BeautifulSoup('<img src="test.jpg">', 'html.parser')
    texts = await process_images_ocr(soup, "https://example.com")
    assert len(texts) == 1
    assert texts[0] == "OCR text"
