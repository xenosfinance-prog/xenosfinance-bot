import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==========================
# VARIABILI D'AMBIENTE DA RAILWAY
# ==========================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8522641168:AAGpRKL30HMcnGawGX1cdZ6ao1u5bZWpTA")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "M6FQOZ01M20T34ET")

# DEBUG - Verifica
print("=" * 60)
print("🤖 CONFIGURAZIONE BOT")
print("=" * 60)
print(f"Token configurato: {'✅' if BOT_TOKEN else '❌'}")
print(f"Alpha Vantage Key: {'✅' if ALPHAVANTAGE_API_KEY else '❌'}")
print("=" * 60)

# ==========================
# AVVIO BOT SOLO SE TOKEN ESISTE
# ==========================
if BOT_TOKEN and BOT_TOKEN != "8522641168:AAGpRKL30HMcnGawGX1cdZ6ao1u5bZWpTA":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # ... (tutto il resto del tuo codice con le funzioni) ...
    
    print("🚀 Bot avviato e in polling...")
    app.run_polling()
else:
    print("❌ ERRORE: Token Telegram non configurato correttamente")
    print("💡 Controlla le variabili su Railway → Variables")
