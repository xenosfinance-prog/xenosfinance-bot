#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROFESSIONAL MARKET ANALYSIS BOT
Complete financial analysis with AI-powered insights
Uses: Multi-API + Claude AI for sentiment and analysis
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import requests
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== CONFIG =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHANNEL_ID')
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY') or os.getenv('ALPHAVANTAGE_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')  # Claude API key
NEWS_API_KEY = os.getenv('NEWS_API_KEY', 'demo')  # Optional - NewsAPI.org

UPDATE_INTERVAL_HOURS = 4
CACHE_FILE = 'market_cache.json'

# Eastern Time for market hours
ET = ZoneInfo("America/New_York")

# ===== MARKET SYMBOLS =====
MARKET_SYMBOLS = {
    'futures': {
        'ES=F': 'S&P 500',
        'NQ=F': 'Nasdaq',
        'YM=F': 'Dow Jones',
        'RTY=F': 'Russell 2000',
    },
    'commodities': {
        'GC=F': 'Gold',
        'CL=F': 'WTI Crude',
        'BZ=F': 'Brent Crude',
        'SI=F': 'Silver',
        'NG=F': 'Nat Gas',
        'HG=F': 'Copper',
    },
    'forex': {
        'EURUSD=X': 'EUR/USD',
        'GBPUSD=X': 'GBP/USD',
        'USDJPY=X': 'USD/JPY',
        'USDCHF=X': 'USD/CHF',
        'AUDUSD=X': 'AUD/USD',
    },
    'indices': {
        '^VIX': 'VIX',
        'DX-Y.NYB': 'DXY',
    },
    'crypto': {
        'BTC-USD': 'Bitcoin',
        'ETH-USD': 'Ethereum',
        'SOL-USD': 'Solana',
    }
}


# ===== CACHE =====
def load_cache() -> Dict:
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}


def save_cache(data: Dict):
    try:
        data['_last_update'] = datetime.now().isoformat()
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info("✅ Cache saved")
    except Exception as e:
        logger.error(f"Cache error: {e}")


