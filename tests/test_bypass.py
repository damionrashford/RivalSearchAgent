import pytest
from src.core.bypass import detect_paywall, select_ua, select_proxy, get_proxies
from src.config import DEFAULT_UA_LIST, ARCHIVE_FALLBACKS

@pytest.mark.asyncio
async def test_get_proxies():
    proxies = await get_proxies(5)
    assert isinstance(proxies, list)
    assert len(proxies) <= 5

def test_select_ua():
    ua = select_ua()
    assert ua in DEFAULT_UA_LIST

def test_select_proxy(mocker):
    import src.core.bypass
    # Mock the module-level proxies variable
    src.core.bypass.proxies = ["127.0.0.1:8080"]
    proxy = select_proxy()
    assert proxy == "127.0.0.1:8080"
    src.core.bypass.proxies = []
    assert select_proxy() is None

def test_detect_paywall():
    assert detect_paywall("Subscribe now!") is True
    assert detect_paywall("Free content") is False

def test_archive_fallbacks():
    assert len(ARCHIVE_FALLBACKS) > 0
    assert all(url.startswith("https://") for url in ARCHIVE_FALLBACKS)
