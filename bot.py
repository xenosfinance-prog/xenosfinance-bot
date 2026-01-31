import os
import asyncio
import time
from datetime import datetime, timedelta
import pytz
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import yfinance as yf
import requests
from typing import Dict

# ======= CONFIGURATION =======
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
PORT = int(os.getenv("PORT", 8080))

# Timezones
ET = pytz.timezone('America/New_York')
UTC = pytz.UTC

# Market hours (Eastern Time)
MARKET_OPEN = 9, 30
MARKET_CLOSE = 16, 0
PRE_MARKET_START = 4, 0
POST_MARKET_END = 20, 0

# ======= CACHE SYSTEM =======
# Saves last fetched data so if Yahoo blocks us, we still have data
_cache = {}
_cache_time = {}
CACHE_TTL = 300  # 5 minuti cache

def get_cached(symbol: str) -> Dict | None:
    """Return cached data if still valid"""
    if symbol in _cache and symbol in _cache_time:
        if time.time() - _cache_time[symbol] < CACHE_TTL:
            return _cache[symbol]
    return None

def set_cache(symbol: str, data: Dict):
    """Save data to cache"""
    _cache[symbol] = data
    _cache_time[symbol] = time.time()

# ======= MARKET SCHEDULE =======
class MarketSchedule:
    @staticmethod
    def get_current_time_et() -> datetime:
        return datetime.now(ET)

    @staticmethod
    def is_weekday() -> bool:
        return MarketSchedule.get_current_time_et().weekday() < 5

    @staticmethod
    def get_market_status() -> str:
        if not MarketSchedule.is_weekday():
            return "CLOSED_WEEKEND"
        current = MarketSchedule.get_current_time_et()
        mins = current.hour * 60 + current.minute

        if mins < PRE_MARKET_START[0] * 60 + PRE_MARKET_START[1]:
            return "CLOSED_OVERNIGHT"
        elif mins < MARKET_OPEN[0] * 60 + MARKET_OPEN[1]:
            return "PRE_MARKET"
        elif mins < MARKET_CLOSE[0] * 60 + MARKET_CLOSE[1]:
            return "MARKET_OPEN"
        elif mins < POST_MARKET_END[0] * 60 + POST_MARKET_END[1]:
            return "POST_MARKET"
        else:
            return "CLOSED_OVERNIGHT"

    @staticmethod
    def get_next_market_event() -> tuple:
        current = MarketSchedule.get_current_time_et()
        status = MarketSchedule.get_market_status()

        if status == "CLOSED_WEEKEND":
            days_ahead = 7 - current.weekday()
            if days_ahead == 7:
                days_ahead = 1
            next_monday = current + timedelta(days=days_ahead)
            next_event = next_monday.replace(hour=PRE_MARKET_START[0], minute=PRE_MARKET_START[1], second=0, microsecond=0)
            return "PRE MARKET OPEN", next_event
        elif status == "CLOSED_OVERNIGHT":
            if current.hour >= POST_MARKET_END[0]:
                next_day = current + timedelta(days=1)
                next_event = next_day.replace(hour=PRE_MARKET_START[0], minute=PRE_MARKET_START[1], second=0, microsecond=0)
            else:
                next_event = current.replace(hour=PRE_MARKET_START[0], minute=PRE_MARKET_START[1], second=0, microsecond=0)
            return "PRE MARKET OPEN", next_event
        elif status == "PRE_MARKET":
            next_event = current.replace(hour=MARKET_OPEN[0], minute=MARKET_OPEN[1], second=0, microsecond=0)
            return "MARKET OPEN", next_event
        elif status == "MARKET_OPEN":
            next_event = current.replace(hour=MARKET_CLOSE[0], minute=MARKET_CLOSE[1], second=0, microsecond=0)
            return "MARKET CLOSE", next_event
        elif status == "POST_MARKET":
            next_event = current.replace(hour=POST_MARKET_END[0], minute=POST_MARKET_END[1], second=0, microsecond=0)
            return "POST MARKET CLOSE", next_event
        return "UNKNOWN", current

    @staticmethod
    def get_market_status_emoji() -> str:
        emojis = {
            "PRE_MARKET": "🌅",
            "MARKET_OPEN": "🟢",
            "POST_MARKET": "🌆",
            "CLOSED_OVERNIGHT": "🌙",
            "CLOSED_WEEKEND": "🏖️"
        }
        return emojis.get(MarketSchedule.get_market_status(), "⏰")

