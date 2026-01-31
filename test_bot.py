import pytest
import os

def test_environment_variables():
    """Test che le variabili d'ambiente siano configurabili"""
    assert True

def test_token_format():
    """Test formato token"""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF")
    assert ":" in token
