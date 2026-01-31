import os
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import yfinance as yf
import requests
from typing import Dict, Optional

# ======= CONFIGURATION =======
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")  # Get free key from newsapi.org
PORT = int(os.getenv("PORT", 8443))  # Railway assigns this automatically

# Timezones
ET = pytz.timezone('America/New_York')
UTC = pytz.UTC

# Market hours (Eastern Time)
MARKET_OPEN = 9, 30  # 9:30 AM ET
MARKET_CLOSE = 16, 0  # 4:00 PM ET
PRE_MARKET_START = 4, 0  # 4:00 AM ET
POST_MARKET_END = 20, 0  # 8:00 PM ET

# ======= MARKET SCHEDULE MANAGER =======
class MarketSchedule:
    @staticmethod
    def get_current_time_et() -> datetime:
        """Get current time in Eastern Time"""
        return datetime.now(ET)
    
    @staticmethod
    def is_weekday() -> bool:
        """Check if today is Monday-Friday"""
        current = MarketSchedule.get_current_time_et()
        return current.weekday() < 5  # 0=Monday, 4=Friday
    
    @staticmethod
    def get_market_status() -> str:
        """Determine current market status"""
        if not MarketSchedule.is_weekday():
            return "CLOSED_WEEKEND"
        
        current = MarketSchedule.get_current_time_et()
        current_time = (current.hour, current.minute)
        
        # Convert to minutes for easier comparison
        current_mins = current.hour * 60 + current.minute
        pre_market_mins = PRE_MARKET_START[0] * 60 + PRE_MARKET_START[1]
        market_open_mins = MARKET_OPEN[0] * 60 + MARKET_OPEN[1]
        market_close_mins = MARKET_CLOSE[0] * 60 + MARKET_CLOSE[1]
        post_market_mins = POST_MARKET_END[0] * 60 + POST_MARKET_END[1]
        
        if current_mins < pre_market_mins:
            return "CLOSED_OVERNIGHT"
        elif current_mins < market_open_mins:
            return "PRE_MARKET"
        elif current_mins < market_close_mins:
            return "MARKET_OPEN"
        elif current_mins < post_market_mins:
            return "POST_MARKET"
        else:
            return "CLOSED_OVERNIGHT"
    
    @staticmethod
    def get_next_market_event() -> tuple:
        """Get the next market event (open/close) and time"""
        current = MarketSchedule.get_current_time_et()
        status = MarketSchedule.get_market_status()
        
        if status == "CLOSED_WEEKEND":
            # Find next Monday
            days_ahead = 7 - current.weekday()
            if days_ahead == 7:
                days_ahead = 1
            next_monday = current + timedelta(days=days_ahead)
            next_event = next_monday.replace(hour=PRE_MARKET_START[0], minute=PRE_MARKET_START[1], second=0, microsecond=0)
            return "PRE_MARKET_OPEN", next_event
        
        elif status == "CLOSED_OVERNIGHT":
            # Next is pre-market
            if current.hour >= POST_MARKET_END[0]:
                # Tomorrow's pre-market
                next_day = current + timedelta(days=1)
                next_event = next_day.replace(hour=PRE_MARKET_START[0], minute=PRE_MARKET_START[1], second=0, microsecond=0)
            else:
                # Today's pre-market
                next_event = current.replace(hour=PRE_MARKET_START[0], minute=PRE_MARKET_START[1], second=0, microsecond=0)
            return "PRE_MARKET_OPEN", next_event
        
        elif status == "PRE_MARKET":
            next_event = current.replace(hour=MARKET_OPEN[0], minute=MARKET_OPEN[1], second=0, microsecond=0)
            return "MARKET_OPEN", next_event
        
        elif status == "MARKET_OPEN":
            next_event = current.replace(hour=MARKET_CLOSE[0], minute=MARKET_CLOSE[1], second=0, microsecond=0)
            return "MARKET_CLOSE", next_event
        
        elif status == "POST_MARKET":
            next_event = current.replace(hour=POST_MARKET_END[0], minute=POST_MARKET_END[1], second=0, microsecond=0)
            return "POST_MARKET_CLOSE", next_event
        
        return "UNKNOWN", current
    
    @staticmethod
    def get_market_status_emoji() -> str:
        """Get emoji for current market status"""
        status = MarketSchedule.get_market_status()
        emojis = {
            "PRE_MARKET": "🌅",
            "MARKET_OPEN": "🔔",
            "POST_MARKET": "🌆",
            "CLOSED_OVERNIGHT": "🌙",
            "CLOSED_WEEKEND": "🏖️"
        }
        return emojis.get(status, "⏰")

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
    schedule = MarketSchedule()
    
    try:
        print("📊 Generating professional market update...")
        
        # Get market status
        market_status = schedule.get_market_status()
        status_emoji = schedule.get_market_status_emoji()
        next_event, next_time = schedule.get_next_market_event()
        
        # Format next event time
        time_until = next_time - schedule.get_current_time_et()
        hours_until = int(time_until.total_seconds() / 3600)
        mins_until = int((time_until.total_seconds() % 3600) / 60)
        
        # Market status messages
        status_messages = {
            "PRE_MARKET": "🌅 **PRE-MARKET SESSION** - US markets opening soon",
            "MARKET_OPEN": "🔔 **MARKET OPEN** - Active trading session",
            "POST_MARKET": "🌆 **POST-MARKET SESSION** - Extended hours trading",
            "CLOSED_OVERNIGHT": "🌙 **MARKETS CLOSED** - Overnight session",
            "CLOSED_WEEKEND": "🏖️ **WEEKEND** - Markets resume Monday"
        }
        
        status_message = status_messages.get(market_status, "⏰ Market Status Unknown")
        
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
        now = datetime.now(UTC)
        et_time = now.astimezone(ET)
        timestamp = et_time.strftime("%Y-%m-%d %H:%M ET")
        day_name = et_time.strftime("%A")
        
        # ===== BUILD PROFESSIONAL MESSAGE =====
        message = f"""
╔═══════════════════════════════════╗
    📊 **PROFESSIONAL MARKET ANALYSIS**
╚═══════════════════════════════════╝

🕐 **{timestamp}** ({day_name})

{status_emoji} {status_message}
⏰ **Next**: {next_event.replace('_', ' ')} in {hours_until}h {mins_until}m

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

⏰ **Update Schedule**: Every 4 hours (Mon-Fri only)
🔔 **Market Hours**: 9:30 AM - 4:00 PM ET
🌅 **Pre-Market**: 4:00 AM - 9:30 AM ET
🌆 **Post-Market**: 4:00 PM - 8:00 PM ET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='Markdown')
        print(f"✅ Professional market update sent at {timestamp}")
        print(f"   Market Status: {market_status}")
        print(f"   Next Event: {next_event} in {hours_until}h {mins_until}m")
        
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
async def scheduled_updates_task(app):
    """Background task for scheduled market updates"""
    print("📅 Scheduled updates task started")
    
    # Send initial market update if it's a weekday
    if CHANNEL_ID:
        if MarketSchedule.is_weekday():
            print("📊 Sending initial market update...")
            await send_professional_market_update()
        else:
            print("🏖️ Weekend - No initial update sent")
            print("   Bot will resume Monday")
    
    # Main loop: send updates every 4 hours on weekdays only
    last_update_day = None
    
    while True:
        try:
            # Wait 4 hours
            await asyncio.sleep(14400)  # 4 hours = 14400 seconds
            
            if CHANNEL_ID and MarketSchedule.is_weekday():
                current_day = MarketSchedule.get_current_time_et().date()
                
                # Send update
                print(f"\n{'='*60}")
                print(f"⏰ 4-hour interval reached - {MarketSchedule.get_current_time_et().strftime('%A %H:%M ET')}")
                await send_professional_market_update()
                last_update_day = current_day
                
            else:
                current = MarketSchedule.get_current_time_et()
                if current.weekday() >= 5:
                    # Only log once per weekend check
                    if last_update_day != current.date():
                        print(f"\n🏖️ Weekend detected - Skipping update ({current.strftime('%A')})")
                        print("   Next update: Monday morning")
                        last_update_day = current.date()
        except Exception as e:
            print(f"❌ Error in scheduled updates: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying

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
    print(f"✅ Port: {PORT}")
    
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
    
    # Initialize and start bot with polling
    await app.initialize()
    await app.start()
    
    # Start polling with conflict resolution
    print("🤖 Starting bot with polling (conflict resolution enabled)...")
    print("📅 Schedule: Updates every 4 hours, Monday-Friday only")
    print("🕐 Market Hours: 9:30 AM - 4:00 PM ET")
    print("🌅 Pre-Market: 4:00 AM - 9:30 AM ET")
    print("🌆 Post-Market: 4:00 PM - 8:00 PM ET")
    
    try:
        # Start polling with drop_pending_updates to clear any conflicts
        await app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
        print("✅ Bot polling started successfully!")
        
        # Run scheduled updates in background
        await scheduled_updates_task(app)
        
    except KeyboardInterrupt:
        print("\n⚠️  Shutting down bot...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        print("✅ Bot stopped successfully")

if __name__ == "__main__":
    asyncio.run(main())
