#!/usr/bin/env python3
"""
Professional Market Analysis Bot
Alpha Vantage + Telegram
Senza dipendenze schedule
"""

import os
import time
import requests
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== CONFIGURAZIONE =====
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8522641168:AAES...')
CHANNEL_ID = os.getenv('CHANNEL_ID', '-1002375600499')
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY', 'demo')

# Configura logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== ALPHA VANTAGE DATA FETCH =====

def get_alpha_vantage_quote(symbol):
    """Ottieni dati da Alpha Vantage"""
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "Global Quote" in data:
            quote = data["Global Quote"]
            price_str = quote.get('05. price', '0')
            change_str = quote.get('09. change', '0')
            
            return {
                'symbol': symbol,
                'price': float(price_str) if price_str.replace('.', '', 1).isdigit() else 0,
                'change': float(change_str) if change_str.replace('.', '', 1).lstrip('-').isdigit() else 0,
                'change_percent': quote.get('10. change percent', '0%'),
                'volume': quote.get('06. volume', '0')
            }
        else:
            logger.warning(f"Dati non disponibili per {symbol}")
            return None
            
    except Exception as e:
        logger.error(f"Errore fetching {symbol}: {e}")
        return None

def fetch_market_data():
    """Recupera tutti i dati di mercato"""
    logger.info("📊 Generando aggiornamento mercato...")
    
    # Lista asset da monitorare
    assets = [
        {"symbol": "SPY", "name": "S&P 500"},
        {"symbol": "QQQ", "name": "Nasdaq 100"},
        {"symbol": "DIA", "name": "Dow Jones"},
        {"symbol": "IWM", "name": "Russell 2000"},
        {"symbol": "GLD", "name": "Gold"},
        {"symbol": "SLV", "name": "Silver"},
        {"symbol": "TLT", "name": "Bonds 20+"},
        {"symbol": "VXX", "name": "VIX Short-Term"}
    ]
    
    results = []
    
    for asset in assets:
        logger.info(f"  📈 Recuperando {asset['symbol']} ({asset['name']})...")
        data = get_alpha_vantage_quote(asset['symbol'])
        
        if data:
            results.append({
                'name': asset['name'],
                'symbol': data['symbol'],
                'price': data['price'],
                'change': data['change'],
                'change_percent': data['change_percent']
            })
        
        # Rate limiting Alpha Vantage (5 chiamate/minuto free tier)
        time.sleep(12)
    
    return results

def generate_market_report():
    """Genera report di mercato"""
    market_data = fetch_market_data()
    
    if not market_data:
        return "⚠️ Impossibile recuperare dati di mercato. Riprova più tardi."
    
    # Analisi trend
    green = sum(1 for item in market_data if item['change'] > 0)
    red = sum(1 for item in market_data if item['change'] < 0)
    
    # Costruisci report
    report = "📊 **AGGIORNAMENTO MERCATO PROFESSIONALE**\n"
    report += f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    report += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Sezione indici
    report += "📈 **INDICI PRINCIPALI**\n"
    indices = [item for item in market_data if item['symbol'] in ['SPY', 'QQQ', 'DIA', 'IWM']]
    for item in indices:
        emoji = "🟢" if item['change'] > 0 else "🔴" if item['change'] < 0 else "⚪"
        report += f"{emoji} **{item['name']}** ({item['symbol']}): ${item['price']:.2f} "
        report += f"({item['change']:+.2f}, {item['change_percent']})\n"
    
    report += "\n🏆 **COMMODITIES**\n"
    commodities = [item for item in market_data if item['symbol'] in ['GLD', 'SLV']]
    for item in commodities:
        emoji = "🟢" if item['change'] > 0 else "🔴" if item['change'] < 0 else "⚪"
        report += f"{emoji} **{item['name']}**: ${item['price']:.2f} "
        report += f"({item['change']:+.2f}, {item['change_percent']})\n"
    
    report += "\n📊 **SINTESI MERCATO**\n"
    report += f"• Trend Positivi: {green} asset\n"
    report += f"• Trend Negativi: {red} asset\n"
    
    if green > red:
        report += "• Sentimento: ⬆️ **BULLISH**\n"
    elif red > green:
        report += "• Sentimento: ⬇️ **BEARISH**\n"
    else:
        report += "• Sentimento: ➡️ **NEUTRAL**\n"
    
    report += "\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
    report += "🔔 Aggiornamento ogni 4 ore (Lun-Ven)\n"
    report += "⏰ Orari mercato: 9:30-16:00 ET\n"
    
    return report

