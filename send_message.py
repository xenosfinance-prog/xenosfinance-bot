import requests

# 🔹 Inserisci qui il token del bot
TOKEN = "IL_TUO_BOT_TOKEN"

# 🔹 Inserisci l'ID del canale come stringa
CHANNEL_ID = "-1001234567890"

# Messaggio da inviare
TEXT = "✅ Messaggio di test inviato correttamente via HTTP!"

# Chiamata diretta alle API di Telegram
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {
    "chat_id": CHANNEL_ID,
    "text": TEXT
}

response = requests.post(url, data=payload)

if response.status_code == 200:
    print("Messaggio inviato con successo!")
else:
    print("Errore:", response.status_code, response.text)
