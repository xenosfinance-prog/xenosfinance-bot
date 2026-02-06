import os
import logging
import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from anthropic import Anthropic

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)

# ============================================================
# CONFIG
# ============================================================
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
CLAUDE_API_KEY = os.environ['CLAUDE_API_KEY']
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '')

claude = Anthropic(api_key=CLAUDE_API_KEY)

# ============================================================
# MULTI-SOURCE MARKET DATA (No yfinance!)
# ============================================================

async def fetch_json(session, url, headers=None, timeout=10):
    """Safe JSON fetch with timeout."""
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            if resp.status == 200:
                return await resp.json()
    except Exception as e:
        logger.warning(f"Fetch failed: {url[:60]}... - {e}")
    return None

async def get_coinbase_btc(session):
    """BTC from Coinbase (free, no key)."""
    data = await fetch_json(session, "https://api.coinbase.com/v2/prices/BTC-USD/spot")
    if data and 'data' in data:
        return {'symbol': 'BTC/USD', 'price': float(data['data']['amount']), 'source': 'Coinbase'}
    return None

async def get_coinbase_eth(session):
    """ETH from Coinbase."""
    data = await fetch_json(session, "https://api.coinbase.com/v2/prices/ETH-USD/spot")
    if data and 'data' in data:
        return {'symbol': 'ETH/USD', 'price': float(data['data']['amount']), 'source': 'Coinbase'}
    return None

async def get_forex_ecb(session):
    """EUR/USD, GBP/USD, USD/JPY from ECB (free, no key)."""
    data = await fetch_json(session, "https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,JPY,CHF,CAD,AUD")
    if data and 'rates' in data:
        results = []
        rates = data['rates']
        if 'EUR' in rates:
            results.append({'symbol': 'EUR/USD', 'price': round(1/rates['EUR'], 5), 'source': 'ECB'})
        if 'GBP' in rates:
            results.append({'symbol': 'GBP/USD', 'price': round(1/rates['GBP'], 5), 'source': 'ECB'})
        if 'JPY' in rates:
            results.append({'symbol': 'USD/JPY', 'price': round(rates['JPY'], 3), 'source': 'ECB'})
        if 'CHF' in rates:
            results.append({'symbol': 'USD/CHF', 'price': round(rates['CHF'], 5), 'source': 'ECB'})
        if 'CAD' in rates:
            results.append({'symbol': 'USD/CAD', 'price': round(rates['CAD'], 5), 'source': 'ECB'})
        if 'AUD' in rates:
            results.append({'symbol': 'AUD/USD', 'price': round(1/rates['AUD'], 5), 'source': 'ECB'})
        return results
    return []

async def get_metals_price(session):
    """Gold/Silver from free metals API."""
    # Try multiple free sources
    # Source 1: metals.live
    data = await fetch_json(session, "https://api.metals.live/v1/spot")
    if data and isinstance(data, list):
        results = []
        for item in data:
            if item.get('gold'):
                results.append({'symbol': 'Gold (XAU)', 'price': float(item['gold']), 'source': 'metals.live'})
            if item.get('silver'):
                results.append({'symbol': 'Silver (XAG)', 'price': float(item['silver']), 'source': 'metals.live'})
        if results:
            return results

    # Source 2: frankfurter for gold via proxy
    data = await fetch_json(session, "https://api.frankfurter.app/latest?from=XAU&to=USD")
    if data and 'rates' in data and 'USD' in data['rates']:
        return [{'symbol': 'Gold (XAU)', 'price': float(data['rates']['USD']), 'source': 'ECB'}]

    return []

async def get_fear_greed(session):
    """Crypto Fear & Greed Index."""
    data = await fetch_json(session, "https://api.alternative.me/fng/?limit=1")
    if data and 'data' in data and len(data['data']) > 0:
        d = data['data'][0]
        return {'value': int(d['value']), 'classification': d['value_classification']}
    return None

async def get_coingecko_data(session):
    """Top crypto from CoinGecko (free, no key, 10-50 calls/min)."""
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,cardano,ripple&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
    data = await fetch_json(session, url)
    if data:
        results = []
        name_map = {
            'bitcoin': 'BTC', 'ethereum': 'ETH', 'solana': 'SOL',
            'cardano': 'ADA', 'ripple': 'XRP'
        }
        for cid, symbol in name_map.items():
            if cid in data:
                item = data[cid]
                results.append({
                    'symbol': f'{symbol}/USD',
                    'price': item.get('usd', 0),
                    'change_24h': item.get('usd_24h_change', 0),
                    'market_cap': item.get('usd_market_cap', 0),
                    'source': 'CoinGecko'
                })
        return results
    return []

