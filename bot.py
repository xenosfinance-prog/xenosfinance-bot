import os
import asyncio
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL = "@xenosfinance"

bot = Bot(TOKEN)

async def send_message(text):
    await bot.send_message(chat_id=CHANNEL, text=text)

async def scheduler():
    while True:
        try:
            await send_message("Bot Xenosfinance attivo ✅ – test post automatico")
        except Exception as e:
            print("Errore invio:", e)
        await asyncio.sleep(600)

async def main():
    print("Bot avviato...")
    await send_message("Bot riavviato correttamente 🚀")
    asyncio.create_task(scheduler())
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
