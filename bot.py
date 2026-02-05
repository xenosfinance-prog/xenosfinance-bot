#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPLETE HYBRID MARKET BOT - PRODUCTION READY
Zero Yahoo Finance, Zero Rate Limiting
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import requests

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== CONFIG =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')

UPDATE_INTERVAL_HOURS = 4
CACHE_FILE = 'market_cache.json'

# ===== SIMBOLI =====
MARKET_SYMBOLS = {
    'Futures Indici': {
        'SPY': 'S&P 500 (ETF)',
        'QQQ': 'Nasdaq 100 (ETF)',
        'DIA': 'Dow Jones (ETF)',
    },
    'Materie Prime': {
        'GLD': 'Gold (ETF)',
        'SLV': 'Silver (ETF)', 
        'USO': 'Oil (ETF)',
        'UNG': 'Natural Gas (ETF)',
    },
    'Crypto': {
        'bitcoin': 'Bitcoin',
        'ethereum': 'Ethereum',
        'solana': 'Solana',
    },
    'Forex': {
        'eur': 'EUR/USD',
        'gbp': 'GBP/USD',
        'jpy': 'USD/JPY',
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
        logger.error(f"Cache save error: {e}")


def is_cache_valid(cache: Dict, hours: int = UPDATE_INTERVAL_HOURS) -> bool:
    if not cache or '_last_update' not in cache:
        return False
    try:
        last = datetime.fromisoformat(cache['_last_update'])
        return datetime.now() - last < timedelta(hours=hours)
    except:
        return False


# ===== ALPHA VANTAGE =====
def fetch_alpha_vantage(symbol: str) -> Optional[Dict]:
    if not ALPHA_VANTAGE_KEY:
        return None
    
    try:
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if 'Global Quote' in data and data['Global Quote']:
            quote = data['Global Quote']
            price = float(quote.get('05. price', 0))
            change_pct = float(quote.get('10. change percent', '0').replace('%', ''))
            
            if price > 0:
                return {
                    'price': price,
                    'change_percent': change_pct,
                    'source': 'AlphaVantage'
                }
    except Exception as e:
        logger.error(f"AlphaVantage error {symbol}: {e}")
    
    return None


# ===== COINGECKO =====
def fetch_crypto_coingecko(coin_id: str) -> Optional[Dict]:
    try:
        url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {
            'ids': coin_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if coin_id in data:
            return {
                'price': data[coin_id]['usd'],
                'change_percent': data[coin_id].get('usd_24h_change', 0),
                'source': 'CoinGecko'
            }
    except Exception as e:
        logger.error(f"CoinGecko error {coin_id}: {e}")
    
    return None


# ===== FOREX =====
def fetch_forex(base: str) -> Optional[Dict]:
    try:
        currencies_map = {
            'eur': ('EUR', False),
            'gbp': ('GBP', False),
            'jpy': ('JPY', True),
            'aud': ('AUD', False),
        }
        
        if base.lower() not in currencies_map:
            return None
        
        currency, is_inverse = currencies_map[base.lower()]
        
        url = 'https://open.er-api.com/v6/latest/USD'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'rates' in data and currency in data['rates']:
            rate = data['rates'][currency]
            price = rate if is_inverse else 1 / rate
            
            return {
                'price': price,
                'change_percent': 0,
                'source': 'ExchangeRate'
            }
    except Exception as e:
        logger.error(f"Forex error {base}: {e}")
    
    return None


# ===== UPDATE =====
def update_all_markets() -> Dict:
    logger.info("\n" + "="*60)
    logger.info("🔄 MARKET UPDATE - MULTI-API MODE")
    logger.info("="*60)
    
    all_data = {}
    av_calls = 0
    max_av = 20
    
    for category, symbols in MARKET_SYMBOLS.items():
        logger.info(f"\n📊 {category}")
        all_data[category] = {}
        
        for symbol, name in symbols.items():
            logger.info(f"  {name}...")
            data = None
            
            if category == 'Crypto':
                data = fetch_crypto_coingecko(symbol)
                time.sleep(2)
            elif category == 'Forex':
                data = fetch_forex(symbol)
                time.sleep(1)
            else:  # Futures/Commodities
                if av_calls < max_av:
                    data = fetch_alpha_vantage(symbol)
                    av_calls += 1
                    time.sleep(12)
            
            if data:
                all_data[category][symbol] = {'name': name, **data}
                price = data['price']
                change = data.get('change_percent', 0)
                
                if price < 1:
                    p = f"${price:.4f}"
                elif price < 100:
                    p = f"${price:.2f}"
                else:
                    p = f"${price:,.2f}"
                
                logger.info(f"    ✅ {p} ({change:+.2f}%)")
            else:
                cache = load_cache()
                if category in cache and symbol in cache[category]:
                    all_data[category][symbol] = {**cache[category][symbol], 'from_cache': True}
                    logger.info(f"    📦 Cached")
                else:
                    all_data[category][symbol] = {'name': name, 'price': None}
                    logger.warning(f"    ❌ Failed")
    
    logger.info(f"\n✅ COMPLETED | AV calls: {av_calls}/{max_av}")
    logger.info("="*60 + "\n")
    
    return all_data


# ===== FORMAT =====
def format_message(data: Dict) -> str:
    parts = ["📊 <b>MERCATI FINANZIARI</b>\n"]
    parts.append(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
    
    for category, symbols in data.items():
        if category.startswith('_'):
            continue
        
        parts.append(f"\n<b>━━━ {category.upper()} ━━━</b>")
        
        for symbol, info in symbols.items():
            name = info.get('name', symbol)
            price = info.get('price')
            
            if price is None:
                parts.append(f"⚪ {name}: <i>N/A</i>")
                continue
            
            change = info.get('change_percent', 0)
            emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
            sign = "+" if change > 0 else ""
            cached = " 📦" if info.get('from_cache') else ""
            
            if price < 1:
                p = f"${price:.4f}"
            elif price < 100:
                p = f"${price:.2f}"
            else:
                p = f"${price:,.2f}"
            
            if change != 0:
                parts.append(f"{emoji} <b>{name}</b>{cached}\n   {p} ({sign}{change:.2f}%)")
            else:
                parts.append(f"{emoji} <b>{name}</b>{cached}\n   {p}")
    
    parts.append(f"\n━━━━━━━━━━━━━━━━━")
    parts.append(f"Prossimo: {UPDATE_INTERVAL_HOURS}h")
    
    return "\n".join(parts)


# ===== COMMANDS =====
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Market Bot Attivo</b>\n\n"
        "📊 Multi-API (no Yahoo Finance!)\n\n"
        "/update - Forza aggiornamento\n"
        "/status - Stato bot\n\n"
        f"⏰ Update ogni {UPDATE_INTERVAL_HOURS}h",
        parse_mode='HTML'
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cache = load_cache()
    
    if is_cache_valid(cache):
        last = datetime.fromisoformat(cache['_last_update'])
        next_upd = last + timedelta(hours=UPDATE_INTERVAL_HOURS)
        delta = next_upd - datetime.now()
        
        h = int(delta.total_seconds() // 3600)
        m = int((delta.total_seconds() % 3600) // 60)
        
        msg = (
            f"✅ <b>Bot Attivo</b>\n\n"
            f"📅 Ultimo: {last.strftime('%d/%m %H:%M')}\n"
            f"⏰ Prossimo: {h}h {m}m\n"
            f"🔑 AV: {'✅' if ALPHA_VANTAGE_KEY else '❌'}"
        )
    else:
        msg = "⚠️ Cache non valida"
    
    await update.message.reply_text(msg, parse_mode='HTML')


async def cmd_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Aggiornamento...")
    
    try:
        data = update_all_markets()
        save_cache(data)
        msg = format_message(data)
        await update.message.reply_text(msg, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Update error: {e}")
        await update.message.reply_text(f"❌ Errore: {str(e)[:150]}")


# ===== SCHEDULED =====
async def scheduled_update(context: ContextTypes.DEFAULT_TYPE):
    logger.info("⏰ Scheduled update")
    
    try:
        cache = load_cache()
        if is_cache_valid(cache):
            logger.info("✅ Cache valid, skip")
            return
        
        data = update_all_markets()
        save_cache(data)
        
        msg = format_message(data)
        await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
        
        logger.info("✅ Update sent")
    except Exception as e:
        logger.error(f"❌ Error: {e}")


# ===== MAIN =====
def main():
    logger.info("\n" + "="*60)
    logger.info("🚀 HYBRID MARKET BOT - PRODUCTION")
    logger.info("="*60)
    logger.info("✅ NO Yahoo Finance")
    logger.info("✅ Multi-API: AlphaVantage + CoinGecko + ExchangeRate")
    logger.info("="*60 + "\n")
    
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("❌ Missing BOT_TOKEN or CHAT_ID!")
        return
    
    logger.info(f"✅ Token: {BOT_TOKEN[:10]}...")
    logger.info(f"✅ Chat: {CHAT_ID}")
    logger.info(f"✅ AV Key: {'Configured' if ALPHA_VANTAGE_KEY else 'MISSING'}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("update", cmd_update))
    
    app.job_queue.run_repeating(
        scheduled_update,
        interval=UPDATE_INTERVAL_HOURS * 3600,
        first=60
    )
    
    logger.info("✅ Ready\n" + "="*60 + "\n")
    
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == '__main__':
    main()