# ======= MARKET DATA FETCHER (con delay e cache) =======
class MarketAnalyzer:
    @staticmethod
    async def get_ticker_data(symbol: str) -> Dict:
        """Fetch data con cache e delay per evitare 429"""
        # Controlla cache prima
        cached = get_cached(symbol)
        if cached:
            print(f"  📦 {symbol} from cache")
            return cached

        # Delay per evitare rate limit
        await asyncio.sleep(1.5)

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            current_price = info.get('regularMarketPrice', 0)
            prev_close = info.get('previousClose', current_price)
            change = ((current_price - prev_close) / prev_close * 100) if prev_close else 0

            hist = ticker.history(period="5d")
            if len(hist) >= 2:
                week_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100)
            else:
                week_change = 0

            data = {
                'price': current_price,
                'change': change,
                'week_change': week_change,
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0)
            }

            # Salva in cache
            set_cache(symbol, data)
            print(f"  ✅ {symbol}: ${current_price}")
            return data

        except Exception as e:
            print(f"  ❌ {symbol}: {e}")
            # Prova a restituire cache vecchia anche se scaduta
            if symbol in _cache:
                print(f"  📦 {symbol} using old cache")
                return _cache[symbol]
            return {'price': 0, 'change': 0, 'week_change': 0, 'volume': 0, 'market_cap': 0}

    @staticmethod
    def get_sentiment_indicator(change: float) -> str:
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
        if not NEWS_API_KEY:
            return ("• Fed maintains current interest rate stance\n"
                    "• Global markets await inflation data\n"
                    "• Geopolitical tensions impact energy sector\n"
                    "• EU ECB navigating growth concerns\n"
                    "• Asia markets mixed amid China stimulus")
        try:
            url = (f"https://newsapi.org/v2/top-headlines"
                   f"?category=business&language=en&pageSize=5&apiKey={NEWS_API_KEY}")
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get('status') == 'ok' and data.get('articles'):
                news_items = []
                for article in data['articles'][:5]:
                    title = article.get('title', '').split(' - ')[0]
                    if len(title) > 80:
                        title = title[:77] + "..."
                    news_items.append(f"• {title}")
                return "\n".join(news_items)
        except Exception as e:
            print(f"News fetch error: {e}")
        return ("• Markets monitoring central bank policies\n"
                "• Global economic data in focus\n"
                "• Geopolitical developments under watch")

    @staticmethod
    def get_macro_analysis() -> str:
        return ("• US: Fed policy remains data-dependent, inflation trending toward target\n"
                "• EU: ECB navigating growth concerns amid rate normalization\n"
                "• ASIA: China economic stimulus measures supporting growth\n"
                "• COMMODITIES: Energy markets sensitive to geopolitical developments")