# ===== TELEGRAM BOT =====

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    await update.message.reply_text(
        "🤖 **Bot Analisi Mercato Professionale**\n\n"
        "Fornisco aggiornamenti sul mercato ogni 4 ore.\n"
        "Comandi disponibili:\n"
        "/market - Ultimo aggiornamento mercato\n"
        "/status - Stato del bot\n"
        "/help - Assistenza"
    )

async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /market"""
    await update.message.reply_text("🔄 Recupero dati mercato...")
    report = generate_market_report()
    await update.message.reply_text(report, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status"""
    status_msg = (
        "✅ **BOT STATUS**\n"
        f"• Online: Sì\n"
        f"• Ultimo aggiornamento: {datetime.now().strftime('%H:%M')}\n"
        f"• Prossimo aggiornamento: Ogni 4 ore\n"
        f"• Canale: @professional_market_bot\n"
        f"• Dati: Alpha Vantage API"
    )
    await update.message.reply_text(status_msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    help_msg = (
        "📚 **GUIDA BOT**\n\n"
        "Questo bot fornisce:\n"
        "• Aggiornamenti mercato ogni 4 ore\n"
        "• Analisi indici principali\n"
        "• Commodities (oro, argento)\n"
        "• Sentimento di mercato\n\n"
        "Comandi:\n"
        "/market - Aggiornamento corrente\n"
        "/status - Stato bot\n"
        "/help - Questo messaggio\n\n"
        "Supporto: contatta @tuocanale"
    )
    await update.message.reply_text(help_msg, parse_mode='Markdown')

async def scheduled_updates():
    """Gestisce aggiornamenti programmati"""
    logger.info("📅 Scheduler iniziato: ogni 4 ore (Lun-Ven)")
    
    while True:
        now = datetime.now()
        
        # Controlla se è giorno lavorativo (Lun-Ven)
        if now.weekday() < 5:  # 0=Lun, 4=Ven
            # Controlla se è ora di inviare (ogni 4 ore)
            current_hour = now.hour
            
            if current_hour % 4 == 0 and now.minute < 5:  # Invia all'ora precisa
                try:
                    logger.info("📊 Invio aggiornamento programmato...")
                    report = generate_market_report()
                    
                    app = Application.builder().token(TELEGRAM_TOKEN).build()
                    bot = app.bot
                    
                    await bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=report,
                        parse_mode='Markdown'
                    )
                    logger.info("✅ Aggiornamento inviato con successo!")
                    
                except Exception as e:
                    logger.error(f"❌ Errore invio aggiornamento: {e}")
        
        # Attendi 1 minuto prima di controllare di nuovo
        await asyncio.sleep(60)

async def main():
    """Funzione principale"""
    # Inizializza bot Telegram
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Aggiungi comandi
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("market", market_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # Avvia bot
    logger.info("======================================================================")
    logger.info("🚀 PROFESSIONAL MARKET ANALYSIS BOT STARTING")
    logger.info("======================================================================")
    logger.info(f"✅ Token: {TELEGRAM_TOKEN[:10]}...")
    logger.info(f"✅ Channel ID: {CHANNEL_ID}")
    logger.info("✅ All command handlers registered")
    logger.info("📅 Schedule: Every 4 hours, Mon-Fri only")
    logger.info("🕐 Market Hours: 9:30 AM - 4:00 PM ET")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("✅ BOT FULLY RUNNING - Polling + Scheduled Updates")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Crea task per polling e scheduler
    polling_task = asyncio.create_task(
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    )
    
    scheduler_task = asyncio.create_task(
        scheduled_updates()
    )
    
    # Esegui entrambi i task
    await asyncio.gather(polling_task, scheduler_task)

if __name__ == "__main__":
    # Verifica variabili d'ambiente
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "8522641168:AAES...":
        logger.error("❌ Token Telegram non configurato!")
        logger.info("👉 Imposta la variabile d'ambiente TELEGRAM_TOKEN su Railway")
        exit(1)
    
    if ALPHA_VANTAGE_KEY == "demo":
        logger.warning("⚠️  Usando Alpha Vantage DEMO key (limitata)")
        logger.info("👉 Ottieni una key gratuita: https://www.alphavantage.co/support/#api-key")
        logger.info("👉 Imposta ALPHA_VANTAGE_KEY su Railway")
    
    # Avvia bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot fermato dall'utente")
