import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==========================
# VARIABILI D'AMBIENTE DA RAILWAY
# ==========================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

# DEBUG - Verifica
print("=" * 60)
print("🤖 CONFIGURAZIONE BOT")
print("=" * 60)
print(f"Token trovato: {'✅' if BOT_TOKEN else '❌'}")
print(f"Token valore: {BOT_TOKEN[:15] if BOT_TOKEN else 'NONE'}...")
print(f"Alpha Vantage Key: {'✅' if ALPHAVANTAGE_API_KEY else '❌'}")
print("=" * 60)

# ==========================
# FUNZIONI DEL BOT (IL TUO CODICE)
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Bot attivo ✅")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Avvia il bot\n"
        "/help - Lista comandi\n"
        "/price SYMBOL - Prezzo live\n"
        "/sma SYMBOL - Media mobile (SMA14)\n"
        "/rsi SYMBOL - RSI14\n"
        "/dashboard SYMBOL1 SYMBOL2 ... - Multi-titolo"
    )

def get_quote(symbol):
    if not ALPHAVANTAGE_API_KEY:
        return None
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": ALPHAVANTAGE_API_KEY
    }
    r = requests.get(url, params=params).json()
    return r.get("Global Quote", {})

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /price SYMBOL")
        return
    symbol = context.args[0].upper()
    q = get_quote(symbol)
    if not q:
        await update.message.reply_text(f"Nessun dato per {symbol}")
        return
    price_val = q.get("05. price", "N/A")
    change = float(q.get("09. change", 0))
    pct = q.get("10. change percent", "N/A")
    emoji = "🟢" if change >= 0 else "🔴"
    await update.message.reply_text(f"{symbol}: ${price_val} ({emoji} {pct})")

# ==========================
# AVVIO BOT
# ==========================
if BOT_TOKEN:
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Aggiungi handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("price", price))
    
    print("🚀 Bot avviato e in polling...")
    app.run_polling()
else:
    print("❌ ERRORE: Token Telegram non trovato")
    print("💡 Verifica su Railway → Variables → TELEGRAM_BOT_TOKEN")