# ===== MARKET HOURS =====
def get_market_status() -> Dict:
    """Get current market status"""
    now = datetime.now(ET)
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    hour = now.hour
    minute = now.minute
    
    # Weekend
    if weekday >= 5:  # Saturday or Sunday
        return {
            'status': 'WEEKEND',
            'message': 'Markets Closed - Weekend',
            'next_open': 'Monday 9:30 AM ET'
        }
    
    # Regular trading hours: 9:30 AM - 4:00 PM ET
    if hour == 9 and minute >= 30 or 10 <= hour < 16:
        time_to_close = datetime(now.year, now.month, now.day, 16, 0, tzinfo=ET) - now
        hours = int(time_to_close.total_seconds() // 3600)
        mins = int((time_to_close.total_seconds() % 3600) // 60)
        return {
            'status': 'MARKET_OPEN',
            'message': 'Active trading session',
            'next_event': f'MARKET CLOSE in {hours}h {mins}m'
        }
    
    # Pre-market: 4:00 AM - 9:30 AM ET
    elif 4 <= hour < 9 or (hour == 9 and minute < 30):
        return {
            'status': 'PRE_MARKET',
            'message': 'Pre-market trading',
            'next_event': 'MARKET OPEN at 9:30 AM ET'
        }
    
    # Post-market: 4:00 PM - 8:00 PM ET
    elif 16 <= hour < 20:
        return {
            'status': 'POST_MARKET',
            'message': 'After-hours trading',
            'next_event': 'Extended hours until 8:00 PM ET'
        }
    
    # Closed overnight
    else:
        return {
            'status': 'MARKET_CLOSED',
            'message': 'Markets Closed',
            'next_event': 'PRE-MARKET opens at 4:00 AM ET'
        }


# ===== FETCH PRICES (MINIMAL - Using yfinance with heavy delays) =====
def fetch_price_yfinance(symbol: str, retries: int = 2) -> Optional[Dict]:
    """Fetch price from yfinance with extreme caution"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        
        # Try history first (most reliable)
        hist = ticker.history(period='5d')
        if not hist.empty:
            current = float(hist['Close'].iloc[-1])
            prev = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else current
            week_ago = float(hist['Close'].iloc[0]) if len(hist) >= 5 else prev
            
            change = current - prev
            change_pct = (change / prev * 100) if prev != 0 else 0
            week_change_pct = ((current - week_ago) / week_ago * 100) if week_ago != 0 else 0
            
            return {
                'price': current,
                'change': change,
                'change_percent': change_pct,
                'week_change_percent': week_change_pct,
                'source': 'yfinance'
            }
    except Exception as e:
        logger.error(f"YFinance error {symbol}: {e}")
        
    return None


# ===== CRYPTO (CoinGecko) =====
def fetch_crypto_coingecko(coin_id: str) -> Optional[Dict]:
    """Fetch crypto from CoinGecko"""
    try:
        # Map symbols to CoinGecko IDs
        mapping = {
            'BTC-USD': 'bitcoin',
            'ETH-USD': 'ethereum',
            'SOL-USD': 'solana',
        }
        
        cg_id = mapping.get(coin_id, coin_id.replace('-USD', '').lower())
        
        url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {
            'ids': cg_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_7d_change': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if cg_id in data:
            price = data[cg_id]['usd']
            change_24h = data[cg_id].get('usd_24h_change', 0)
            change_7d = data[cg_id].get('usd_7d_change', 0)
            
            return {
                'price': price,
                'change_percent': change_24h,
                'week_change_percent': change_7d,
                'source': 'CoinGecko'
            }
    except Exception as e:
        logger.error(f"CoinGecko error {coin_id}: {e}")
    
    return None


# ===== FETCH ALL MARKETS =====
def fetch_all_market_data() -> Dict:
    """Fetch all market data with heavy rate limiting"""
    logger.info("\n" + "="*60)
    logger.info("🔄 FETCHING MARKET DATA")
    logger.info("="*60)
    
    all_data = {}
    
    for category, symbols in MARKET_SYMBOLS.items():
        logger.info(f"\n📊 {category.upper()}")
        all_data[category] = {}
        
        for symbol, name in symbols.items():
            logger.info(f"  {name}...")
            
            data = None
            
            # Use CoinGecko for crypto
            if category == 'crypto':
                data = fetch_crypto_coingecko(symbol)
                time.sleep(2)
            else:
                # Use yfinance with EXTREME caution
                data = fetch_price_yfinance(symbol)
                time.sleep(15)  # 15 seconds between each call!
            
            if data:
                all_data[category][symbol] = {'name': name, **data}
                logger.info(f"    ✅ ${data['price']:,.2f}")
            else:
                # Try cache
                cache = load_cache()
                if category in cache and symbol in cache[category]:
                    all_data[category][symbol] = {**cache[category][symbol], 'cached': True}
                    logger.info(f"    📦 Using cache")
                else:
                    all_data[category][symbol] = {'name': name, 'price': 0, 'error': True}
                    logger.warning(f"    ❌ Failed")
    
    logger.info("\n✅ DATA FETCH COMPLETED\n")
    return all_data


# ===== NEWS FETCHING =====
def fetch_financial_news() -> List[str]:
    """Fetch top financial news"""
    if NEWS_API_KEY == 'demo':
        # Default news if no API key
        return [
            "Fed maintains current interest rate stance",
            "Global markets await inflation data",
            "Geopolitical tensions impact energy sector",
            "EU ECB navigating growth concerns",
            "Asia markets mixed amid China stimulus"
        ]
    
    try:
        url = 'https://newsapi.org/v2/top-headlines'
        params = {
            'category': 'business',
            'language': 'en',
            'pageSize': 5,
            'apiKey': NEWS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == 'ok' and data.get('articles'):
            return [article['title'] for article in data['articles'][:5]]
    except Exception as e:
        logger.error(f"News API error: {e}")
    
    return fetch_financial_news()  # Fallback to defaults


# ===== CLAUDE AI ANALYSIS =====
def generate_ai_analysis(market_data: Dict) -> Dict:
    """Generate professional analysis using Claude API"""
    
    if not ANTHROPIC_API_KEY:
        logger.warning("No Anthropic API key - using default analysis")
        return {
            'sentiment': 'NEUTRAL',
            'sentiment_desc': 'Markets showing mixed signals',
            'overview': {
                'US': 'Fed policy remains data-dependent, inflation trending toward target',
                'EU': 'ECB navigating growth concerns amid rate normalization',
                'ASIA': 'China economic stimulus measures supporting growth',
                'COMMODITIES': 'Energy markets sensitive to geopolitical developments'
            }
        }
    
    try:
        # Prepare market summary for Claude
        summary = f"""Current market data:
Futures: S&P {market_data['futures'].get('ES=F', {}).get('price', 0):.2f} ({market_data['futures'].get('ES=F', {}).get('change_percent', 0):+.2f}%)
Nasdaq: {market_data['futures'].get('NQ=F', {}).get('price', 0):.2f} ({market_data['futures'].get('NQ=F', {}).get('change_percent', 0):+.2f}%)
VIX: {market_data['indices'].get('^VIX', {}).get('price', 0):.2f}
Gold: ${market_data['commodities'].get('GC=F', {}).get('price', 0):.2f}
Bitcoin: ${market_data['crypto'].get('BTC-USD', {}).get('price', 0):,.0f}
"""
        
        # Call Claude API
        headers = {
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        
        payload = {
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 500,
            'messages': [{
                'role': 'user',
                'content': f"""{summary}

Provide a brief professional market analysis with:
1. Overall sentiment (BULLISH/BEARISH/NEUTRAL) with one-line description
2. US economic outlook (1 sentence)
3. EU economic outlook (1 sentence)  
4. Asia economic outlook (1 sentence)
5. Commodities outlook (1 sentence)

Format as JSON:
{{
  "sentiment": "BULLISH|BEARISH|NEUTRAL",
  "sentiment_desc": "one line description",
  "us": "sentence",
  "eu": "sentence",
  "asia": "sentence",
  "commodities": "sentence"
}}"""
            }]
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['content'][0]['text']
            
            # Parse JSON from Claude's response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return {
                    'sentiment': analysis.get('sentiment', 'NEUTRAL'),
                    'sentiment_desc': analysis.get('sentiment_desc', 'Mixed signals'),
                    'overview': {
                        'US': analysis.get('us', 'Economic data pending'),
                        'EU': analysis.get('eu', 'Policy normalization ongoing'),
                        'ASIA': analysis.get('asia', 'Growth measures in place'),
                        'COMMODITIES': analysis.get('commodities', 'Market sensitive to developments')
                    }
                }
        
        logger.warning(f"Claude API returned {response.status_code}")
        
    except Exception as e:
        logger.error(f"Claude API error: {e}")
    
    # Fallback to default
    return generate_ai_analysis({})


# ===== FORMAT MESSAGE =====
def format_professional_message(data: Dict, analysis: Dict, news: List[str]) -> str:
    """Format the complete professional market analysis message"""
    
    market_status = get_market_status()
    now_et = datetime.now(ET)
    
    msg = []
    
    # Header
    msg.append("╔══════════════════════════════════╗")
    msg.append("    <b>PROFESSIONAL MARKET ANALYSIS</b>")
    msg.append("╚══════════════════════════════════╝")
    msg.append(f"📅 {now_et.strftime('%Y-%m-%d %H:%M ET (%A)')}")
    msg.append("")
    msg.append(f"<b>{market_status['status']}</b> - {market_status['message']}")
    msg.append(f"Next: {market_status['next_event']}")
    msg.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Market Sentiment
    sentiment = analysis.get('sentiment', 'NEUTRAL')
    sentiment_emoji = "🔴" if sentiment == "BEARISH" else "🟢" if sentiment == "BULLISH" else "⚪"
    msg.append(f"<b>MARKET SENTIMENT</b>")
    msg.append(f"{sentiment_emoji} <b>{sentiment}</b> - {analysis.get('sentiment_desc', 'Mixed signals')}")
    msg.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # US Futures
    msg.append("<b>🇺🇸 US FUTURES</b>")
    for symbol, name in [('ES=F', 'S&P 500'), ('NQ=F', 'Nasdaq'), ('YM=F', 'Dow Jones'), ('RTY=F', 'Russell 2000')]:
        d = data['futures'].get(symbol, {})
        price = d.get('price', 0)
        change = d.get('change_percent', 0)
        week = d.get('week_change_percent', 0)
        
        if price > 0:
            msg.append(f"{name}: {price:,.2f} ({change:+.2f}%) | Week: {week:+.2f}%")
        else:
            msg.append(f"{name}: N/A")
    
    msg.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Commodities
    msg.append("<b>🏅 COMMODITIES</b>")
    
    gold = data['commodities'].get('GC=F', {})
    if gold.get('price'):
        g_price = gold['price']
        g_change = gold.get('change_percent', 0)
        g_week = gold.get('week_change_percent', 0)
        msg.append(f"Gold: ${g_price:,.2f}/oz ({g_change:+.2f}%)")
        msg.append(f"  └─ Weekly: {g_week:+.2f}% | Safe-haven {'rising' if g_change > 0 else 'falling'}")
    
    wti = data['commodities'].get('CL=F', {})
    brent = data['commodities'].get('BZ=F', {})
    if wti.get('price') or brent.get('price'):
        msg.append("")
        if wti.get('price'):
            msg.append(f"WTI Crude: ${wti['price']:,.2f}/bbl ({wti.get('change_percent', 0):+.2f}%)")
        if brent.get('price'):
            msg.append(f"Brent Crude: ${brent['price']:,.2f}/bbl ({brent.get('change_percent', 0):+.2f}%)")
        msg.append(f"  └─ Energy sector showing {'strength' if wti.get('change_percent', 0) > 0 else 'weakness'}")
    
    msg.append("")
    for symbol, name in [('SI=F', 'Silver'), ('NG=F', 'Nat Gas'), ('HG=F', 'Copper')]:
        d = data['commodities'].get(symbol, {})
        if d.get('price'):
            msg.append(f"{name}: ${d['price']:,.2f} ({d.get('change_percent', 0):+.2f}%)")
    
    msg.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Forex
    msg.append("<b>💱 FOREX MAJORS</b>")
    for symbol, name in MARKET_SYMBOLS['forex'].items():
        d = data['forex'].get(symbol, {})
        if d.get('price'):
            price = d['price']
            change = d.get('change_percent', 0)
            week = d.get('week_change_percent', 0)
            msg.append(f"{name}: {price:.4f} ({change:+.2f}%) | 5D: {week:+.2f}%")
        else:
            msg.append(f"{name}: N/A")
    
    msg.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Key Indicators
    msg.append("<b>📊 KEY INDICATORS</b>")
    
    vix = data['indices'].get('^VIX', {})
    if vix.get('price'):
        vix_level = "High" if vix['price'] > 20 else "Moderate" if vix['price'] > 15 else "Low"
        msg.append(f"VIX (Fear Index): {vix['price']:.2f} ({vix.get('change_percent', 0):+.2f}%)")
        msg.append(f"  └─ Volatility: {vix_level}")
    
    dxy = data['indices'].get('DX-Y.NYB', {})
    if dxy.get('price'):
        dxy_trend = "Strengthening" if dxy.get('change_percent', 0) > 0 else "Weakening"
        msg.append(f"DXY (Dollar Index): {dxy['price']:.2f} ({dxy.get('change_percent', 0):+.2f}%)")
        msg.append(f"  └─ USD: {dxy_trend}")
    
    msg.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Crypto
    msg.append("<b>₿ CRYPTOCURRENCY</b>")
    for symbol, name in MARKET_SYMBOLS['crypto'].items():
        d = data['crypto'].get(symbol, {})
        if d.get('price'):
            price = d['price']
            change = d.get('change_percent', 0)
            week = d.get('week_change_percent', 0)
            msg.append(f"{name}: ${price:,.2f} ({change:+.2f}%) | Week: {week:+.2f}%")
        else:
            msg.append(f"{name}: N/A")
    
    msg.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # News
    msg.append("<b>📰 TOP FINANCIAL NEWS</b>")
    for item in news[:5]:
        msg.append(f"• {item}")
    
    msg.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Macro Overview
    msg.append("<b>🌍 MACRO ECONOMIC OVERVIEW</b>")
    overview = analysis.get('overview', {})
    msg.append(f"• <b>US:</b> {overview.get('US', 'N/A')}")
    msg.append(f"• <b>EU:</b> {overview.get('EU', 'N/A')}")
    msg.append(f"• <b>ASIA:</b> {overview.get('ASIA', 'N/A')}")
    msg.append(f"• <b>COMMODITIES:</b> {overview.get('COMMODITIES', 'N/A')}")
    
    msg.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Disclaimer
    msg.append("<b>⚠️ RISK DISCLAIMER</b>")
    msg.append("<i>This analysis is for informational purposes only.")
    msg.append("Not financial advice. Always DYOR.</i>")
    
    return "\n".join(msg)


# ===== MAIN UPDATE FUNCTION =====
def generate_complete_update() -> str:
    """Generate complete professional market update"""
    logger.info("🔄 Generating complete market analysis...")
    
    # 1. Fetch market data
    market_data = fetch_all_market_data()
    
    # 2. Get news
    news = fetch_financial_news()
    
    # 3. Generate AI analysis
    analysis = generate_ai_analysis(market_data)
    
    # 4. Save to cache
    save_cache(market_data)
    
    # 5. Format message
    message = format_professional_message(market_data, analysis, news)
    
    logger.info("✅ Complete analysis generated")
    
    return message


# ===== TELEGRAM COMMANDS =====
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 <b>Professional Market Analysis Bot</b>\n\n"
        "AI-powered financial market analysis\n\n"
        "Commands:\n"
        "/update - Get latest analysis\n"
        "/status - Bot status\n"
        "/market - Current market hours\n\n"
        f"⏰ Auto-updates every {UPDATE_INTERVAL_HOURS}h",
        parse_mode='HTML'
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cache = load_cache()
    last_update = cache.get('_last_update', 'Never')
    
    if last_update != 'Never':
        last_update = datetime.fromisoformat(last_update).strftime('%Y-%m-%d %H:%M')
    
    msg = (
        f"✅ <b>Bot Active</b>\n\n"
        f"📅 Last update: {last_update}\n"
        f"🔄 Interval: {UPDATE_INTERVAL_HOURS}h\n"
        f"🔑 Claude AI: {'✅' if ANTHROPIC_API_KEY else '❌'}\n"
        f"📰 News API: {'✅' if NEWS_API_KEY != 'demo' else '❌ (using defaults)'}"
    )
    
    await update.message.reply_text(msg, parse_mode='HTML')


async def cmd_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_market_status()
    msg = (
        f"<b>Market Status</b>\n\n"
        f"Status: {status['status']}\n"
        f"{status['message']}\n\n"
        f"Next: {status['next_event']}"
    )
    await update.message.reply_text(msg, parse_mode='HTML')


async def cmd_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔄 Generating professional market analysis...\n"
        "⏱️ This may take 3-5 minutes due to rate limiting."
    )
    
    try:
        message = generate_complete_update()
        await update.message.reply_text(message, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Update error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:200]}")


# ===== SCHEDULED UPDATE =====
async def scheduled_update(context: ContextTypes.DEFAULT_TYPE):
    logger.info("⏰ Scheduled update triggered")
    
    try:
        message = generate_complete_update()
        await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        logger.info("✅ Scheduled update sent")
    except Exception as e:
        logger.error(f"❌ Scheduled update error: {e}")


# ===== MAIN =====
def main():
    logger.info("\n" + "="*60)
    logger.info("🚀 PROFESSIONAL MARKET ANALYSIS BOT")
    logger.info("="*60)
    logger.info("✅ Multi-API Market Data")
    logger.info("✅ AI-Powered Analysis (Claude)")
    logger.info("✅ Professional Financial Reporting")
    logger.info("="*60 + "\n")
    
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("❌ Missing BOT_TOKEN or CHAT_ID!")
        return
    
    logger.info(f"✅ Token: {BOT_TOKEN[:10]}...")
    logger.info(f"✅ Chat: {CHAT_ID}")
    logger.info(f"✅ Claude API: {'Configured' if ANTHROPIC_API_KEY else 'MISSING - Using defaults'}")
    logger.info(f"✅ News API: {'Configured' if NEWS_API_KEY != 'demo' else 'Using defaults'}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("market", cmd_market))
    app.add_handler(CommandHandler("update", cmd_update))
    
    app.job_queue.run_repeating(
        scheduled_update,
        interval=UPDATE_INTERVAL_HOURS * 3600,
        first=120  # First update after 2 minutes
    )
    
    logger.info("✅ Ready\n" + "="*60 + "\n")
    
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == '__main__':
    main()
