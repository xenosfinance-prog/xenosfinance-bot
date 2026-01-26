import os

def main():
    print("=" * 60)
    print("🚀 BOT STARTING")
    print("=" * 60)

    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN non impostato")
        return  # <-- ESCE, NIENTE LOOP

    print(f"✅ Token trovato: {BOT_TOKEN[:15]}...")

    from telegram.ext import ApplicationBuilder, CommandHandler

    async def start(update, context):
        await update.message.reply_text("✅ Bot online!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("🤖 Bot in polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
