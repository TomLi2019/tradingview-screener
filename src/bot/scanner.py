import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tradingview_screener.query import Query
from bot.config import EMA_SHORT, EMA_LONG, EMA_TREND


def _ema_col(period, tf):
    return f'EMA{period}|{tf}'


def _build_columns(tf):
    return [
        'name', 'close', f'close|{tf}',
        f'EMA{EMA_SHORT}|{tf}', f'EMA{EMA_LONG}|{tf}', f'EMA{EMA_TREND}|{tf}',
        f'EMA{EMA_SHORT}', f'EMA{EMA_LONG}', f'EMA{EMA_TREND}',
        f'VWAP|{tf}', f'RSI|{tf}', 'volume', f'volume|{tf}',
        'high', 'low', 'market_cap_basic',
        'premarket_change', 'premarket_volume',
        'postmarket_change', 'postmarket_volume',
    ]


def scan_stocks(tickers, timeframe='5'):
    if not tickers:
        return None
    q = Query().select(*_build_columns(timeframe)).set_tickers(*tickers)
    n_rows, df = q.get_scanner_data()
    return df


def scan_premarket(tickers, timeframe='5'):
    if not tickers:
        return None
    columns = _build_columns(timeframe) + [
        'premarket_high', 'premarket_low',
        'premarket_change_abs', 'pre_change|5',
    ]
    q = Query().select(*columns).set_tickers(*tickers)
    n_rows, df = q.get_scanner_data()
    return df


def scan_postmarket(tickers, timeframe='5'):
    if not tickers:
        return None
    columns = _build_columns(timeframe) + [
        'postmarket_high', 'postmarket_low',
        'postmarket_change_abs',
    ]
    q = Query().select(*columns).set_tickers(*tickers)
    n_rows, df = q.get_scanner_data()
    return df
