import os
from telegram.ext import ApplicationBuilder, CommandHandler

def main():
    print("=" * 60)
    print("🚀 BOT STARTING")
    print("=" * 60)
    
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    PORT = int(os.getenv("PORT", 8080))
    
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN non impostato")
        return
    
    print(f"✅ Token trovato: {BOT_TOKEN[:15]}...")
    
    async def start(update, context):
        await update.message.reply_text("✅ Bot online!")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print(f"🤖 Bot starting on port {PORT}...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
