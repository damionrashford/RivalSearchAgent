import pytest
import os
from src.config import DEFAULT_UA_LIST, PAYWALL_INDICATORS, ARCHIVE_FALLBACKS  # assume config has these

def test_default_ua_list():
    assert len(DEFAULT_UA_LIST) > 1
    assert all("Mozilla/5.0" in ua for ua in DEFAULT_UA_LIST)

def test_paywall_indicators():
    assert "subscribe" in PAYWALL_INDICATORS
    assert len(PAYWALL_INDICATORS) > 1

def test_archive_fallbacks():
    assert len(ARCHIVE_FALLBACKS) > 1
    assert "archive.is" in ARCHIVE_FALLBACKS[0]

def test_env_vars(mocker):
    os.environ['DATA_PATH'] = 'test.json'
    # Reload config if needed; assume it loads env
    from src.config import get_config  # hypothetical
    config = get_config()
    assert config['data_path'] == 'test.json'
