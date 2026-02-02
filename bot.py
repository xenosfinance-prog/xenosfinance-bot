  📥 Fetching futures & commodities via Alpha Vantage...
  
  # ETF proxy per futures (Alpha Vantage compatibile)
  futures_data = []
  
  # Mappatura simboli futures -> ETF
  futures_map = [
      {"symbol": "SPY", "name": "S&P 500 ETF", "type": "index"},
      {"symbol": "QQQ", "name": "Nasdaq 100 ETF", "type": "index"},
      {"symbol": "DIA", "name": "Dow Jones ETF", "type": "index"},
      {"symbol": "IWM", "name": "Russell 2000 ETF", "type": "index"}
  ]
  
  commodities_map = [
      {"symbol": "GLD", "name": "Gold ETF", "type": "commodity"},
      {"symbol": "SLV", "name": "Silver ETF", "type": "commodity"}
  ]
  
  # Funzione per fetch Alpha Vantage
  def get_alpha_vantage_quote(symbol):
      """Recupera dati da Alpha Vantage"""
      import requests
      import os
      import time
      
      # Prendi API key da variabile d'ambiente
      api_key = os.getenv('ALPHA_VANTAGE_KEY', 'demo')
      
      # URL per quote in tempo reale
      url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
      
      try:
          response = requests.get(url, timeout=10)
          data = response.json()
          
          # Parse risposta Alpha Vantage
          if "Global Quote" in data:
              quote = data["Global Quote"]
              return {
                  'symbol': symbol,
                  'price': quote.get('05. price', 'N/A'),
                  'change': quote.get('09. change', 'N/A'),
                  'change_percent': quote.get('10. change percent', 'N/A')
              }
          else:
              print(f"  ⚠️  {symbol}: Dati non disponibili")
              return {
                  'symbol': symbol,
                  'price': 'N/A',
                  'change': 'N/A',
                  'change_percent': 'N/A'
              }
              
      except Exception as e:
          print(f"  ❌ {symbol}: {str(e)[:50]}...")
          return {
              'symbol': symbol,
              'price': 'N/A',
              'change': 'N/A',
              'change_percent': 'N/A'
          }
      finally:
          # Rate limiting Alpha Vantage (5 chiamate/minuto free tier)
          time.sleep(12)  # 12 secondi tra le chiamate
  
  # Fetch futures (ETF proxy)
  for item in futures_map:
      print(f"  📈 Fetching {item['symbol']} ({item['name']})...")
      data = get_alpha_vantage_quote(item['symbol'])
      futures_data.append(data)
  
  # Fetch commodities (ETF proxy)
  commodities_data = []
  for item in commodities_map:
      print(f"  📈 Fetching {item['symbol']} ({item['name']})...")
      data = get_alpha_vantage_quote(item['symbol'])
      commodities_data.append(data)
  
  # Output risultati
  print("  ✅ Futures (ETF proxy):")
  for item in futures_data:
      print(f"    • {item['symbol']}: ${item['price']} ({item['change_percent']})")
  
  print("  ✅ Commodities (ETF proxy):")
  for item in commodities_data:
      print(f"    • {item['symbol']}: ${item['price']} ({item['change_percent']})")
