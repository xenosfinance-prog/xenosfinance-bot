import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==========================
# LEGGI DA VARIABILI D'AMBIENTE
# ==========================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ ERRORE: Token non configurato su Railway")
    print("💡 Vai su Railway → Variables → TELEGRAM_BOT_TOKEN")
    print("💡 Inserisci il NUOVO token rigenerato")
    exit(1)

print(f"✅ Token configurato: {BOT_TOKEN[:10]}...")

# ==========================
# FUNZIONI BASE
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot attivo!")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - Avvia\n/help - Aiuto")

# ==========================
# AVVIO
# ==========================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))

print("🚀 Bot avviato...")
app.run_polling()
