# FIX per Python 3.13 dove imghdr è stato rimosso
try:
    import imghdr
except ImportError:
    # Crea un modulo fittizio per imghdr
    import sys
    
    class FakeImghdr:
        @staticmethod
        def what(file, h=None):
            return None
    
    sys.modules['imghdr'] = FakeImghdr()
    imghdr = FakeImghdr()

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import yfinance as yf
import requests
import os
import logging

# Configura logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ======= TOKEN FROM ENVIRONMENT =======
TOKEN = os.environ.get("TELEGRAM_TOKEN")  # più sicuro su Render

# ... il resto del tuo codice rimane uguale ...

# ======= BOT SETUP =======
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command handler (aggiungi tutti qui)
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("forex_major", forex_major))
    dp.add_handler(CommandHandler("forex_minor", forex_minor))
    dp.add_handler(CommandHandler("forex_summary", forex_summary))
    dp.add_handler(CommandHandler("gold", gold))
    dp.add_handler(CommandHandler("silver", silver))
    dp.add_handler(CommandHandler("commodities", commodities))
    dp.add_handler(CommandHandler("oil_wti", oil_wti))
    dp.add_handler(CommandHandler("oil_brent", oil_brent))
    dp.add_handler(CommandHandler("ngas", ngas))
    dp.add_handler(CommandHandler("eia_report", eia_report))
    dp.add_handler(CommandHandler("macro_us", macro_us))
    dp.add_handler(CommandHandler("macro_eu", macro_eu))
    dp.add_handler(CommandHandler("macro_global", macro_global))
    dp.add_handler(CommandHandler("market_news", market_news))
    dp.add_handler(CommandHandler("us_stocks", us_stocks))
    dp.add_handler(CommandHandler("eu_stocks", eu_stocks))
    dp.add_handler(CommandHandler("pre_market", pre_market))
    dp.add_handler(CommandHandler("earnings", earnings))
    dp.add_handler(CommandHandler("crypto_major", crypto_major))
    dp.add_handler(CommandHandler("crypto_summary", crypto_summary))

    # Start bot
    updater.start_polling()
    logger.info("Bot started and polling...")
    updater.idle()

if __name__ == '__main__':
    main()
