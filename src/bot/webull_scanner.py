import pandas as pd
import numpy as np
from datetime import datetime, date
from webull import webull

from bot.config import EMA_SHORT, EMA_LONG, EMA_TREND


def _strip_exchange(ticker: str) -> str:
    """Convert 'NASDAQ:AAPL' to 'AAPL'."""
    return ticker.split(':')[-1] if ':' in ticker else ticker


def _calc_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _calc_vwap(df: pd.DataFrame) -> float:
    """Calculate VWAP from today's candles only."""
    today = date.today().isoformat()
    today_df = df[df.index.astype(str).str.startswith(today)]
    if today_df.empty:
        today_df = df.tail(78)  # fallback: ~1 trading day of 5-min bars

    typical_price = (today_df['high'] + today_df['low'] + today_df['close']) / 3
    cum_tp_vol = (typical_price * today_df['volume']).cumsum()
    cum_vol = today_df['volume'].cumsum()
    vwap = cum_tp_vol / cum_vol.replace(0, np.nan)
    return vwap.iloc[-1] if not vwap.empty else None


def _calc_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else None


def scan_extended_hours(tickers, timeframe='5'):
    """Fetch candle data from Webull and calculate EMA/VWAP/RSI for extended hours."""
    if not tickers:
        return None

    wb = webull()
    rows = []

    for ticker in tickers:
        symbol = _strip_exchange(ticker)
        try:
            bars = wb.get_bars(stock=symbol, interval='m5', count=250)
            if bars is None or (isinstance(bars, pd.DataFrame) and bars.empty):
                print(f"[webull_scanner] No candle data for {symbol}")
                continue

            if isinstance(bars, list):
                bars = pd.DataFrame(bars)

            if 'close' not in bars.columns:
                print(f"[webull_scanner] Missing 'close' column for {symbol}")
                continue

            close = bars['close'].astype(float)
            ema_s = _calc_ema(close, EMA_SHORT)
            ema_l = _calc_ema(close, EMA_LONG)
            ema_t = _calc_ema(close, EMA_TREND)
            vwap = _calc_vwap(bars)
            rsi = _calc_rsi(close)

            # Use live quote for current price (includes extended hours)
            latest_close = close.iloc[-1]
            try:
                quote = wb.get_quote(stock=symbol)
                if quote and isinstance(quote, dict):
                    # Try post/pre market price first, then last trade price
                    live_price = (
                        quote.get('pPrice') or      # post-market price
                        quote.get('mktrfPrice') or   # pre-market price
                        quote.get('close') or
                        quote.get('tradePrice')
                    )
                    if live_price:
                        latest_close = float(live_price)
                        print(f"[webull_scanner] {symbol}: live quote=${latest_close:.2f}")
            except Exception as qe:
                print(f"[webull_scanner] Quote fallback for {symbol}: {qe}")

            tf = timeframe

            row = {
                'ticker': ticker,
                'name': symbol,
                'close': latest_close,
                f'close|{tf}': latest_close,
                f'EMA{EMA_SHORT}|{tf}': ema_s.iloc[-1],
                f'EMA{EMA_LONG}|{tf}': ema_l.iloc[-1],
                f'EMA{EMA_TREND}|{tf}': ema_t.iloc[-1],
                f'VWAP|{tf}': vwap,
                f'RSI|{tf}': rsi,
                'volume': int(bars['volume'].astype(float).sum()) if 'volume' in bars.columns else 0,
                f'volume|{tf}': int(bars['volume'].astype(float).iloc[-1]) if 'volume' in bars.columns else 0,
            }
            rows.append(row)
            vwap_str = f"${vwap:.2f}" if vwap else "N/A"
            print(f"[webull_scanner] {ticker}: close=${latest_close:.2f}, EMA{EMA_SHORT}={ema_s.iloc[-1]:.2f}, EMA{EMA_LONG}={ema_l.iloc[-1]:.2f}, VWAP={vwap_str}")

        except Exception as e:
            print(f"[webull_scanner] Error fetching {symbol}: {e}")
            continue

    if not rows:
        return None

    return pd.DataFrame(rows)
