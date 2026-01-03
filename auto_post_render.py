import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# 🔹 CARICA VARIABILI DA .env (per sicurezza)
load_dotenv()

# 🔹 Inserisci il token del tuo bot (MEGLIO COME VARIABILE D'AMBIENTE)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "IL_TUO_BOT_TOKEN")

# 🔹 FIX CRITICO: L'ID del canale NON deve essere stringa se è numerico!
# Per canali privati: usa numero intero NEGATIVO
CHANNEL_ID = -1002375600499  # ⚠️ RIMUOVI LE VIRGOLETTE! Solo numero

# 🔹 Messaggio base
BASE_MESSAGE = "🎯 Messaggio automatico dal bot Render! Ora: {}"

# 🔹 Intervallo tra i messaggi (in secondi)
INTERVAL = 3600

# Funzione per inviare messaggio
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,  # Ora è un numero, non stringa
        "text": text,
        "parse_mode": "HTML"  # ⭐ Aggiunto per formattazione
    }
    try:
        r = requests.post(url, json=payload, timeout=10)  # ⭐ Usa json= invece di data=
        result = r.json()
        
        if result.get("ok"):
            print(f"{datetime.now()}: ✅ Messaggio inviato con successo!")
            print(f"Message ID: {result['result']['message_id']}")
        else:
            print(f"{datetime.now()}: ❌ Errore: {result.get('description')}")
            print(f"Codice errore: {result.get('error_code')}")
            
    except requests.exceptions.RequestException as e:
        print(f"{datetime.now()}: ⚠️ Errore di connessione: {e}")
    except Exception as e:
        print(f"{datetime.now()}: ⚠️ Errore generico: {e}")

# Funzione per testare il token
def test_token():
    """Test rapido per verificare se il token è valido"""
    test_url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    try:
        r = requests.get(test_url, timeout=5)
        data = r.json()
        if data.get("ok"):
            print(f"✅ Token VALIDO! Bot: @{data['result']['username']}")
            return True
        else:
            print(f"❌ Token NON VALIDO! Errore: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Errore test token: {e}")
        return False

# Loop principale
if __name__ == "__main__":
    print(f"🚀 Avvio bot...")
    print(f"Token (primi 10 char): {TOKEN[:10]}...")
    print(f"Channel ID: {CHANNEL_ID}")
    print(f"Intervallo: {INTERVAL} secondi ({INTERVAL/3600} ore)")
    
    # Test del token prima di iniziare
    if not test_token():
        print("❌ Token non valido! Fermo l'esecuzione.")
        exit(1)
    
    print("✅ Token verificato, avvio invio messaggi...")
    print("=" * 50)
    
    # Contatore messaggi
    message_count = 0
    
    while True:
        try:
            message_count += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            msg = BASE_MESSAGE.format(current_time)
            
            print(f"\n📨 Invio messaggio #{message_count} alle {current_time}")
            send_message(msg)
            
            print(f"⏳ Prossimo invio tra {INTERVAL} secondi...")
            time.sleep(INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Bot fermato manualmente dall'utente")
            print(f"Totale messaggi inviati: {message_count}")
            break
        except Exception as e:
            print(f"⚠️ Errore nel loop principale: {e}")
            print("Riprovo in 60 secondi...")
            time.sleep(60)
