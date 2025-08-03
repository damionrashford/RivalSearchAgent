import pytest
from src.logger import logger  # assume setup

def test_logger(caplog):
    with caplog.at_level("INFO"):
        logger.info("Test log")
        assert "Test log" in caplog.text
