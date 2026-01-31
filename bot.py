import os
import time
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Bot
import asyncio

# Configurazione
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

async def invia_news():
    """Invia news finanziarie al canale"""
    bot = Bot(token=BOT_TOKEN)
    
    # Esempio di messaggio di news (sostituisci con le tue news da AlphaVantage)
    messaggio = "📊 News Finanziarie\n\nMercati aggiornati!"
    
    await bot.send_message(chat_id=CHANNEL_ID, text=messaggio)
    print("✅ News inviate al canale!")

async def start(update, context):
    await update.message.reply_text("✅ Bot online!")

async def main():
    print("=" * 60)
    print("🚀 BOT STARTING")
    print("=" * 60)
    
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN mancante")
        return
    
    print(f"✅ Token OK: {BOT_TOKEN[:15]}...")
    
    # Crea applicazione
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print("🤖 Bot avviato!")
    
    # Invia prima news subito
    await invia_news()
    
    # Loop per inviare news ogni 1 ora
    while True:
        await asyncio.sleep(3600)  # 3600 secondi = 1 ora
        await invia_news()

if __name__ == "__main__":
    asyncio.run(main())
