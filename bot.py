import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==========================
# VARIABILI D’AMBIENTE
# ==========================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

# Verifica token
if not BOT_TOKEN:
    raise ValueError("Errore: TELEGRAM_BOT_TOKEN non impostato!")
if not ALPHAVANTAGE_API_KEY:
    raise ValueError("Errore: ALPHAVANTAGE_API_KEY non impostato!")

# ==========================
# FUNZIONI BASE
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

# ==========================
# FUNZIONI ALPHA VANTAGE
# ==========================
def get_quote(symbol):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol.upper(),
        "apikey": ALPHAVANTAGE_API_KEY
    }
    r = requests.get(url, params=params).json()
    return r.get("Global Quote", {})

def get_sma(symbol):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "SMA",
        "symbol": symbol.upper(),
        "interval": "daily",
        "time_period": 14,
        "series_type": "close",
        "apikey": ALPHAVANTAGE_API_KEY
    }
    r = requests.get(url, params=params).json()
    return r.get("Technical Analysis: SMA", {})

def get_rsi(symbol):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "RSI",
        "symbol": symbol.upper(),
        "interval": "daily",
        "time_period": 14,
        "series_type": "close",
        "apikey": ALPHAVANTAGE_API_KEY
    }
    r = requests.get(url, params=params).json()
    return r.get("Technical Analysis: RSI", {})

# ==========================
# HANDLER NUOVI COMANDI
# ==========================
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /price SYMBOL")
        return
    messages = []
    for symbol in context.args:
        q = get_quote(symbol)
        if not q:
            messages.append(f"{symbol.upper()}: dati non disponibili")
            continue
        price = q.get("05. price", "N/A")
        change = float(q.get("09. change", 0))
        pct = q.get("10. change percent", "N/A")
        emoji = "🟢" if change >= 0 else "🔴"
        messages.append(f"{symbol.upper()} {emoji} - ${price} ({pct})")
    await update.message.reply_text("\n".join(messages))

async def sma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /sma SYMBOL")
        return
    symbol = context.args[0]
    sma_data = get_sma(symbol)
    if not sma_data:
        await update.message.reply_text(f"SMA per {symbol.upper()} non disponibile")
        return
    latest_date = list(sma_data.keys())[0]
    sma_value = sma_data[latest_date]["SMA"]
    await update.message.reply_text(f"SMA14 {symbol.upper()}: {sma_value} (ultimo giorno: {latest_date})")

async def rsi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /rsi SYMBOL")
        return
    symbol = context.args[0]
    rsi_data = get_rsi(symbol)
    if not rsi_data:
        await update.message.reply_text(f"RSI per {symbol.upper()} non disponibile")
        return
    latest_date = list(rsi_data.keys())[0]
    rsi_value = rsi_data[latest_date]["RSI"]
    await update.message.reply_text(f"RSI14 {symbol.upper()}: {rsi_value} (ultimo giorno: {latest_date})")

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /dashboard SYMBOL1 SYMBOL2 ...")
        return
    messages = []
    for symbol in context.args:
        q = get_quote(symbol)
        if not q:
            messages.append(f"{symbol.upper()}: dati non disponibili")
            continue
        price = q.get("05. price", "N/A")
        change = float(q.get("09. change", 0))
        pct = q.get("10. change percent", "N/A")
        emoji = "🟢" if change >= 0 else "🔴"
        sma_data = get_sma(symbol)
        latest_sma = list(sma_data.keys())[0] if sma_data else "N/A"
        sma_value = sma_data[latest_sma]["SMA"] if sma_data else "N/A"
        rsi_data = get_rsi(symbol)
        latest_rsi = list(rsi_data.keys())[0] if rsi_data else "N/A"
        rsi_value = rsi_data[latest_rsi]["RSI"] if rsi_data else "N/A"
        messages.append(
            f"{symbol.upper()} {emoji} - ${price} ({pct})\nSMA14: {sma_value}, RSI14: {rsi_value}"
        )
    await update.message.reply_text("\n\n".join(messages))

# ==========================
# APPLICATION BUILDER 20.x
# ==========================
app = ApplicationBuilder().token(BOT_TOKEN).build()

# ==========================
# AGGIUNGI TUTTI I COMANDI
# ==========================
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("price", price))
app.add_handler(CommandHandler("sma", sma))
app.add_handler(CommandHandler("rsi", rsi))
app.add_handler(CommandHandler("dashboard", dashboard))

# ==========================
# AVVIO BOT
# ==========================
app.run_polling()
