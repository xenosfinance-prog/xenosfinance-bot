# Aggiungi in fondo a bot.py
if __name__ == "__main__":
    # Test automatici se eseguito con pytest
    import sys
    if "pytest" in sys.modules:
        def test_bot_token():
            """Test che il token è configurato"""
            assert os.environ.get("TELEGRAM_BOT_TOKEN") is not None
    else:
        # Avvia il bot normalmente
        app.run_polling()