# ======= PROFESSIONAL MARKET UPDATE =======
async def send_professional_market_update():
    """Send comprehensive professional market analysis to channel"""
    bot = Bot(token=TOKEN)
    analyzer = MarketAnalyzer()

    try:
        print("\n📊 Generating professional market update...")

        # Market status
        market_status = MarketSchedule.get_market_status()
        status_emoji = MarketSchedule.get_market_status_emoji()
        next_event, next_time = MarketSchedule.get_next_market_event()

        time_until = next_time - MarketSchedule.get_current_time_et()
        hours_until = int(time_until.total_seconds() / 3600)
        mins_until = int((time_until.total_seconds() % 3600) / 60)

        status_messages = {
            "PRE_MARKET": "🌅 PRE-MARKET SESSION - US markets opening soon",
            "MARKET_OPEN": "🟢 MARKET OPEN - Active trading session",
            "POST_MARKET": "🌆 POST-MARKET SESSION - Extended hours trading",
            "CLOSED_OVERNIGHT": "🌙 MARKETS CLOSED - Overnight session",
            "CLOSED_WEEKEND": "🏖️ WEEKEND - Markets resume Monday"
        }
        status_message = status_messages.get(market_status, "⏰ Market Status Unknown")

        # ===== FETCH DATA (sequenziale con delay) =====
        print("  📥 Fetching futures...")
        futures_data = {}
        for name, symbol in [('S&P 500', 'ES=F'), ('Nasdaq', 'NQ=F'), ('Dow Jones', 'YM=F'), ('Russell 2000', 'RTY=F')]:
            futures_data[name] = await analyzer.get_ticker_data(symbol)

        print("  📥 Fetching commodities...")
        commodities_data = {}
        for name, symbol in [('Gold', 'GC=F'), ('Silver', 'SI=F'), ('WTI Crude', 'CL=F'), ('Brent Crude', 'BZ=F'), ('Nat Gas', 'NG=F'), ('Copper', 'HG=F')]:
            commodities_data[name] = await analyzer.get_ticker_data(symbol)

        print("  📥 Fetching forex...")
        forex_data = {}
        for name, symbol in [('EUR/USD', 'EURUSD=X'), ('GBP/USD', 'GBPUSD=X'), ('USD/JPY', 'JPY=X'), ('USD/CHF', 'CHF=X'), ('AUD/USD', 'AUDUSD=X')]:
            forex_data[name] = await analyzer.get_ticker_data(symbol)

        print("  📥 Fetching crypto...")
        crypto_data = {}
        for name, symbol in [('Bitcoin', 'BTC-USD'), ('Ethereum', 'ETH-USD'), ('Solana', 'SOL-USD')]:
            crypto_data[name] = await analyzer.get_ticker_data(symbol)

        print("  📥 Fetching indices...")
        indices_data = {}
        for name, symbol in [('VIX', '^VIX'), ('DXY', 'DX-Y.NYB')]:
            indices_data[name] = await analyzer.get_ticker_data(symbol)

        # News & sentiment
        news = NewsFetcher.get_financial_news()
        macro = NewsFetcher.get_macro_analysis()
        all_data = {**futures_data, **commodities_data, **forex_data, **crypto_data}
        sentiment = analyzer.get_market_sentiment(all_data)

        # Timestamp
        now = datetime.now(UTC)
        et_time = now.astimezone(ET)
        timestamp = et_time.strftime("%Y-%m-%d %H:%M ET")
        day_name = et_time.strftime("%A")

        # ===== BUILD MESSAGE =====
        msg = (
            f"╔══════════════════════════════════╗\n"
            f"   📊 PROFESSIONAL MARKET ANALYSIS\n"
            f"╚══════════════════════════════════╝\n\n"
            f"🕐 {timestamp} ({day_name})\n\n"
            f"{status_emoji} {status_message}\n"
            f"⏰ Next: {next_event} in {hours_until}h {mins_until}m\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 MARKET SENTIMENT\n"
            f"{sentiment}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔮 US FUTURES\n"
        )

        for name, data in futures_data.items():
            emoji = analyzer.get_sentiment_indicator(data['change'])
            msg += f"{emoji} {name}: {data['price']:,.2f} ({data['change']:+.2f}%) | Week: {data['week_change']:+.2f}%\n"

        msg += (
            f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🥇 COMMODITIES\n\n"
        )

        gold = commodities_data['Gold']
        oil_wti = commodities_data['WTI Crude']
        oil_brent = commodities_data['Brent Crude']

        msg += (
            f"{analyzer.get_sentiment_indicator(gold['change'])} Gold: ${gold['price']:,.2f}/oz ({gold['change']:+.2f}%)\n"
            f"   └─ Weekly: {gold['week_change']:+.2f}% | Safe-haven demand {'rising ⬆️' if gold['change'] > 0 else 'falling ⬇️'}\n\n"
            f"{analyzer.get_sentiment_indicator(oil_wti['change'])} WTI Crude: ${oil_wti['price']:,.2f}/bbl ({oil_wti['change']:+.2f}%)\n"
            f"{analyzer.get_sentiment_indicator(oil_brent['change'])} Brent Crude: ${oil_brent['price']:,.2f}/bbl ({oil_brent['change']:+.2f}%)\n"
            f"   └─ Energy sector {'under pressure 🔻' if oil_wti['change'] < 0 else 'showing strength 🔺'}\n\n"
        )

        for name in ['Silver', 'Nat Gas', 'Copper']:
            data = commodities_data[name]
            emoji = analyzer.get_sentiment_indicator(data['change'])
            msg += f"{emoji} {name}: ${data['price']:,.2f} ({data['change']:+.2f}%)\n"

        msg += (
            f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💱 FOREX MAJORS\n\n"
        )

        for name, data in forex_data.items():
            emoji = analyzer.get_sentiment_indicator(data['change'])
            price_fmt = f"{data['price']:.4f}" if 'JPY' not in name and 'CHF' not in name else f"{data['price']:.2f}"
            msg += f"{emoji} {name}: {price_fmt} ({data['change']:+.2f}%) | 5D: {data['week_change']:+.2f}%\n"

        vix = indices_data['VIX']
        dxy = indices_data['DXY']
        vix_label = 'Elevated ⚠️' if vix['price'] > 20 else ('Low ✅' if vix['price'] < 15 else 'Moderate')

        msg += (
            f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 KEY INDICATORS\n\n"
            f"{analyzer.get_sentiment_indicator(vix['change'])} VIX (Fear Index): {vix['price']:.2f} ({vix['change']:+.2f}%)\n"
            f"   └─ Volatility: {vix_label}\n\n"
            f"{analyzer.get_sentiment_indicator(dxy['change'])} DXY (Dollar Index): {dxy['price']:.2f} ({dxy['change']:+.2f}%)\n"
            f"   └─ USD: {'Strengthening 💪' if dxy['change'] > 0 else 'Weakening 📉'}\n"
        )

        msg += (
            f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"₿ CRYPTOCURRENCY\n\n"
        )

        for name, data in crypto_data.items():
            emoji = analyzer.get_sentiment_indicator(data['change'])
            msg += f"{emoji} {name}: ${data['price']:,.2f} ({data['change']:+.2f}%) | Week: {data['week_change']:+.2f}%\n"

        msg += (
            f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📰 TOP FINANCIAL NEWS\n\n"
            f"{news}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 MACRO ECONOMIC OVERVIEW\n\n"
            f"{macro}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ RISK DISCLAIMER\n"
            f"This analysis is for informational purposes only.\n"
            f"Not financial advice. Always DYOR.\n\n"
            f"⏰ Updates: Every 4 hours (Mon-Fri)\n"
            f"🔔 Market: 9:30 AM - 4:00 PM ET\n"
            f"🌅 Pre-Market: 4:00 AM - 9:30 AM ET\n"
            f"🌆 Post-Market: 4:00 PM - 8:00 PM ET\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

        await bot.send_message(chat_id=CHANNEL_ID, text=msg)
        print(f"✅ Market update sent! | Status: {market_status} | Next: {next_event}")

    except Exception as e:
        print(f"❌ Error sending update: {e}")
        try:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"⚠️ Market update temporarily unavailable. Retrying in 4 hours.\nError: {str(e)[:100]}"
            )
        except:
            pass

