# 📊 Professional Telegram Market Analysis Bot

Bot professionale per analisi di mercato con aggiornamenti automatici ogni **4 ore** dal **Lunedì al Venerdì**.

## ✨ Caratteristiche Principali

✅ **Aggiornamenti ogni 4 ore** (solo giorni feriali)
✅ **Tracking ore di mercato** (Pre-Market, Market Open, Post-Market)
✅ **Analisi completa**: Futures, Forex, Commodities, Crypto
✅ **News finanziarie real-time**
✅ **Sentiment analysis automatico**
✅ **Indicatori VIX e DXY**

## ⏰ Schedule Automatico

```
📅 Lunedì - Venerdì: Aggiornamenti ogni 4 ore
🏖️ Sabato - Domenica: Bot in pausa (weekend)

🕐 Orari Mercato US (ET):
   🌅 Pre-Market:  4:00 AM - 9:30 AM
   🔔 Market Open: 9:30 AM - 4:00 PM  
   🌆 Post-Market: 4:00 PM - 8:00 PM
   🌙 Closed:      8:00 PM - 4:00 AM
```

Ogni update include lo **status del mercato** e il **prossimo evento** (apertura/chiusura).

## 🚀 Deploy su Railway

### 1️⃣ Prepara il repository

```bash
# Clona o crea una cartella con questi file:
- professional_market_bot.py
- requirements.txt
- Procfile
- railway.json
- .gitignore
```

### 2️⃣ Carica su GitHub

```bash
# Inizializza git
git init
git add .
git commit -m "Initial commit - Professional Market Bot"

# Crea un repo su GitHub e carica
git remote add origin https://github.com/TUO_USERNAME/market-bot.git
git branch -M main
git push -u origin main
```

### 3️⃣ Deploy su Railway

1. Vai su [railway.app](https://railway.app)
2. Clicca **"New Project"**
3. Seleziona **"Deploy from GitHub repo"**
4. Scegli il tuo repository `market-bot`
5. Railway rileverà automaticamente Python e installerà le dipendenze

### 4️⃣ Configura le variabili d'ambiente

Nella dashboard Railway, vai su **Variables** e aggiungi:

```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHANNEL_ID=@tuo_canale_o_chat_id
NEWS_API_KEY=tua_chiave_newsapi_opzionale
```

**Come ottenere i token:**

#### 🤖 TELEGRAM_BOT_TOKEN:
1. Apri Telegram e cerca `@BotFather`
2. Invia `/newbot`
3. Scegli un nome e username per il bot
4. Copia il token che ti dà

#### 📢 TELEGRAM_CHANNEL_ID:
**Metodo 1 - Canale pubblico:**
```
@nome_del_tuo_canale
```

**Metodo 2 - Canale/Gruppo privato:**
1. Aggiungi il bot al canale/gruppo come amministratore
2. Usa questo bot per trovare l'ID: `@userinfobot`
3. Oppure usa questo codice:
```python
# Invia un messaggio nel canale e poi controlla i log del bot
# Vedrai il chat_id nei log
```

#### 📰 NEWS_API_KEY (Opzionale):
1. Vai su [newsapi.org](https://newsapi.org/register)
2. Registrati gratis
3. Copia la tua API key
4. *Se non la configuri, il bot userà news placeholder*

### 5️⃣ Deploy automatico

Railway farà automaticamente il deploy! Vedrai i log in tempo reale.

### 6️⃣ Verifica funzionamento

Controlla i log su Railway. Dovresti vedere:
```
🚀 PROFESSIONAL MARKET ANALYSIS BOT STARTING
✅ Token configured
✅ Channel ID
📊 Sending initial market update...
✅ Market update sent to channel!
```

## 📱 Comandi disponibili

Apri Telegram e scrivi al bot:

- `/start` - Avvia il bot
- `/help` - Lista comandi
- `/update` - Ottieni update immediato
- `/gold` - Prezzo oro
- `/crypto_major` - Cripto principali
- `/forex_major` - Forex majors
- `/market_news` - Ultime notizie

## 🔄 Aggiornamenti automatici

Il bot invia automaticamente analisi complete ogni **4 ore** al canale configurato, **solo dal Lunedì al Venerdì**.

Ogni update include:
- 📊 Status del mercato (Pre-Market, Open, Post-Market, Closed)
- ⏰ Prossimo evento di mercato e countdown
- 📈 Analisi completa di tutti gli asset
- 📰 Ultime notizie finanziarie

## ⚙️ Personalizzazione

Modifica `professional_market_bot.py` per:
- Cambiare frequenza aggiornamenti (linea con `asyncio.sleep(14400)` - attualmente 4 ore)
- Modificare orari di mercato (variabili `MARKET_OPEN`, `MARKET_CLOSE`, etc.)
- Aggiungere/rimuovere asset
- Personalizzare il formato dei messaggi
- Cambiare giorni operativi (attualmente Lun-Ven)

## 🐛 Troubleshooting

**Il bot non invia messaggi al canale:**
- Verifica che il bot sia amministratore del canale
- Controlla che il CHANNEL_ID sia corretto (con @ per canali pubblici)
- Per canali privati, usa l'ID numerico (es: `-1001234567890`)

**Errore "Token invalid":**
- Ricontrolla il token da @BotFather
- Assicurati non ci siano spazi extra

**Il bot si disconnette:**
- Railway potrebbe aver bisogno di un piano a pagamento per 24/7
- Verifica i log per errori specifici

## 💰 Costi Railway

- **Hobby Plan**: $5/mese - include $5 di crediti
- Il bot consuma molto poco, probabilmente rientra nei crediti gratuiti
- Railway ti avvisa prima di addebitare qualcosa

## 📊 Features

✅ **Schedule intelligente**: Updates ogni 4 ore, solo Lun-Ven
✅ **Market Hours Tracking**: Pre-Market, Market Open, Post-Market
✅ **Countdown prossimi eventi**: Apertura/Chiusura mercati
✅ Futures US (S&P, Nasdaq, Dow, Russell)
✅ Commodities (Gold, Silver, Oil, Gas, Copper)
✅ Forex Majors (EUR/USD, GBP/USD, etc.)
✅ Crypto (BTC, ETH, SOL)
✅ Indicatori VIX e DXY
✅ News finanziarie real-time
✅ Analisi macro economica
✅ Sentiment analysis automatico
✅ Variazioni giornaliere e settimanali
✅ Timezone-aware (Eastern Time)

## 🔐 Security

- Non committare mai i token nel codice
- Usa sempre variabili d'ambiente
- Il `.gitignore` protegge file sensibili

## 📝 License

Uso personale - Modifica liberamente!

---

**Fatto con ❤️ per traders professionisti**