async def get_stock_indices_google(session):
    """Try to get major indices from multiple free sources."""
    results = []

    # Source: Yahoo Finance v8 API (direct, not yfinance library)
    symbols = {
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ',
        '^DJI': 'Dow Jones',
        '^RUT': 'Russell 2000',
        '^VIX': 'VIX',
        '^FTSE': 'FTSE 100',
        '^N225': 'Nikkei 225',
    }

    for yf_symbol, name in symbols.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}?interval=1d&range=2d"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        data = await fetch_json(session, url, headers=headers, timeout=8)
        if data and 'chart' in data and 'result' in data['chart']:
            try:
                result = data['chart']['result'][0]
                meta = result['meta']
                price = meta.get('regularMarketPrice', 0)
                prev = meta.get('chartPreviousClose', 0)
                change_pct = ((price - prev) / prev * 100) if prev else 0
                results.append({
                    'symbol': name,
                    'price': round(price, 2),
                    'change_pct': round(change_pct, 2),
                    'source': 'Yahoo'
                })
            except Exception as e:
                logger.warning(f"Parse error for {name}: {e}")

    return results

async def get_commodity_yahoo(session):
    """Commodities from Yahoo v8 API."""
    results = []
    symbols = {
        'GC=F': 'Gold',
        'SI=F': 'Silver',
        'CL=F': 'WTI Crude',
        'BZ=F': 'Brent Crude',
        'NG=F': 'Natural Gas',
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for yf_symbol, name in symbols.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}?interval=1d&range=2d"
        data = await fetch_json(session, url, headers=headers, timeout=8)
        if data and 'chart' in data and 'result' in data['chart']:
            try:
                meta = data['chart']['result'][0]['meta']
                price = meta.get('regularMarketPrice', 0)
                prev = meta.get('chartPreviousClose', 0)
                change_pct = ((price - prev) / prev * 100) if prev else 0
                results.append({
                    'symbol': name,
                    'price': round(price, 2),
                    'change_pct': round(change_pct, 2),
                    'source': 'Yahoo'
                })
            except:
                pass

    return results

async def get_treasury_yields(session):
    """US Treasury yields from FRED (free, no key for basic)."""
    results = []
    # Try Treasury.gov XML or use a simple proxy
    series = {'DGS2': '2Y', 'DGS10': '10Y', 'DGS30': '30Y'}

    for series_id, label in series.items():
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&sort_order=desc&limit=1&file_type=json&api_key=DEMO_KEY"
        data = await fetch_json(session, url, timeout=8)
        if data and 'observations' in data and len(data['observations']) > 0:
            try:
                val = data['observations'][0]['value']
                if val != '.':
                    results.append({'symbol': f'US {label} Yield', 'price': float(val), 'source': 'FRED'})
            except:
                pass

    return results

async def fetch_all_market_data():
    """Fetch all market data concurrently from multiple free sources."""
    logger.info("🔄 Fetching market data from multiple free sources...")

    async with aiohttp.ClientSession() as session:
        # Launch all fetches concurrently
        tasks = {
            'indices': get_stock_indices_google(session),
            'commodities_yahoo': get_commodity_yahoo(session),
            'metals': get_metals_price(session),
            'crypto': get_coingecko_data(session),
            'forex': get_forex_ecb(session),
            'fear_greed': get_fear_greed(session),
            'yields': get_treasury_yields(session),
            'btc': get_coinbase_btc(session),
            'eth': get_coinbase_eth(session),
        }

        results = {}
        for key, coro in tasks.items():
            try:
                results[key] = await coro
            except Exception as e:
                logger.error(f"Error fetching {key}: {e}")
                results[key] = None

    # Compile market data
    market_data = {
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'indices': results.get('indices') or [],
        'commodities': [],
        'crypto': [],
        'forex': results.get('forex') or [],
        'yields': results.get('yields') or [],
        'fear_greed': results.get('fear_greed'),
    }

    # Merge commodities
    commod_yahoo = results.get('commodities_yahoo') or []
    metals = results.get('metals') or []
    market_data['commodities'] = commod_yahoo if commod_yahoo else []
    # Add metals if not already from yahoo
    metal_names = {c['symbol'] for c in market_data['commodities']}
    for m in metals:
        if m['symbol'] not in metal_names:
            market_data['commodities'].append(m)

    # Merge crypto
    crypto_cg = results.get('crypto') or []
    market_data['crypto'] = crypto_cg
    # If CoinGecko failed, use Coinbase
    crypto_symbols = {c['symbol'] for c in market_data['crypto']}
    if results.get('btc') and 'BTC/USD' not in crypto_symbols:
        market_data['crypto'].insert(0, results['btc'])
    if results.get('eth') and 'ETH/USD' not in crypto_symbols:
        market_data['crypto'].insert(1, results['eth'])

    # Count successes
    total = sum(len(v) for v in [market_data['indices'], market_data['commodities'],
                                   market_data['crypto'], market_data['forex'], market_data['yields']])
    logger.info(f"✅ Fetched {total} data points total")

    return market_data

