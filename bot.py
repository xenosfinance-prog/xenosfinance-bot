import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Variabili d'ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL = "@xenosfinance"  # o ID numerico: -1001234567890

if not TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN non impostato!")

# --- FUNZIONI COMANDI --- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Xenos Finance Bot operativo!\nUsa /overview o /pdd per segnali PDD/TEMU."
    )

async def overview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📊 Market Overview Dicembre – TEMU momentum!\n\n"
    text += "PDD: forte rally natalizio 🚀\n"
    text += "AAPL, TSLA: trend positivo 📈\n"
    await update.message.reply_text(text)

async def pdd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🚀 Segnale PDD – TEMU shopping momentum!\nIngresso: 120\nTP: 130\nSL: 115"
    await update.message.reply_text(msg)

# --- FUNZIONE MESSAGGI AUTOMATICI --- #
async def send_periodic_messages(app: ApplicationBuilder):
    await app.bot.send_message(
        chat_id=CHANNEL,
        text="🎁 Xenos Finance: TEMU shopping rally is powering PDD this December 🚀"
    )
    while True:
        await asyncio.sleep(3600)  # ogni ora
        await app.bot.send_message(
            chat_id=CHANNEL,
            text="🎁 Reminder: TEMU shopping momentum continua – PDD rally! 🚀"
        )

# --- SETUP BOT --- #
app = ApplicationBuilder().token(TOKEN).build()

# Registrazione comandi
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("overview", overview))
app.add_handler(CommandHandler("pdd", pdd))

# Avvio messaggi automatici in background
async def main():
    asyncio.create_task(send_periodic_messages(app))
    await app.run_polling()

# Avvio
if __name__ == "__main__":
    asyncio.run(main())