# ======= COMMAND HANDLERS =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Professional Market Analysis Bot\n\n"
        "📊 Automated updates every 4 hours (Mon-Fri)\n"
        "💱 Forex | 🥇 Commodities | ₿ Crypto | 📈 Futures\n\n"
        "Use /help to see all available commands.\n"
        "📢 Join channel: @xenosmarketfinance"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = (
        "📊 AVAILABLE COMMANDS\n\n"
        "General\n"
        "/start - Start the bot\n"
        "/help - Show commands\n"
        "/update - Get instant market update\n\n"
        "Forex\n"
        "/forex_major - Major Forex pairs\n"
        "/forex_minor - Minor Forex pairs\n"
        "/forex_summary - Forex summary\n\n"
        "Commodities\n"
        "/gold - Gold price\n"
        "/silver - Silver price\n"
        "/commodities - Commodities overview\n"
        "/oil_wti - WTI oil price\n"
        "/oil_brent - Brent oil price\n"
        "/ngas - Natural gas price\n\n"
        "Energy\n"
        "/eia_report - Latest EIA report\n\n"
        "Macro\n"
        "/macro_us - US macro news\n"
        "/macro_eu - EU macro news\n"
        "/macro_global - Global macro overview\n"
        "/market_news - Top market news\n\n"
        "Stocks\n"
        "/us_stocks - US stocks intraday\n"
        "/eu_stocks - EU stocks intraday\n"
        "/pre_market - US pre-market\n"
        "/earnings - Today's earnings\n\n"
        "Crypto\n"
        "/crypto_major - Major cryptocurrencies\n"
        "/crypto_summary - Crypto market overview\n\n"
        "📈 Auto updates every 4 hours (Mon-Fri)!"
    )
    await update.message.reply_text(commands)

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Generating market analysis... This may take a moment.")
    await send_professional_market_update()
    await update.message.reply_text("✅ Update sent to the channel!")

