import os
import requests
from datetime import datetime
import time
import sys

# =============================================
# CONFIGURAZIONE - LEGGE DA VARIABILI D'AMBIENTE
# =============================================

# 🔹 LEGGI IL TOKEN DA RENDER.COM
# Su Render: Environment → Add Variable → TELEGRAM_BOT_TOKEN = "tuo_token"
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# 🔹 ID del canale Telegram (usa il tuo)
# Per canali privati: -100xxxxxxxxxx
# Per canali pubblici: @nomedelcanale
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "-1002375600499")

# 🔹 Intervallo tra i messaggi (in secondi)
INTERVAL = int(os.environ.get("INTERVAL_SECONDS", "3600"))

# 🔹 Messaggio base con placeholder per l'orario
BASE_MESSAGE = os.environ.get("MESSAGE_TEXT", "🎯 Messaggio automatico! Data/ora: {}")

# =============================================
# FUNZIONI DI UTILITY
# =============================================

def check_environment():
    """Verifica che tutte le variabili necessarie siano configurate"""
    print("🔍 Verifica configurazione...")
    
    # Controllo critico: il token DEVE esistere
    if not TOKEN:
        print("❌ ERRORE: TELEGRAM_BOT_TOKEN non configurato!")
        print("\n💡 SOLUZIONE:")
        print("1. Vai su Render.com → il tuo servizio")
        print("2. Clicca 'Environment'")
        print("3. Aggiungi variabile:")
        print("   Key: TELEGRAM_BOT_TOKEN")
        print("   Value: Il tuo token da @BotFather")
        print("4. Riavvia il servizio")
        return False
    
    print(f"✅ Token: {TOKEN[:10]}...")
    print(f"✅ Canale: {CHANNEL_ID}")
    print(f"✅ Intervallo: {INTERVAL}s ({INTERVAL/3600:.1f} ore)")
    return True

def test_telegram_connection():
    """Testa la connessione all'API di Telegram"""
    print("🌐 Test connessione a Telegram API...")
    
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            bot_name = data["result"]["username"]
            print(f"✅ Connesso! Bot: @{bot_name}")
            return True
        else:
            error_msg = data.get("description", "Errore sconosciuto")
            print(f"❌ API Error: {error_msg}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Errore di rete. Verifica la connessione internet.")
        return False
    except Exception as e:
        print(f"❌ Errore inaspettato: {e}")
        return False

def send_telegram_message(text):
    """Invia un messaggio al canale Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",  # Permette formattazione HTML base
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        data = response.json()
        
        if data.get("ok"):
            return {"success": True, "message_id": data["result"]["message_id"]}
        else:
            error_code = data.get("error_code", "N/A")
            error_desc = data.get("description", "Errore sconosciuto")
            return {"success": False, "error": f"{error_code}: {error_desc}"}
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout - connessione troppo lenta"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Errore di connessione"}
    except Exception as e:
        return {"success": False, "error": f"Errore generico: {str(e)}"}

# =============================================
# FUNZIONE PRINCIPALE
# =============================================

def main():
    """Funzione principale del bot"""
    print("=" * 60)
    print("🤖 BOT TELEGRAM PER RENDER.COM")
    print("=" * 60)
    
    # Verifica configurazione
    if not check_environment():
        sys.exit(1)
    
    # Test connessione
    if not test_telegram_connection():
        print("\n💡 Suggerimenti:")
        print("• Controlla che il token sia corretto su @BotFather")
        print("• Assicurati che il bot sia ancora attivo")
        print("• Verifica eventuali blocchi di rete")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ TUTTO OK! Bot pronto all'uso")
    print("=" * 60 + "\n")
    
    message_count = 0
    last_success = datetime.now()
    
    try:
        while True:
            message_count += 1
            current_time = datetime.now()
            
            # Formatta il messaggio
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            message = BASE_MESSAGE.format(formatted_time)
            
            # Log
            print(f"\n📨 INVIO #{message_count}")
            print(f"   ⏰ Ora: {formatted_time}")
            print(f"   📝 Testo: {message[:50]}...")
            
            # Invia il messaggio
            result = send_telegram_message(message)
            
            if result["success"]:
                print(f"   ✅ SUCCESSO! ID: {result['message_id']}")
                last_success = current_time
            else:
                print(f"   ❌ FALLITO: {result['error']}")
                print(f"   🕐 Ultimo successo: {last_success.strftime('%H:%M:%S')}")
            
            # Calcola prossimo invio
            next_time = current_time.timestamp() + INTERVAL
            next_datetime = datetime.fromtimestamp(next_time)
            
            print(f"\n   ⏳ Prossimo invio: {next_datetime.strftime('%H:%M:%S')}")
            print(f"   Attesa di {INTERVAL} secondi...")
            
            # Attesa
            time.sleep(INTERVAL)
            
    except KeyboardInterrupt:
        print(f"\n\n{'='*60}")
        print(f"🛑 BOT FERMATO MANUALMENTE")
        print(f"📊 Statistiche:")
        print(f"   • Messaggi tentati: {message_count}")
        print(f"   • Ultimo successo: {last_success.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n⚠️ ERRORE CRITICO: {e}")
        print("💡 Controlla i log su Render.com per dettagli")

# =============================================
# AVVIO
# =============================================

if __name__ == "__main__":
    main()
