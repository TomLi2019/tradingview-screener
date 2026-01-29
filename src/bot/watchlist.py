import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from webull import webull

from bot.config import WATCHLIST, MIN_VOLUME
from tradingview_screener.query import Query, Column

# Map Webull exchange codes to TradingView format
EXCHANGE_MAP = {
    'NASDAQ': 'NASDAQ',
    'NAS': 'NASDAQ',
    'NYSE': 'NYSE',
    'AMEX': 'AMEX',
    'ASE': 'AMEX',
    'ARCA': 'AMEX',
    'BATS': 'AMEX',
}


def _fetch_webull_gainers(count=30):
    wb = webull()
    data = wb.active_gainer_loser(direction='gainer', rank_type='1d', count=count)
    items = data.get('data', [])

    tickers = []
    for item in items:
        t = item.get('ticker', {})
        symbol = t.get('symbol', '')
        exchange = t.get('disExchangeCode', t.get('exchangeCode', ''))
        if not symbol or not exchange:
            continue
        tv_exchange = EXCHANGE_MAP.get(exchange, exchange)
        tickers.append(f'{tv_exchange}:{symbol}')

    return tickers


def _filter_by_volume(tickers, min_volume, limit=10):
    if not tickers:
        return []
    q = (Query()
         .select('name', 'volume')
         .where(Column('volume') > min_volume)
         .set_tickers(*tickers))
    n_rows, df = q.get_scanner_data()
    if df is None or df.empty:
        return []
    return df['ticker'].tolist()[:limit]


def fetch_gainers(count=30, min_volume=None, limit=10):
    if min_volume is None:
        min_volume = MIN_VOLUME

    try:
        print(f"[watchlist] Fetching top gainers from Webull...")
        raw_tickers = _fetch_webull_gainers(count)
        print(f"[watchlist] Got {len(raw_tickers)} gainers from Webull")

        if not raw_tickers:
            print("[watchlist] No data from Webull, using fallback watchlist")
            return WATCHLIST

        filtered = _filter_by_volume(raw_tickers, min_volume, limit)
        print(f"[watchlist] {len(filtered)} tickers with volume > {min_volume:,}")

        if not filtered:
            print("[watchlist] No gainers met volume filter, using fallback watchlist")
            return WATCHLIST

        return filtered

    except Exception as e:
        print(f"[watchlist] Error fetching gainers: {e}, using fallback watchlist")
        return WATCHLIST
