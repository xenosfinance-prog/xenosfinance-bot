# pip install python-telegram-bot==13.14 requests yfinance
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import yfinance as yf
import requests
import os

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
/earnings - Today’s earnings
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
    price = yf.Ticker("GC=F").info['regularMarketPrice']
    update.message.reply_text(f"Gold: ${price:.2f}")

def silver(update: Update, context: CallbackContext):
    price = yf.Ticker("SI=F").info['regularMarketPrice']
    update.message.reply_text(f"Silver: ${price:.2f}")

def commodities(update: Update, context: CallbackContext):
    update.message.reply_text("Metals and soft commodities: Gold and Silver up, Oil stable...")

# ======= ENERGY =======
def oil_wti(update: Update, context: CallbackContext):
    price = yf.Ticker("CL=F").info['regularMarketPrice']
    update.message.reply_text(f"WTI: ${price:.2f}")

def oil_brent(update: Update, context: CallbackContext):
    price = yf.Ticker("BZ=F").info['regularMarketPrice']
    update.message.reply_text(f"Brent: ${price:.2f}")

def ngas(update: Update, context: CallbackContext):
    price = yf.Ticker("NG=F").info['regularMarketPrice']
    update.message.reply_text(f"Natural Gas: ${price:.2f}")

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
    btc = yf.Ticker("BTC-USD").info['regularMarketPrice']
    eth = yf.Ticker("ETH-USD").info['regularMarketPrice']
    update.message.reply_text(f"BTC: ${btc:.0f}, ETH: ${eth:.0f}")

def crypto_summary(update: Update, context: CallbackContext):
    update.message.reply_text("Crypto: BTC stable, ETH slightly down, general trend bullish.")

# ======= BOT SETUP =======
updater = Updater(TOKEN)
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
updater.start_polling()
updater.idle()
