[![PyPi](https://img.shields.io/badge/PyPi-2.4.0-yellow)](https://pypi.org/project/tradingview-screener/)
[![Downloads](https://static.pepy.tech/badge/tradingview-screener)](https://pepy.tech/project/tradingview-screener)
[![Downloads](https://static.pepy.tech/badge/tradingview-screener/month)](https://pepy.tech/project/tradingview-screener)

```
pip install tradingview-screener
```

# About

This project has two parts:

1. **`tradingview_screener`** — A Python library to create stock screeners using the TradingView API (no web-scraping).
2. **Trading Bot** — An automated EMA crossover trading bot that scans for opportunities, executes paper/live trades, and sends alerts to Discord, SMS, and WhatsApp.

---

# Part 1: TradingView Screener Library

Query over 3000 fields (OHLC, indicators, fundamentals) across equities, crypto, forex, futures, and bonds. Filter and sort with SQL-like syntax.

## Quickstart

### Built-in scanners

```python
from tradingview_screener import Scanner

Scanner.names()
# ['premarket_gainers', 'premarket_losers', 'premarket_most_active',
#  'premarket_gappers', 'postmarket_gainers', 'postmarket_losers',
#  'postmarket_most_active']

n_rows, df = Scanner.premarket_gainers.get_scanner_data()
```

### Custom screeners

```python
from tradingview_screener import Query, Column

(Query()
 .select('name', 'close', 'volume', 'relative_volume_10d_calc')
 .where(
     Column('market_cap_basic').between(1_000_000, 50_000_000),
     Column('relative_volume_10d_calc') > 1.2,
     Column('MACD.macd') >= Column('MACD.signal')
 )
 .order_by('volume', ascending=False)
 .limit(25)
 .get_scanner_data())
```

For more examples see the [docs](https://shner-elmo.github.io/TradingView-Screener/tradingview_screener/query.html).

---

# Part 2: Trading Bot

An automated trading bot built on top of the screener library. It runs on a configurable interval, scans for EMA crossover signals, executes trades, and sends alerts.

## Architecture

```
src/bot/
  main.py          — Entry point, scheduling loop
  config.py        — All settings via environment variables
  watchlist.py     — Dynamic watchlist from Webull top gainers
  scanner.py       — TradingView-based scanner (regular hours)
  webull_scanner.py— Webull candle scanner (pre/post market, with live quotes)
  strategy.py      — EMA crossover + VWAP signal generation
  trader.py        — Trade execution (buy/sell/short/cover)
  broker.py        — PaperBroker (simulated) and TradeZeroBroker (live)
  alerter.py       — Discord, SMS (Twilio), WhatsApp (CallMeBot/Twilio)
  storage.py       — MongoDB signal storage and deduplication
```

## Strategy

The bot uses an **EMA crossover strategy** with VWAP confirmation on a 5-minute timeframe:

| Signal | Condition |
|---|---|
| **Buy** | EMA8 > EMA25 + price above VWAP + price above EMA200 |
| **Strong Buy** | Buy conditions + RSI between 40-70 |
| **Sell (EMA Cross)** | EMA8 < EMA25 (momentum lost) |
| **Sell (VWAP Break)** | Price below VWAP while EMA still bullish |
| **Strong Sell** | EMA bearish + below VWAP |

On buy signals, the bot covers any existing short and opens a long position. On sell signals, it closes any long and opens a short.

## Market Hours

- **Pre-market (4-9 AM ET)** and **Post-market (4-8 PM ET)**: Uses Webull candle data with live quotes (`get_quote()` for real-time extended hours prices).
- **Regular hours (9:30 AM - 4 PM ET)**: Uses TradingView screener API for real-time indicator data.

## Configuration

All settings are controlled via environment variables (or `.env.local`):

| Variable | Default | Description |
|---|---|---|
| `BOT_SCAN_INTERVAL_MINUTES` | `5` | Scan interval |
| `BOT_TIMEFRAME` | `5` | Candle timeframe (minutes) |
| `BOT_EMA_SHORT` | `8` | Short EMA period |
| `BOT_EMA_LONG` | `25` | Long EMA period |
| `BOT_EMA_TREND` | `200` | Trend EMA period |
| `BOT_MIN_VOLUME` | `100000` | Minimum volume filter for watchlist |
| `BOT_POSITION_SIZE` | `1000` | Dollar amount per trade |
| `BOT_STARTING_CAPITAL` | `10000` | Initial paper trading capital |
| `BOT_BROKER_MODE` | `paper` | `paper` or `tradezero` |
| `BOT_DISCORD_ALERTS` | `true` | Enable Discord alerts |
| `BOT_SMS_ALERTS` | `false` | Enable SMS via Twilio |
| `BOT_WHATSAPP_ALERTS` | `false` | Enable WhatsApp via CallMeBot |
| `DISCORD_ALERT_WEBHOOK_URL` | | Discord webhook URL |
| `CALLMEBOT_PHONE` | | Phone number for WhatsApp (CallMeBot) |
| `CALLMEBOT_APIKEY` | | CallMeBot API key |
| `MONGODB_CONNECTION_STRING` | `mongodb://localhost:27017` | MongoDB connection |

## Running the Bot

```bash
# Start MongoDB
mongod --config /usr/local/etc/mongod.conf --fork

# Run the bot
python3 -m bot.main
```

The bot will:
1. Fetch top gainers from Webull (filtered by volume)
2. Scan each ticker for EMA/VWAP/RSI signals
3. Execute paper trades (or live trades via TradeZero)
4. Send alerts to Discord/WhatsApp with signal details
5. Send periodic portfolio summaries with positions and P&L
6. Repeat every 5 minutes

## Alerts

The bot sends two types of alerts:

- **Trade signals**: `[BUY] NASDAQ:AAPL @ $185.50` with EMA, VWAP, and RSI values
- **Portfolio summaries**: Positions with entry time, unrealized P&L, closed trades with realized P&L, and total portfolio value
