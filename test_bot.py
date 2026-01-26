from telegram import Bot

TOKEN = "IL_TUO_TOKEN"  # metti il token reale
CHANNEL_ID = "-1001234567890"  # metti l'ID reale del canale

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHANNEL_ID, text="✅ Bot funziona, messaggio inviato!")
print("Messaggio inviato correttamente")