# ======= FOREX =======
async def forex_major(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    eur = await analyzer.get_ticker_data("EURUSD=X")
    gbp = await analyzer.get_ticker_data("GBPUSD=X")
    jpy = await analyzer.get_ticker_data("JPY=X")
    msg = (
        f"💱 MAJOR FOREX PAIRS\n\n"
        f"{analyzer.get_sentiment_indicator(eur['change'])} EUR/USD: {eur['price']:.4f} ({eur['change']:+.2f}%)\n"
        f"{analyzer.get_sentiment_indicator(gbp['change'])} GBP/USD: {gbp['price']:.4f} ({gbp['change']:+.2f}%)\n"
        f"{analyzer.get_sentiment_indicator(jpy['change'])} USD/JPY: {jpy['price']:.2f} ({jpy['change']:+.2f}%)\n"
    )
    await update.message.reply_text(msg)

async def forex_minor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    aud = await analyzer.get_ticker_data("AUDUSD=X")
    nzd = await analyzer.get_ticker_data("NZDUSD=X")
    cad = await analyzer.get_ticker_data("CADUSD=X")
    msg = (
        f"💱 MINOR FOREX PAIRS\n\n"
        f"{analyzer.get_sentiment_indicator(aud['change'])} AUD/USD: {aud['price']:.4f} ({aud['change']:+.2f}%)\n"
        f"{analyzer.get_sentiment_indicator(nzd['change'])} NZD/USD: {nzd['price']:.4f} ({nzd['change']:+.2f}%)\n"
        f"{analyzer.get_sentiment_indicator(cad['change'])} CAD/USD: {cad['price']:.4f} ({cad['change']:+.2f}%)\n"
    )
    await update.message.reply_text(msg)

async def forex_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💱 Forex markets showing mixed signals. Use /forex_major for detailed analysis.")

# ======= COMMODITIES =======
async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    data = await analyzer.get_ticker_data("GC=F")
    msg = (
        f"{analyzer.get_sentiment_indicator(data['change'])} GOLD\n\n"
        f"Price: ${data['price']:,.2f}/oz\n"
        f"Change: {data['change']:+.2f}%\n"
        f"Week: {data['week_change']:+.2f}%\n\n"
        f"Safe-haven demand {'increasing ⬆️' if data['change'] > 0 else 'decreasing ⬇️'}"
    )
    await update.message.reply_text(msg)

async def silver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    data = await analyzer.get_ticker_data("SI=F")
    msg = (
        f"{analyzer.get_sentiment_indicator(data['change'])} SILVER\n\n"
        f"Price: ${data['price']:,.2f}/oz\n"
        f"Change: {data['change']:+.2f}%\n"
        f"Week: {data['week_change']:+.2f}%\n"
    )
    await update.message.reply_text(msg)

async def commodities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🥇 Use /gold, /silver, /oil_wti or /oil_brent for specific prices.")

async def oil_wti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    data = await analyzer.get_ticker_data("CL=F")
    msg = (
        f"{analyzer.get_sentiment_indicator(data['change'])} WTI CRUDE OIL\n\n"
        f"Price: ${data['price']:,.2f}/barrel\n"
        f"Change: {data['change']:+.2f}%\n"
        f"Week: {data['week_change']:+.2f}%\n"
    )
    await update.message.reply_text(msg)

async def oil_brent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    data = await analyzer.get_ticker_data("BZ=F")
    msg = (
        f"{analyzer.get_sentiment_indicator(data['change'])} BRENT CRUDE OIL\n\n"
        f"Price: ${data['price']:,.2f}/barrel\n"
        f"Change: {data['change']:+.2f}%\n"
        f"Week: {data['week_change']:+.2f}%\n"
    )
    await update.message.reply_text(msg)

async def ngas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    data = await analyzer.get_ticker_data("NG=F")
    msg = (
        f"{analyzer.get_sentiment_indicator(data['change'])} NATURAL GAS\n\n"
        f"Price: ${data['price']:,.2f}/MMBtu\n"
        f"Change: {data['change']:+.2f}%\n"
        f"Week: {data['week_change']:+.2f}%\n"
    )
    await update.message.reply_text(msg)

async def eia_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 EIA Weekly Report: Check latest inventory data at eia.gov")

# ======= MACRO / NEWS =======
async def macro_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇺🇸 US Macro: Fed policy data-dependent. Monitor CPI, employment data.")

async def macro_eu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇪🇺 EU Macro: ECB balancing growth and inflation concerns.")

async def macro_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌍 Global Macro: Mixed signals across regions. China stimulus in focus.")

async def market_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news = NewsFetcher.get_financial_news()
    await update.message.reply_text(f"📰 TOP MARKET NEWS\n\n{news}")

# ======= STOCKS =======
async def us_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    spy = await analyzer.get_ticker_data("SPY")
    qqq = await analyzer.get_ticker_data("QQQ")
    dia = await analyzer.get_ticker_data("DIA")
    msg = (
        f"📈 US STOCKS\n\n"
        f"{analyzer.get_sentiment_indicator(spy['change'])} SPY (S&P 500): ${spy['price']:.2f} ({spy['change']:+.2f}%)\n"
        f"{analyzer.get_sentiment_indicator(qqq['change'])} QQQ (Nasdaq): ${qqq['price']:.2f} ({qqq['change']:+.2f}%)\n"
        f"{analyzer.get_sentiment_indicator(dia['change'])} DIA (Dow): ${dia['price']:.2f} ({dia['change']:+.2f}%)\n"
    )
    await update.message.reply_text(msg)

async def eu_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇪🇺 EU Stocks: DAX, CAC, FTSE tracking. Use /update for full analysis.")

async def pre_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌅 Pre-market data available through futures. Use /update for full analysis.")

async def earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💼 Earnings: Check earnings calendar for today's reports.")

# ======= CRYPTO =======
async def crypto_major(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analyzer = MarketAnalyzer()
    btc = await analyzer.get_ticker_data("BTC-USD")
    eth = await analyzer.get_ticker_data("ETH-USD")
    sol = await analyzer.get_ticker_data("SOL-USD")
    msg = (
        f"₿ MAJOR CRYPTOCURRENCIES\n\n"
        f"{analyzer.get_sentiment_indicator(btc['change'])} Bitcoin: ${btc['price']:,.2f} ({btc['change']:+.2f}%)\n"
        f"{analyzer.get_sentiment_indicator(eth['change'])} Ethereum: ${eth['price']:,.2f} ({eth['change']:+.2f}%)\n"
        f"{analyzer.get_sentiment_indicator(sol['change'])} Solana: ${sol['price']:,.2f} ({sol['change']:+.2f}%)\n"
    )
    await update.message.reply_text(msg)

async def crypto_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("₿ Crypto markets overview. Use /crypto_major for detailed analysis.")

# ======= BACKGROUND SCHEDULER =======
async def scheduled_updates_loop():
    """Background loop: sends updates every 4 hours, Mon-Fri only"""
    print("📅 Scheduled updates loop started")

    # Send first update if weekday
    if CHANNEL_ID:
        if MarketSchedule.is_weekday():
            print("📊 Sending initial market update...")
            await send_professional_market_update()
        else:
            print("🏖️ Weekend - No initial update. Resumes Monday.")

    last_logged_day = None

    while True:
        await asyncio.sleep(14400)  # 4 hours

        if CHANNEL_ID and MarketSchedule.is_weekday():
            print(f"\n⏰ 4h interval - {MarketSchedule.get_current_time_et().strftime('%A %H:%M ET')}")
            await send_professional_market_update()
        else:
            current = MarketSchedule.get_current_time_et()
            if current.weekday() >= 5 and last_logged_day != current.date():
                print(f"\n🏖️ Weekend - Skipping ({current.strftime('%A')}). Resumes Monday.")
                last_logged_day = current.date()

# ======= MAIN =======
async def main():
    print("=" * 70)
    print("🚀 PROFESSIONAL MARKET ANALYSIS BOT STARTING")
    print("=" * 70)

    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN is missing!")
        return
    if not CHANNEL_ID:
        print("⚠️  TELEGRAM_CHANNEL_ID not set. Auto-posting disabled.")

    print(f"✅ Token: {TOKEN[:15]}...")
    print(f"✅ Channel ID: {CHANNEL_ID}")
    print(f"✅ Port: {PORT}")

    # Build app
    app = Application.builder().token(TOKEN).build()

    # Register handlers
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

    # Initialize
    await app.initialize()
    await app.start()

    # Start polling with drop_pending_updates to kill old conflicts
    print("🤖 Starting polling...")
    await app.updater.start_polling(drop_pending_updates=True)
    print("✅ Polling started!")

    # Start scheduled updates as a BACKGROUND task (non-blocking)
    asyncio.create_task(scheduled_updates_loop())

    print("📅 Schedule: Every 4 hours, Mon-Fri only")
    print("🕐 Market Hours: 9:30 AM - 4:00 PM ET")
    print("🌅 Pre-Market: 4:00 AM - 9:30 AM ET")
    print("🌆 Post-Market: 4:00 PM - 8:00 PM ET")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ BOT FULLY RUNNING - Polling + Scheduled Updates")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Keep alive forever
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\n⚠️  Shutting down...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        print("✅ Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
