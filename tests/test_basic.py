import pytest
from app.config import settings

def test_config_loading():
    assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]