# ============================================================
# NEWS
# ============================================================

async def fetch_market_news():
    """Fetch financial news."""
    headlines = []
    async with aiohttp.ClientSession() as session:
        if NEWS_API_KEY:
            url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&pageSize=10&apiKey={NEWS_API_KEY}"
            data = await fetch_json(session, url)
            if data and 'articles' in data:
                for a in data['articles'][:10]:
                    headlines.append(a.get('title', ''))

        # Backup: Google News RSS via a JSON proxy
        if not headlines:
            try:
                import feedparser
                feed = feedparser.parse("https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB")
                for entry in feed.entries[:8]:
                    headlines.append(entry.title)
            except:
                pass

        if not headlines:
            headlines = ["Market news temporarily unavailable - analysis based on price data"]

    return headlines

# ============================================================
# ANALYSIS WITH CLAUDE
# ============================================================

def format_market_data_for_claude(data):
    """Format market data into a clean text block for Claude."""
    lines = [f"📅 Market Data as of {data['timestamp']}", ""]

    if data['indices']:
        lines.append("📊 MAJOR INDICES:")
        for item in data['indices']:
            chg = f" ({item['change_pct']:+.2f}%)" if 'change_pct' in item else ""
            lines.append(f"  • {item['symbol']}: {item['price']:,.2f}{chg}")
        lines.append("")

    if data['commodities']:
        lines.append("🏗️ COMMODITIES:")
        for item in data['commodities']:
            chg = f" ({item['change_pct']:+.2f}%)" if 'change_pct' in item else ""
            lines.append(f"  • {item['symbol']}: ${item['price']:,.2f}{chg}")
        lines.append("")

    if data['crypto']:
        lines.append("₿ CRYPTO:")
        for item in data['crypto']:
            chg = f" ({item.get('change_24h', 0):+.1f}%)" if item.get('change_24h') else ""
            lines.append(f"  • {item['symbol']}: ${item['price']:,.2f}{chg}")
        lines.append("")

    if data['forex']:
        lines.append("💱 FOREX:")
        for item in data['forex']:
            lines.append(f"  • {item['symbol']}: {item['price']}")
        lines.append("")

    if data['yields']:
        lines.append("🏦 TREASURY YIELDS:")
        for item in data['yields']:
            lines.append(f"  • {item['symbol']}: {item['price']:.3f}%")
        lines.append("")

    if data['fear_greed']:
        fg = data['fear_greed']
        lines.append(f"😱 Crypto Fear & Greed Index: {fg['value']}/100 ({fg['classification']})")
        lines.append("")

    return "\n".join(lines)

async def generate_analysis(market_data, news):
    """Generate professional analysis using Claude."""
    data_text = format_market_data_for_claude(market_data)
    news_text = "\n".join(f"  • {h}" for h in news[:8])

    prompt = f"""You are a senior market analyst at a major investment bank. Based on the following real-time market data and news, provide a comprehensive market analysis report.

{data_text}

📰 LATEST HEADLINES:
{news_text}

Generate a professional Telegram-formatted market report with these sections. Use these exact emoji headers:

📊 **MARKET OVERVIEW**
Brief summary of overall market conditions (2-3 sentences)

📈 **EQUITIES**
Analysis of stock index movements, key drivers (3-4 sentences)

🏗️ **COMMODITIES**
Gold, oil, and other commodity analysis (2-3 sentences)

₿ **CRYPTO**
Bitcoin, Ethereum, and crypto market analysis (2-3 sentences)

💱 **FOREX**
Currency market analysis (2-3 sentences)

🏦 **FIXED INCOME**
Bond yield analysis if data available (1-2 sentences)

⚡ **KEY RISKS & CATALYSTS**
Top 3 things to watch, as bullet points

🎯 **OUTLOOK**
Short-term market outlook (2-3 sentences)

Rules:
- Use **bold** for emphasis (Telegram markdown)
- Be specific with numbers from the data
- Professional but accessible tone
- Keep total length under 2500 characters
- Do NOT use headers with # markdown, use emoji + **bold**
- End with a one-line disclaimer"""

    try:
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        # Fallback: format raw data
        return f"🤖 *AI Analysis Unavailable*\n\n{data_text}\n\n_Analysis engine temporarily offline. Raw data shown above._"

# ============================================================
# TELEGRAM SENDING (handles message length limits)
# ============================================================

