import os
import sys

# ==========================
# DEBUG: Verifica se Railway passa le variabili
# ==========================
print("=== RAILWAY DEBUG ===")
print(f"Tutte le variabili: {list(os.environ.keys())}")

# Prova diversi nomi di variabile che Railway potrebbe usare
BOT_TOKEN = (
    os.getenv("TELEGRAM_BOT_TOKEN") or
    os.getenv("BOT_TOKEN") or
    os.getenv("TOKEN") or
    ""  # Fallback vuoto
)

print(f"Token trovato: {'SI' if BOT_TOKEN else 'NO'}")
print("=====================")

# ==========================
# SE RAILWAY NON PASSA LE VARIABILI, USA QUESTO WORKAROUND
# ==========================
if not BOT_TOKEN:
    print("⚠️ Railway non passa le variabili d'ambiente")
    print("📦 Usando workaround alternativo...")
    
    # Workaround: leggi da file .env se esiste
    try:
        with open('.env', 'r') as f:
            for line in f:
                if 'TELEGRAM_BOT_TOKEN=' in line:
                    BOT_TOKEN = line.split('=')[1].strip()
                    break
    except:
        pass

# ==========================
# SE ANCORA NESSUN TOKEN, SPEGNI IL BOT MA SENZA ERRORI
# ==========================
if not BOT_TOKEN:
    print("💡 INFO: Nessun token configurato")
    print("💡 Il bot rimane attivo ma non risponde a comandi Telegram")
    print("💡 Configura su Railway: Variables → TELEGRAM_BOT_TOKEN")
    
    # Mantieni il container attivo ma senza bot Telegram
    try:
        while True:
            import time
            time.sleep(3600)  # Tieni attivo il container
    except KeyboardInterrupt:
        sys.exit(0)

# ==========================
# SE C'È IL TOKEN, AVVIA IL BOT
# ==========================
print(f"✅ Token: {BOT_TOKEN[:15]}...")

# Import DOPO aver verificato il token
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot attivo su Railway!")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - Avvia\n/help - Aiuto")

# Avvia bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))

print("🚀 Bot Telegram avviato!")
app.run_polling()
