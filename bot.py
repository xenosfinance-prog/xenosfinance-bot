import os
import sys

print("=" * 60)
print("🚀 BOT STARTING ON RAILWAY")
print("=" * 60)

# Leggi token da Railway
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if BOT_TOKEN:
    print(f"✅ Token trovato: {BOT_TOKEN[:15]}...")
    
    # Import DOPO aver verificato il token
    from telegram.ext import ApplicationBuilder, CommandHandler
    
    async def start(update, context):
        await update.message.reply_text("✅ Bot online!")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print("🤖 Bot in polling...")
    app.run_polling()
else:
    print("❌ Token non configurato")
    print("💡 Su Railway → Variables → TELEGRAM_BOT_TOKEN")
    print("💡 Valore: il tuo token da @BotFather")
    
    # Tieni il container attivo
    try:
        import time
        while True:
            time.sleep(60)
    except:
        pass