async def send_long_message(bot, chat_id, text, parse_mode='Markdown'):
    """Send message, splitting if too long for Telegram's 4096 char limit."""
    if len(text) <= 4096:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        return

    # Split by double newline to keep sections together
    chunks = []
    current = ""
    for paragraph in text.split("\n\n"):
        if len(current) + len(paragraph) + 2 > 4000:
            if current:
                chunks.append(current)
            current = paragraph
        else:
            current = current + "\n\n" + paragraph if current else paragraph
    if current:
        chunks.append(current)

    for chunk in chunks:
        try:
            await bot.send_message(chat_id=chat_id, text=chunk, parse_mode=parse_mode)
        except Exception:
            # If markdown fails, send as plain text
            await bot.send_message(chat_id=chat_id, text=chunk)
        await asyncio.sleep(0.5)

# ============================================================
# MAIN ANALYSIS FLOW
# ============================================================

async def generate_and_send_report(bot):
    """Complete flow: fetch data → analyze → send."""
    try:
        logger.info("🔄 Starting market analysis pipeline...")

        # Fetch data and news concurrently
        market_data, news = await asyncio.gather(
            fetch_all_market_data(),
            fetch_market_news()
        )

        # Check if we have any data
        total_points = sum(len(v) for k, v in market_data.items()
                         if isinstance(v, list))
        if total_points == 0:
            await bot.send_message(
                chat_id=CHAT_ID,
                text="⚠️ *Market Data Temporarily Unavailable*\n\nAll data sources returned errors. Will retry at next scheduled time.",
                parse_mode='Markdown'
            )
            return

        logger.info(f"📊 Got {total_points} data points, generating analysis...")

        # Generate AI analysis
        analysis = await generate_analysis(market_data, news)

        # Send to Telegram
        await send_long_message(bot, CHAT_ID, analysis)
        logger.info("✅ Report sent successfully!")

    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}", exc_info=True)
        try:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"⚠️ Analysis error: {str(e)[:200]}"
            )
        except:
            pass

# ============================================================
# COMMAND HANDLERS
# ============================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *Professional Market Analysis Bot*\n\n"
        "Commands:\n"
        "/report - Generate full market analysis\n"
        "/status - Check bot & data source status\n"
        "/markets - Quick price snapshot\n\n"
        "📅 Auto-reports every 4 hours",
        parse_mode='Markdown'
    )

async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🔄 Generating analysis... (30-60 seconds)")
    await generate_and_send_report(context.bot)
    try:
        await msg.delete()
    except:
        pass

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check which data sources are working."""
    status_msg = await update.message.reply_text("🔍 Testing data sources...")

    results = []
    async with aiohttp.ClientSession() as session:
        # Test each source
        tests = [
            ("Yahoo Finance API", get_stock_indices_google(session)),
            ("CoinGecko", get_coingecko_data(session)),
            ("Coinbase", get_coinbase_btc(session)),
            ("ECB Forex", get_forex_ecb(session)),
            ("Metals API", get_metals_price(session)),
            ("FRED Yields", get_treasury_yields(session)),
        ]

        for name, coro in tests:
            try:
                result = await coro
                if result:
                    count = len(result) if isinstance(result, list) else 1
                    results.append(f"✅ {name}: {count} items")
                else:
                    results.append(f"❌ {name}: No data")
            except Exception as e:
                results.append(f"❌ {name}: {str(e)[:30]}")

    status = "\n".join(results)
    await status_msg.edit_text(
        f"📡 *Data Source Status*\n\n{status}\n\n🕐 {datetime.now(timezone.utc).strftime('%H:%M UTC')}",
        parse_mode='Markdown'
    )

async def cmd_markets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick price snapshot without AI analysis."""
    msg = await update.message.reply_text("📊 Fetching prices...")
    data = await fetch_all_market_data()
    text = format_market_data_for_claude(data)
    await msg.edit_text(text)

# ============================================================
# SCHEDULED JOB
# ============================================================

async def scheduled_update():
    logger.info("⏰ Scheduled update triggered")
    bot = Bot(token=TELEGRAM_TOKEN)
    await generate_and_send_report(bot)

# ============================================================
# MAIN
# ============================================================

def main():
    logger.info("=" * 60)
    logger.info("🚀 PROFESSIONAL MARKET ANALYSIS BOT v2.0")
    logger.info("=" * 60)
    logger.info("✅ Multi-source market data (no yfinance)")
    logger.info("✅ AI-Powered Analysis (Claude)")
    logger.info("✅ Sources: Yahoo API, CoinGecko, Coinbase, ECB, FRED")
    logger.info("=" * 60)

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("markets", cmd_markets))

    scheduler = AsyncIOScheduler(timezone='UTC')
    scheduler.add_job(scheduled_update, 'interval', hours=4, next_run_time=datetime.now(timezone.utc))
    scheduler.start()
    logger.info("✅ Scheduler started (4-hour intervals)")

    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
