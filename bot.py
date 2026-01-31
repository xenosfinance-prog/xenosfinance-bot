import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import yfinance as yf
import requests
from typing import Dict, Optional

# ======= CONFIGURATION =======
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")  # Get free key from newsapi.org

# ======= MARKET DATA FETCHER =======
class MarketAnalyzer:
    @staticmethod
    def get_ticker_data(symbol: str) -> Dict:
        """Fetch comprehensive ticker data"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="5d")
            
            current_price = info.get('regularMarketPrice', 0)
            prev_close = info.get('previousClose', current_price)
            change = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
            
            # Calculate 5-day trend
            if len(hist) >= 2:
                week_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100)
            else:
                week_change = 0
                
            return {
                'price': current_price,
                'change': change,
                'week_change': week_change,
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0)
            }
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return {'price': 0, 'change': 0, 'week_change': 0, 'volume': 0, 'market_cap': 0}
    
    @staticmethod
    def get_sentiment_indicator(change: float) -> str:
        """Return emoji based on price change"""
        if change > 1:
            return "🚀"
        elif change > 0:
            return "📈"
        elif change < -1:
            return "🔴"
        elif change < 0:
            return "📉"
        return "➡️"
    
    @staticmethod
    def get_market_sentiment(data: Dict) -> str:
        """Analyze overall market sentiment"""
        positive = sum(1 for v in data.values() if v.get('change', 0) > 0)
        total = len(data)
        ratio = positive / total if total > 0 else 0
        
        if ratio > 0.7:
            return "🟢 BULLISH - Strong buying pressure across markets"
        elif ratio > 0.5:
            return "🟡 NEUTRAL-BULLISH - Mixed signals, slight upward bias"
        elif ratio > 0.3:
            return "🟡 NEUTRAL-BEARISH - Mixed signals, slight downward pressure"
        else:
            return "🔴 BEARISH - Significant selling pressure observed"

# ======= NEWS FETCHER =======
class NewsFetcher:
    @staticmethod
    def get_financial_news() -> str:
        """Fetch top financial and geopolitical news"""
        if not NEWS_API_KEY:
            return "• Fed maintains current interest rate stance\n• Global markets await inflation data\n• Geopolitical tensions impact energy sector"
        
        try:
            url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&pageSize=5&apiKey={NEWS_API_KEY}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('status') == 'ok' and data.get('articles'):
                news_items = []
                for article in data['articles'][:5]:
                    title = article.get('title', '').split(' - ')[0]  # Remove source
                    if len(title) > 80:
                        title = title[:77] + "..."
                    news_items.append(f"• {title}")
                return "\n".join(news_items)
        except Exception as e:
            print(f"News fetch error: {e}")
        
        return "• Markets monitoring central bank policies\n• Global economic data in focus\n• Geopolitical developments under watch"
    
    @staticmethod
    def get_macro_analysis() -> str:
        """Generate macro economic analysis"""
        # This would ideally pull from economic APIs (FRED, World Bank, etc.)
        return """**MACRO OUTLOOK:**
• US: Fed policy remains data-dependent, inflation trending toward target
• EU: ECB navigating growth concerns amid rate normalization
• ASIA: China economic stimulus measures supporting growth
• COMMODITIES: Energy markets sensitive to geopolitical developments"""

# ======= PROFESSIONAL MARKET UPDATE =======
async def send_professional_market_update():
    """Send comprehensive professional market analysis"""
    bot = Bot(token=TOKEN)
    analyzer = MarketAnalyzer()
    news_fetcher = NewsFetcher()
    
    try:
        print("📊 Generating professional market update...")
        
        # ===== FETCH ALL MARKET DATA =====
        futures_data = {
            'S&P 500': analyzer.get_ticker_data("ES=F"),
            'Nasdaq': analyzer.get_ticker_data("NQ=F"),
            'Dow Jones': analyzer.get_ticker_data("YM=F"),
            'Russell 2000': analyzer.get_ticker_data("RTY=F"),
        }
        
        commodities_data = {
            'Gold': analyzer.get_ticker_data("GC=F"),
            'Silver': analyzer.get_ticker_data("SI=F"),
            'WTI Crude': analyzer.get_ticker_data("CL=F"),
            'Brent Crude': analyzer.get_ticker_data("BZ=F"),
            'Nat Gas': analyzer.get_ticker_data("NG=F"),
            'Copper': analyzer.get_ticker_data("HG=F"),
        }
        
        forex_data = {
            'EUR/USD': analyzer.get_ticker_data("EURUSD=X"),
            'GBP/USD': analyzer.get_ticker_data("GBPUSD=X"),
            'USD/JPY': analyzer.get_ticker_data("JPY=X"),
            'USD/CHF': analyzer.get_ticker_data("CHF=X"),
            'AUD/USD': analyzer.get_ticker_data("AUDUSD=X"),
        }
        
        crypto_data = {
            'Bitcoin': analyzer.get_ticker_data("BTC-USD"),
            'Ethereum': analyzer.get_ticker_data("ETH-USD"),
            'Solana': analyzer.get_ticker_data("SOL-USD"),
        }
        
        indices_data = {
            'VIX': analyzer.get_ticker_data("^VIX"),
            'DXY': analyzer.get_ticker_data("DX-Y.NYB"),
        }
        
        # ===== GET NEWS & SENTIMENT =====
        news = news_fetcher.get_financial_news()
        macro = news_fetcher.get_macro_analysis()
        
        # Market sentiment
        all_data = {**futures_data, **commodities_data, **forex_data, **crypto_data}
        sentiment = analyzer.get_market_sentiment(all_data)
        
        # ===== TIMESTAMP =====
        now = datetime.utcnow()
        timestamp = now.strftime("%Y-%m-%d %H:%M UTC")
        
        # ===== BUILD PROFESSIONAL MESSAGE =====
        message = f"""
