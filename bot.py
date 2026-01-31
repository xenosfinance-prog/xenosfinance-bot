import os
import asyncio
import requests
from datetime import datetime
import yfinance as yf
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ===== ENV =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
NEWS_KEY = os.getenv("NEWS_API_KEY")

# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Macro & Markets bot is running.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Auto market + geo updates enabled.\n"
        "No manual action required."
    )

# ===== GEO NEWS =====
GEO_QUERY = (
    "war OR attack OR sanctions OR military OR "
    "fed OR ecb OR rates OR inflation OR "
    "oil OR gas OR opec OR recession"
)

def get_geo_news():
    r = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "apiKey": NEWS_KEY,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 4,
            "q": GEO_QUERY
        },
        timeout=10
    ).json()
    return r.get("articles", [])

def macro_summary(news):
    titles = " ".join(n["title"].lower() for n in news)
    if any(k in titles for k in ["war", "attack", "missile"]):
        return "Geopolitical escalation increasing risk-off bias."
    if any(k in titles for k in ["fed", "ecb", "rates", "inflation"]):
        return "Central bank policy expectations driving markets."
    if any(k in titles for k in ["oil", "gas", "opec"]):
        return "Energy supply risks adding inflation pressure."
    return "Macro environment remains fragile."

# ===== JOB (AUTO TASK) =====
async def auto_update(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot

    try:
        btc = yf.Ticker("BTC-USD").info.get("regularMarketPrice", 0)
        eth = yf.Ticker("ETH-USD").info.get("regularMarketPrice", 0)
        gold = yf.Ticker("GC=F").info.get("regularMarketPrice", 0)

        market_msg = f"""📊 MARKET UPDATE

• BTC: ${btc:,.0f}
• ETH: ${eth:,.0f}
• Gold: ${gold:,.2f}
"""
        await bot.send_message(chat_id=CHANNEL_ID, text=market_msg)

        news = get_geo_news()
        if news:
            sp = yf.Ticker("^GSPC").info.get("regularMarketPrice", "N/A")
            oil = yf.Ticker("CL=F").info.get("regularMarketPrice", 0)

            geo_msg = f"""🌍 GEO & FUTURES INTELLIGENCE

• S&P 500: {sp}
• Oil WTI: ${oil:.2f}

📰 High-impact news:
"""
            for n in news:
                geo_msg += f"• {n['title']}\n"

            geo_msg += f"""
🧠 Macro Summary
• {macro_summary(news)}

🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""
            await bot.send_message(chat_id=CHANNEL_ID, text=geo_msg)

    except Exception as e:
        print("AUTO UPDATE ERROR:", e)

# ===== MAIN =====
async def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # ✅ JOB QUEUE — SAFE
    app.job_queue.run_repeating(
        auto_update,
        interval=7200,   # 2 hours
        first=10
    )

    print("🤖 Bot running with stable polling + job queue")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
