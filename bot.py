# Vecchi comandi (FX, commodities, macro, news, stocks, crypto)
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("help", help_command))
dp.add_handler(CommandHandler("forex_major", forex_major))
dp.add_handler(CommandHandler("forex_minor", forex_minor))
dp.add_handler(CommandHandler("forex_summary", forex_summary))
dp.add_handler(CommandHandler("gold", gold))
dp.add_handler(CommandHandler("silver", silver))
dp.add_handler(CommandHandler("commodities", commodities))
dp.add_handler(CommandHandler("oil_wti", oil_wti))
dp.add_handler(CommandHandler("oil_brent", oil_brent))
dp.add_handler(CommandHandler("ngas", ngas))
dp.add_handler(CommandHandler("eia_report", eia_report))
dp.add_handler(CommandHandler("macro_us", macro_us))
dp.add_handler(CommandHandler("macro_eu", macro_eu))
dp.add_handler(CommandHandler("macro_global", macro_global))
dp.add_handler(CommandHandler("market_news", market_news))
dp.add_handler(CommandHandler("us_stocks", us_stocks))
dp.add_handler(CommandHandler("eu_stocks", eu_stocks))
dp.add_handler(CommandHandler("pre_market", pre_market))
dp.add_handler(CommandHandler("earnings", earnings))
dp.add_handler(CommandHandler("crypto_major", crypto_major))
dp.add_handler(CommandHandler("crypto_summary", crypto_summary))

# Nuovi comandi Alpha Vantage
dp.add_handler(CommandHandler("price", price))   # Prezzo live di uno o più titoli
dp.add_handler(CommandHandler("sma", sma))       # Media mobile (SMA) di un titolo
dp.add_handler(CommandHandler("rsi", rsi))       # RSI di un titolo
dp.add_handler(CommandHandler("dashboard", dashboard)) # Multi-titolo + prezzi + indicatori
