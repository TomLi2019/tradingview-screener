import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env.local from project root (two levels up from this file)
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / '.env.local')

# Scan settings
SCAN_INTERVAL_MINUTES = int(os.environ.get('BOT_SCAN_INTERVAL_MINUTES', '5'))
TIMEFRAME = os.environ.get('BOT_TIMEFRAME', '5')

# Watchlist — comma-separated tickers like "NASDAQ:AAPL,NASDAQ:TSLA"
WATCHLIST = [t.strip() for t in os.environ.get('BOT_WATCHLIST', '').split(',') if t.strip()]

# EMA periods
EMA_SHORT = int(os.environ.get('BOT_EMA_SHORT', '8'))
EMA_LONG = int(os.environ.get('BOT_EMA_LONG', '25'))
EMA_TREND = int(os.environ.get('BOT_EMA_TREND', '200'))

# Alert cooldown — don't re-alert the same ticker+action within this many minutes
ALERT_COOLDOWN_MINUTES = int(os.environ.get('BOT_ALERT_COOLDOWN_MINUTES', '30'))

# Volume filter for dynamic watchlist
MIN_VOLUME = int(os.environ.get('BOT_MIN_VOLUME', '100000'))

# Broker settings
BROKER_MODE = os.environ.get('BOT_BROKER_MODE', 'paper')  # paper / tradezero
STARTING_CAPITAL = float(os.environ.get('BOT_STARTING_CAPITAL', '10000'))
POSITION_SIZE = float(os.environ.get('BOT_POSITION_SIZE', '1000'))
TRADEZERO_USERNAME = os.environ.get('TRADEZERO_USERNAME', '')
TRADEZERO_PASSWORD = os.environ.get('TRADEZERO_PASSWORD', '')

# Notification toggles
DISCORD_ALERTS_ENABLED = os.environ.get('BOT_DISCORD_ALERTS', 'true').lower() == 'true'
SMS_ALERTS_ENABLED = os.environ.get('BOT_SMS_ALERTS', 'false').lower() == 'true'
WHATSAPP_ALERTS_ENABLED = os.environ.get('BOT_WHATSAPP_ALERTS', 'false').lower() == 'true'

# MongoDB
MONGODB_CONNECTION_STRING = os.environ.get('MONGODB_CONNECTION_STRING', 'mongodb://localhost:27017')
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'next-amazona')
SIGNALS_COLLECTION = 'bot_signals'
