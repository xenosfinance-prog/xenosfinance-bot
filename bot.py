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

# ======= HELP / START =======
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hello! I am your intraday market bot. Use /help to see available commands.")

def help_command(update: Update, context: CallbackContext):
    commands = """
/start - Start the bot
/help - Show commands
/forex_major - Major Forex pairs
/forex_minor - Minor Forex pairs
/forex_summary - Forex summary
/gold - Gold price
/silver - Silver price
/commodities - Commodities overview
/oil_wti - WTI oil price
/oil_brent - Brent oil price
/ngas - Natural gas price
/eia_report - Latest EIA report
/macro_us - US macro news
/macro_eu - EU macro news
/macro_global - Global macro overview
/market_news - Top market news
/us_stocks - US stocks intraday
/eu_stocks - EU stocks intraday
/pre_market - US pre-market
/earnings - Today's earnings
/crypto_major - Major cryptocurrencies
/crypto_summary - Crypto market overview
"""
    update.message.reply_text(commands)

# ======= FOREX =======
def forex_major(update: Update, context: CallbackContext):
    update.message.reply_text("EUR/USD: 1.1599 (+0.03%)\nUSD/JPY: 155.50 (+0.10%)\nGBP/USD: 1.3400 (-0.05%)\nUSD/CHF: 0.9100 (+0.02%)")

def forex_minor(update: Update, context: CallbackContext):
    update.message.reply_text("AUD/JPY: 102.50 (+0.08%)\nEUR/GBP: 0.8700 (+0.01%)\nNZD/USD: 0.6200 (-0.02%)")

def forex_summary(update: Update, context: CallbackContext):
    update.message.reply_text("Forex intraday: Market stable, EUR/USD slightly up...")

# ======= COMMODITIES =======
def gold(update: Update, context: CallbackContext):
    try:
        ticker = yf.Ticker("GC=F")
        price = ticker.info.get('regularMarketPrice', 'N/A')
        if price != 'N/A':
            update.message.reply_text(f"Gold: ${price:.2f}")
        else:
            update.message.reply_text("Gold: Data not available")
    except Exception as e:
        logger.error(f"Error fetching gold price: {e}")
        update.message.reply_text("Gold: Error fetching data")

def silver(update: Update, context: CallbackContext):
    try:
        ticker = yf.Ticker("SI=F")
        price = ticker.info.get('regularMarketPrice', 'N/A')
        if price != 'N/A':
            update.message.reply_text(f"Silver: ${price:.2f}")
        else:
            update.message.reply_text("Silver: Data not available")
    except Exception as e:
        logger.error(f"Error fetching silver price: {e}")
        update.message.reply_text("Silver: Error fetching data")

def commodities(update: Update, context: CallbackContext):
    update.message.reply_text("Metals and soft commodities: Gold and Silver up, Oil stable...")

# ======= ENERGY =======
def oil_wti(update: Update, context: CallbackContext):
    try:
        ticker = yf.Ticker("CL=F")
        price = ticker.info.get('regularMarketPrice', 'N/A')
        if price != 'N/A':
            update.message.reply_text(f"WTI: ${price:.2f}")
        else:
            update.message.reply_text("WTI: Data not available")
    except Exception as e:
        logger.error(f"Error fetching WTI price: {e}")
        update.message.reply_text("WTI: Error fetching data")

def oil_brent(update: Update, context: CallbackContext):
    try:
        ticker = yf.Ticker("BZ=F")
        price = ticker.info.get('regularMarketPrice', 'N/A')
        if price != 'N/A':
            update.message.reply_text(f"Brent: ${price:.2f}")
        else:
            update.message.reply_text("Brent: Data not available")
    except Exception as e:
        logger.error(f"Error fetching Brent price: {e}")
        update.message.reply_text("Brent: Error fetching data")

def ngas(update: Update, context: CallbackContext):
    try:
        ticker = yf.Ticker("NG=F")
        price = ticker.info.get('regularMarketPrice', 'N/A')
        if price != 'N/A':
            update.message.reply_text(f"Natural Gas: ${price:.2f}")
        else:
            update.message.reply_text("Natural Gas: Data not available")
    except Exception as e:
        logger.error(f"Error fetching Natural Gas price: {e}")
        update.message.reply_text("Natural Gas: Error fetching data")

def eia_report(update: Update, context: CallbackContext):
    update.message.reply_text("EIA Weekly Report: Oil prices slightly up, inventories down...")

# ======= MACRO / NEWS =======
def macro_us(update: Update, context: CallbackContext):
    update.message.reply_text("US Macro: GDP growth, inflation stable, labor market solid.")

def macro_eu(update: Update, context: CallbackContext):
    update.message.reply_text("EU Macro: PMI rising, ECB evaluates monetary policy...")

def macro_global(update: Update, context: CallbackContext):
    update.message.reply_text("Global Macro: Mixed Asian markets, Chinese economy stable.")

def market_news(update: Update, context: CallbackContext):
    update.message.reply_text("News: Nasdaq +0.5%, Gold stable, Oil slightly down...")

# ======= STOCKS =======
def us_stocks(update: Update, context: CallbackContext):
    update.message.reply_text("US Stocks intraday: AAPL +1.2%, TSLA +2.0%, AMZN +0.8%")

def eu_stocks(update: Update, context: CallbackContext):
    update.message.reply_text("EU Stocks intraday: DAX +0.3%, CAC +0.2%, FTSE +0.1%")

def pre_market(update: Update, context: CallbackContext):
    update.message.reply_text("US Pre-market: Nasdaq +0.2%, S&P500 +0.1%")

def earnings(update: Update, context: CallbackContext):
    update.message.reply_text("Earnings today: AAPL, MSFT, TSLA. Expected results positive.")

# ======= CRYPTO =======
def crypto_major(update: Update, context: CallbackContext):
    try:
        btc_ticker = yf.Ticker("BTC-USD")
        eth_ticker = yf.Ticker("ETH-USD")
        btc = btc_ticker.info.get('regularMarketPrice', 'N/A')
        eth = eth_ticker.info.get('regularMarketPrice', 'N/A')
        
        if btc != 'N/A' and eth != 'N/A':
            update.message.reply_text(f"BTC: ${btc:.0f}\nETH: ${eth:.0f}")
        else:
            update.message.reply_text("Crypto: Data not available")
    except Exception as e:
        logger.error(f"Error fetching crypto prices: {e}")
        update.message.reply_text("Crypto: Error fetching data")

def crypto_summary(update: Update, context: CallbackContext):
    update.message.reply_text("Crypto: BTC stable, ETH slightly down, general trend bullish.")

# ======= BOT SETUP =======
def main():
    # OBBLIGATORIO: use_context=True per python-telegram-bot v13.x
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command handler
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
    logger.info("Bot starting...")
    updater.start_polling()
    logger.info("Bot started and polling...")
    updater.idle()

if __name__ == '__main__':
    main()