╔═══════════════════════════════════╗
    📊 **PROFESSIONAL MARKET ANALYSIS**
╚═══════════════════════════════════╝

🕐 **{timestamp}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 **MARKET SENTIMENT**
{sentiment}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔮 **US FUTURES OVERVIEW**
"""
        
        for name, data in futures_data.items():
            emoji = analyzer.get_sentiment_indicator(data['change'])
            message += f"{emoji} **{name}**: {data['price']:,.2f} ({data['change']:+.2f}%) | Week: {data['week_change']:+.2f}%\n"
        
        message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🥇 **COMMODITIES ANALYSIS**
"""
        
        gold = commodities_data['Gold']
        oil_wti = commodities_data['WTI Crude']
        oil_brent = commodities_data['Brent Crude']
        
        message += f"""
{analyzer.get_sentiment_indicator(gold['change'])} **Gold**: ${gold['price']:,.2f}/oz ({gold['change']:+.2f}%)
   └─ Weekly: {gold['week_change']:+.2f}% | Safe-haven demand {('rising' if gold['change'] > 0 else 'falling')}

{analyzer.get_sentiment_indicator(oil_wti['change'])} **WTI Crude**: ${oil_wti['price']:,.2f}/bbl ({oil_wti['change']:+.2f}%)
{analyzer.get_sentiment_indicator(oil_brent['change'])} **Brent Crude**: ${oil_brent['price']:,.2f}/bbl ({oil_brent['change']:+.2f}%)
   └─ Energy sector {'under pressure' if oil_wti['change'] < 0 else 'showing strength'}

"""
        
        for name, data in list(commodities_data.items())[4:]:
            emoji = analyzer.get_sentiment_indicator(data['change'])
            message += f"{emoji} **{name}**: ${data['price']:,.2f} ({data['change']:+.2f}%)\n"
        
        message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💱 **FOREX MAJORS**
"""
        
        for name, data in forex_data.items():
            emoji = analyzer.get_sentiment_indicator(data['change'])
            price_display = f"{data['price']:.4f}" if 'JPY' not in name and 'CHF' not in name else f"{data['price']:.2f}"
            message += f"{emoji} **{name}**: {price_display} ({data['change']:+.2f}%) | 5D: {data['week_change']:+.2f}%\n"
        
        vix = indices_data['VIX']
        dxy = indices_data['DXY']
        
        message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **KEY INDICATORS**
{analyzer.get_sentiment_indicator(vix['change'])} **VIX (Fear Index)**: {vix['price']:.2f} ({vix['change']:+.2f}%)
   └─ Market volatility: {'Elevated' if vix['price'] > 20 else 'Low' if vix['price'] < 15 else 'Moderate'}

{analyzer.get_sentiment_indicator(dxy['change'])} **DXY (Dollar Index)**: {dxy['price']:.2f} ({dxy['change']:+.2f}%)
   └─ USD strength: {'Strengthening' if dxy['change'] > 0 else 'Weakening'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
₿ **CRYPTOCURRENCY MARKETS**
"""
        
        for name, data in crypto_data.items():
            emoji = analyzer.get_sentiment_indicator(data['change'])
            message += f"{emoji} **{name}**: ${data['price']:,.2f} ({data['change']:+.2f}%) | Week: {data['week_change']:+.2f}%\n"
        
        message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📰 **TOP FINANCIAL NEWS**
{news}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌍 **MACRO ECONOMIC OVERVIEW**
{macro}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ **RISK DISCLAIMER**
This analysis is for informational purposes only. 
Not financial advice. Always DYOR.

