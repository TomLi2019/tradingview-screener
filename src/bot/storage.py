from dataclasses import asdict
from datetime import datetime, timedelta

from bot.config import MONGODB_CONNECTION_STRING, MONGODB_DATABASE, SIGNALS_COLLECTION, ALERT_COOLDOWN_MINUTES
from bot.strategy import Signal

# In-memory cooldown cache as fallback when MongoDB is unavailable
_recent_alerts = {}


def _get_collection():
    import pymongo
    client = pymongo.MongoClient(MONGODB_CONNECTION_STRING, serverSelectionTimeoutMS=3000)
    db = client[MONGODB_DATABASE]
    # Force a connection check
    client.admin.command('ping')
    return client, db[SIGNALS_COLLECTION]


def save_signal(signal: Signal):
    try:
        client, collection = _get_collection()
        doc = asdict(signal)
        collection.insert_one(doc)
        client.close()
    except Exception as e:
        print(f"[storage] MongoDB unavailable, signal not persisted: {e}")


def was_recently_alerted(ticker: str, action: str) -> bool:
    try:
        client, collection = _get_collection()
        cutoff = (datetime.now() - timedelta(minutes=ALERT_COOLDOWN_MINUTES)).strftime('%Y-%m-%dT%H:%M:%S')
        count = collection.count_documents({
            'ticker': ticker,
            'action': action,
            'timestamp': {'$gte': cutoff},
        })
        client.close()
        return count > 0
    except Exception:
        # Fallback to in-memory cooldown
        key = f"{ticker}:{action}"
        last = _recent_alerts.get(key)
        if last and (datetime.now() - last).total_seconds() < ALERT_COOLDOWN_MINUTES * 60:
            return True
        _recent_alerts[key] = datetime.now()
        return False
