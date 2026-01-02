from telegram import Bot

# 🔹 Inserisci qui il token del tuo bot
TOKEN = "IL_TUO_BOT_TOKEN"

# 🔹 Inserisci l'ID del tuo canale (con -100 davanti se è privato)
CHANNEL_ID = -1001234567890

# Crea l'oggetto bot
bot = Bot(token=TOKEN)

# Invia il messaggio al canale
bot.send_message(chat_id=CHANNEL_ID, text="✅ Messaggio di test inviato correttamente!")

print("Messaggio inviato con successo!")
