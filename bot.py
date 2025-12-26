import os
import asyncio
from flask import Flask
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_TOKEN")  # Assicurati di aver impostato questa variabile su Render
CHANNEL = "@xenosfinance"

bot = Bot(TOKEN)

async def send_message(text):
    try:
        await bot.send_message(chat_id=CHANNEL, text=text)
    except Exception as e:
        print("Errore invio:", e)

async def scheduler():
    while True:
        await send_message("Bot Xenosfinance attivo ✅ – test post automatico")
        await asyncio.sleep(600)  # ogni 10 minuti

app = Flask(__name__)

@app.route("/")
def home():
    return "Xenos bot attivo!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    app.run(host="0.0.0.0", port=port)
