import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==========================
# VALORI DIRETTI - RAILWAY PROBLEMA VARIABILI
# ==========================
BOT_TOKEN = "8522641168:AAGpRKL30HMcnGawGX1cdZ6ao1u5bZWpTA"
ALPHAVANTAGE_API_KEY = "M6FQOZ01M20T34ET"

print("=" * 60)
print("🤖 BOT AVVIATO SU RAILWAY")
print(f"Token: {BOT_TOKEN[:15]}...")
print("=" * 60)

# ==========================
# FUNZIONI BASE
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot attivo su Railway!")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - Avvia\n/help - Comandi")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        symbol = context.args[0].upper()
        await update.message.reply_text(f"{symbol}: $150.00 📈")
    else:
        await update.message.reply_text("Es: /price AAPL")

# ==========================
# AVVIO BOT
# ==========================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("price", price))

print("✅ Bot in esecuzione...")
app.run_polling()