⏰ **Next update in 2 hours**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='Markdown')
        print(f"✅ Professional market update sent at {timestamp}")
        
    except Exception as e:
        print(f"❌ Error sending professional update: {e}")
        # Send error notification
        try:
            await bot.send_message(
                chat_id=CHANNEL_ID, 
                text=f"⚠️ Market update temporarily unavailable. Retrying shortly.\nError: {str(e)[:100]}"
            )
        except:
            pass

# ======= COMMAND HANDLERS =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Professional Market Analysis Bot**\n\n"
        "Get comprehensive market analysis every 2 hours!\n"
        "Use /help to see all available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = """
📊 **AVAILABLE COMMANDS**

**General**
/start - Start the bot
/help - Show commands
/update - Get instant market update

**Forex**
/forex_major - Major Forex pairs
/forex_minor - Minor Forex pairs
/forex_summary - Forex summary

**Commodities**
/gold - Gold price
/silver - Silver price
/commodities - Commodities overview
/oil_wti - WTI oil price
/oil_brent - Brent oil price
/ngas - Natural gas price

**Energy & Reports**
/eia_report - Latest EIA report

**Macro News**
/macro_us - US macro news
/macro_eu - EU macro news
/macro_global - Global macro overview
/market_news - Top market news

**Stocks**
/us_stocks - US stocks intraday
/eu_stocks - EU stocks intraday
/pre_market - US pre-market
/earnings - Today's earnings

**Crypto**
/crypto_major - Major cryptocurrencies
/crypto_summary - Crypto market overview

📈 Professional updates sent every 2 hours!
"""
    await update.message.reply_text(commands)

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual update trigger"""
    await update.message.reply_text("📊 Generating professional market analysis...")
    await send_professional_market_update()

