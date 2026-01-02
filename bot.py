import os
import asyncio
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL = "@xenosfinance"  # se hai il Chat ID numerico, meglio usarlo: -100xxxx

bot = Bot(TOKEN)

async def send_message(text):
    try:
        await bot.send_message(chat_id=CHANNEL, text=text)
        print("Messaggio inviato al canale ✅")
    except Exception as e:
        print("Errore invio:", e)

async def scheduler():
    print("🤖 Scheduler avviato...")
    while True:
        await send_message("🎁 Xenos Finance: TEMU shopping rally is powering PDD this December 🚀")
        await asyncio.sleep(600)  # 10 minuti

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("❌ TELEGRAM_TOKEN non impostato nelle variabili d'ambiente!")

    asyncio.run(scheduler())
