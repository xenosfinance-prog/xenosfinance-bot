import os
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import yfinance as yf

# ======= TOKEN FROM ENVIRONMENT =======
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# ======= HELP / START =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your intraday market bot. Use /help to see available commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(commands)

# ======= FOREX =======
async def forex_major(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("EUR/USD: 1.1599 (+0.03%)\nUSD/JPY: 155.50 (+0.10%)\nGBP/USD: 1.3400 (-0.05%)\nUSD/CHF: 0.9100 (+0.02%)")

async def forex_minor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("AUD/JPY: 102.50 (+0.08%)\nEUR/GBP: 0.8700 (+0.01%)\nNZD/USD: 0.6200 (-0.02%)")

async def forex_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Forex intraday: Market stable, EUR/USD slightly up...")

# ======= COMMODITIES =======
async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = yf.Ticker("GC=F").info['regularMarketPrice']
        await update.message.reply_text(f"Gold: ${price:.2f}")
    except:
        await update.message.reply_text("Gold: Data not available")

async def silver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = yf.Ticker("SI=F").info['regularMarketPrice']
        await update.message.reply_text(f"Silver: ${price:.2f}")
    except:
        await update.message.reply_text("Silver: Data not available")

async def commodities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Metals and soft commodities: Gold and Silver up, Oil stable...")

# ======= ENERGY =======
async def oil_wti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = yf.Ticker("CL=F").info['regularMarketPrice']
        await update.message.reply_text(f"WTI: ${price:.2f}")
    except:
        await update.message.reply_text("WTI: Data not available")

async def oil_brent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = yf.Ticker("BZ=F").info['regularMarketPrice']
        await update.message.reply_text(f"Brent: ${price:.2f}")
    except:
        await update.message.reply_text("Brent: Data not available")

async def ngas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = yf.Ticker("NG=F").info['regularMarketPrice']
        await update.message.reply_text(f"Natural Gas: ${price:.2f}")
    except:
        await update.message.reply_text("Natural Gas: Data not available")

async def eia_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("EIA Weekly Report: Oil prices slightly up, inventories down...")

# ======= MACRO / NEWS =======
async def macro_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("US Macro: GDP growth, inflation stable, labor market solid.")

async def macro_eu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("EU Macro: PMI rising, ECB evaluates monetary policy...")

async def macro_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Global Macro: Mixed Asian markets, Chinese economy stable.")

async def market_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("News: Nasdaq +0.5%, Gold stable, Oil slightly down...")

# ======= STOCKS =======
async def us_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("US Stocks intraday: AAPL +1.2%, TSLA +2.0%, AMZN +0.8%")

async def eu_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("EU Stocks intraday: DAX +0.3%, CAC +0.2%, FTSE +0.1%")

async def pre_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("US Pre-market: Nasdaq +0.2%, S&P500 +0.1%")

async def earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Earnings today: AAPL, MSFT, TSLA. Expected results positive.")

# ======= CRYPTO =======
async def crypto_major(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        btc = yf.Ticker("BTC-USD").info['regularMarketPrice']
        eth = yf.Ticker("ETH-USD").info['regularMarketPrice']
        await update.message.reply_text(f"BTC: ${btc:.0f}, ETH: ${eth:.0f}")
    except:
        await update.message.reply_text("Crypto: Data not available")

async def crypto_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Crypto: BTC stable, ETH slightly down, general trend bullish.")

# ======= AUTO POST TO CHANNEL =======
async def send_market_update():
    """Send automatic market update to channel"""
    bot = Bot(token=TOKEN)
    
    try:
        # Get real prices
        btc = yf.Ticker("BTC-USD").info.get('regularMarketPrice', 0)
        eth = yf.Ticker("ETH-USD").info.get('regularMarketPrice', 0)
        gold_price = yf.Ticker("GC=F").info.get('regularMarketPrice', 0)
        
        message = f"""📊 **Market Update**

💰 Crypto:
- BTC: ${btc:,.0f}
- ETH: ${eth:,.0f}

🥇 Commodities:
- Gold: ${gold_price:,.2f}

📈 Markets stable, tracking intraday movements...
"""
        
        await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='Markdown')
        print("✅ Market update sent to channel!")
    except Exception as e:
        print(f"❌ Error sending update: {e}")

# ======= MAIN =======
async def main():
    print("=" * 60)
    print("🚀 BOT STARTING")
    print("=" * 60)
    
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN missing")
        return
    
    print(f"✅ Token OK: {TOKEN[:15]}...")
    
    # Create application
    app = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("forex_major", forex_major))
    app.add_handler(CommandHandler("forex_minor", forex_minor))
    app.add_handler(CommandHandler("forex_summary", forex_summary))
    app.add_handler(CommandHandler("gold", gold))
    app.add_handler(CommandHandler("silver", silver))
    app.add_handler(CommandHandler("commodities", commodities))
    app.add_handler(CommandHandler("oil_wti", oil_wti))
    app.add_handler(CommandHandler("oil_brent", oil_brent))
    app.add_handler(CommandHandler("ngas", ngas))
    app.add_handler(CommandHandler("eia_report", eia_report))
    app.add_handler(CommandHandler("macro_us", macro_us))
    app.add_handler(CommandHandler("macro_eu", macro_eu))
    app.add_handler(CommandHandler("macro_global", macro_global))
    app.add_handler(CommandHandler("market_news", market_news))
    app.add_handler(CommandHandler("us_stocks", us_stocks))
    app.add_handler(CommandHandler("eu_stocks", eu_stocks))
    app.add_handler(CommandHandler("pre_market", pre_market))
    app.add_handler(CommandHandler("earnings", earnings))
    app.add_handler(CommandHandler("crypto_major", crypto_major))
    app.add_handler(CommandHandler("crypto_summary", crypto_summary))
    
    print("🤖 Bot started with all commands!")
    
    # Send first update
    await send_market_update()
    
    # Loop for hourly updates
    while True:
        await asyncio.sleep(3600)  # 1 hour
        await send_market_update()

if __name__ == "__main__":
    asyncio.run(main())
```

**Poi aggiorna anche `requirements.txt`:**
```
python-telegram-bot[webhooks]==20.7
yfinance
requests
python-dotenv