# ======= FOREX COMMANDS =======
async def forex_major(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    eur = analyzer.get_ticker_data("EURUSD=X")
    gbp = analyzer.get_ticker_data("GBPUSD=X")
    jpy = analyzer.get_ticker_data("JPY=X")
    
    message = f"""💱 **MAJOR FOREX PAIRS**

{analyzer.get_sentiment_indicator(eur['change'])} EUR/USD: {eur['price']:.4f} ({eur['change']:+.2f}%)
{analyzer.get_sentiment_indicator(gbp['change'])} GBP/USD: {gbp['price']:.4f} ({gbp['change']:+.2f}%)
{analyzer.get_sentiment_indicator(jpy['change'])} USD/JPY: {jpy['price']:.2f} ({jpy['change']:+.2f}%)
"""
    await update.message.reply_text(message)

async def forex_minor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    aud = analyzer.get_ticker_data("AUDUSD=X")
    nzd = analyzer.get_ticker_data("NZDUSD=X")
    cad = analyzer.get_ticker_data("CADUSD=X")
    
    message = f"""💱 **MINOR FOREX PAIRS**

{analyzer.get_sentiment_indicator(aud['change'])} AUD/USD: {aud['price']:.4f} ({aud['change']:+.2f}%)
{analyzer.get_sentiment_indicator(nzd['change'])} NZD/USD: {nzd['price']:.4f} ({nzd['change']:+.2f}%)
{analyzer.get_sentiment_indicator(cad['change'])} CAD/USD: {cad['price']:.4f} ({cad['change']:+.2f}%)
"""
    await update.message.reply_text(message)

async def forex_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💱 Forex markets showing mixed signals. Use /forex_major for detailed analysis.")

# ======= COMMODITIES COMMANDS =======
async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    data = analyzer.get_ticker_data("GC=F")
    message = f"""{analyzer.get_sentiment_indicator(data['change'])} **GOLD**

Price: ${data['price']:,.2f}/oz
Change: {data['change']:+.2f}%
Week: {data['week_change']:+.2f}%

Safe-haven demand {'increasing' if data['change'] > 0 else 'decreasing'}
"""
    await update.message.reply_text(message)

async def silver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    data = analyzer.get_ticker_data("SI=F")
    message = f"""{analyzer.get_sentiment_indicator(data['change'])} **SILVER**

Price: ${data['price']:,.2f}/oz
Change: {data['change']:+.2f}%
Week: {data['week_change']:+.2f}%
"""
    await update.message.reply_text(message)

async def commodities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🥇 Commodities overview available in main update. Use /gold or /silver for specifics.")

async def oil_wti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    data = analyzer.get_ticker_data("CL=F")
    message = f"""{analyzer.get_sentiment_indicator(data['change'])} **WTI CRUDE OIL**

Price: ${data['price']:,.2f}/barrel
Change: {data['change']:+.2f}%
Week: {data['week_change']:+.2f}%
"""
    await update.message.reply_text(message)

async def oil_brent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    data = analyzer.get_ticker_data("BZ=F")
    message = f"""{analyzer.get_sentiment_indicator(data['change'])} **BRENT CRUDE OIL**

Price: ${data['price']:,.2f}/barrel
Change: {data['change']:+.2f}%
Week: {data['week_change']:+.2f}%
"""
    await update.message.reply_text(message)

async def ngas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    data = analyzer.get_ticker_data("NG=F")
    message = f"""{analyzer.get_sentiment_indicator(data['change'])} **NATURAL GAS**

Price: ${data['price']:,.2f}/MMBtu
Change: {data['change']:+.2f}%
Week: {data['week_change']:+.2f}%
"""
    await update.message.reply_text(message)

async def eia_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 EIA Weekly Report: Check latest inventory data at eia.gov")

# ======= MACRO / NEWS COMMANDS =======
async def macro_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇺🇸 US Macro: Fed policy data-dependent. Monitor CPI, employment data.")

async def macro_eu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇪🇺 EU Macro: ECB balancing growth and inflation concerns.")

async def macro_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌍 Global Macro: Mixed signals across regions. China stimulus in focus.")

async def market_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news = NewsFetcher.get_financial_news()
    await update.message.reply_text(f"📰 **TOP MARKET NEWS**\n\n{news}")

# ======= STOCKS COMMANDS =======
async def us_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    spy = analyzer.get_ticker_data("SPY")
    qqq = analyzer.get_ticker_data("QQQ")
    dia = analyzer.get_ticker_data("DIA")
    
    message = f"""📈 **US STOCKS (ETF Proxies)**

{analyzer.get_sentiment_indicator(spy['change'])} SPY (S&P 500): ${spy['price']:.2f} ({spy['change']:+.2f}%)
{analyzer.get_sentiment_indicator(qqq['change'])} QQQ (Nasdaq): ${qqq['price']:.2f} ({qqq['change']:+.2f}%)
{analyzer.get_sentiment_indicator(dia['change'])} DIA (Dow): ${dia['price']:.2f} ({dia['change']:+.2f}%)
"""
    await update.message.reply_text(message)

async def eu_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇪🇺 EU Stocks: DAX, CAC, FTSE tracking. Check futures for overview.")

async def pre_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌅 Pre-market data available through futures: /update for full analysis")

async def earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💼 Earnings: Check earnings calendar for today's reports.")

# ======= CRYPTO COMMANDS =======
async def crypto_major(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    btc = analyzer.get_ticker_data("BTC-USD")
    eth = analyzer.get_ticker_data("ETH-USD")
    sol = analyzer.get_ticker_data("SOL-USD")
    
    message = f"""₿ **MAJOR CRYPTOCURRENCIES**

{analyzer.get_sentiment_indicator(btc['change'])} Bitcoin: ${btc['price']:,.2f} ({btc['change']:+.2f}%)
{analyzer.get_sentiment_indicator(eth['change'])} Ethereum: ${eth['price']:,.2f} ({eth['change']:+.2f}%)
{analyzer.get_sentiment_indicator(sol['change'])} Solana: ${sol['price']:,.2f} ({sol['change']:+.2f}%)
"""
    await update.message.reply_text(message)

async def crypto_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("₿ Crypto markets: Check /crypto_major for detailed analysis")

# ======= MAIN APPLICATION =======
async def main():
    print("=" * 70)
    print("🚀 PROFESSIONAL MARKET ANALYSIS BOT STARTING")
    print("=" * 70)
    
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN environment variable is missing!")
        return
    
    if not CHANNEL_ID:
        print("⚠️  TELEGRAM_CHANNEL_ID not set. Auto-posting disabled.")
    
    print(f"✅ Token configured: {TOKEN[:15]}...")
    print(f"✅ Channel ID: {CHANNEL_ID}")
    
    # Build application
    app = Application.builder().token(TOKEN).build()
    
    # Register all command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("update", update_command))
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
    
    print("✅ All command handlers registered")
    
    # Initialize and start bot
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    print("🤖 Bot is now running and polling for messages...")
    
    # Send initial market update
    if CHANNEL_ID:
        print("📊 Sending initial market update...")
        await send_professional_market_update()
    
    # Main loop: send updates every 2 hours
    try:
        while True:
            await asyncio.sleep(7200)  # 2 hours = 7200 seconds
            if CHANNEL_ID:
                await send_professional_market_update()
    except KeyboardInterrupt:
        print("\n⚠️  Shutting down bot...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        print("✅ Bot stopped successfully")

if __name__ == "__main__":
    asyncio.run(main())
