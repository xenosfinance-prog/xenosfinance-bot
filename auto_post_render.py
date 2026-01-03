import requests
import time
from datetime import datetime

# 🔹 Inserisci il token del tuo bot
TOKEN = "IL_TUO_BOT_TOKEN"

# 🔹 Inserisci l'ID del canale (con -100 se è privato)
CHANNEL_ID = "-1002375600499"

# 🔹 Messaggio base (puoi modificarlo o aggiungere variabili dinamiche)
BASE_MESSAGE = "🎯 Messaggio automatico dal bot Render! Ora: {}"

# 🔹 Intervallo tra i messaggi (in secondi, es. 3600 = 1 ora)
INTERVAL = 3600

# Funzione per inviare messaggio
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text}
    try:
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            print(f"{datetime.now()}: Messaggio inviato con successo!")
        else:
            print(f"{datetime.now()}: Errore: {r.text}")
    except Exception as e:
        print(f"{datetime.now()}: Errore durante invio messaggio: {e}")

# Loop principale
if __name__ == "__main__":
    while True:
        msg = BASE_MESSAGE.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        send_message(msg)
        time.sleep(INTERVAL)
