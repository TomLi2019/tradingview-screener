from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import pandas as pd

from bot.config import EMA_SHORT, EMA_LONG, EMA_TREND, TIMEFRAME


@dataclass
class Signal:
    ticker: str
    action: str          # 'buy', 'strong_buy', 'sell_ema_cross', 'sell_vwap_break', 'strong_sell'
    price: float
    ema_short: float
    ema_long: float
    ema_trend: float
    vwap: Optional[float] = None
    rsi: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))


def ema_crossover(df: pd.DataFrame, timeframe: str = None) -> List[Signal]:
    if df is None or df.empty:
        return []

    tf = timeframe or TIMEFRAME
    ema_short_col = f'EMA{EMA_SHORT}|{tf}'
    ema_long_col = f'EMA{EMA_LONG}|{tf}'
    ema_trend_col = f'EMA{EMA_TREND}|{tf}'
    vwap_col = f'VWAP|{tf}'
    rsi_col = f'RSI|{tf}'
    close_col = f'close|{tf}'

    signals = []
    for _, row in df.iterrows():
        ticker = row.get('ticker', row.get('name', 'UNKNOWN'))
        price = row.get(close_col, row.get('close', 0))
        ema_s = row.get(ema_short_col, None)
        ema_l = row.get(ema_long_col, None)
        ema_t = row.get(ema_trend_col, None)
        vwap = row.get(vwap_col, None)
        rsi = row.get(rsi_col, None)

        if ema_s is None or ema_l is None or ema_t is None or vwap is None:
            continue

        action = None

        ema_bullish = ema_s > ema_l
        above_vwap = price > vwap
        above_trend = price > ema_t

        # === BUY: EMA bullish + above VWAP + above trend ===
        if ema_bullish and above_vwap and above_trend:
            action = 'buy'
            if rsi and 40 < rsi < 70:
                action = 'strong_buy'

        # === SELL SIGNALS (any one triggers exit) ===

        # Strong sell: EMA bearish AND below VWAP (both confirm)
        elif not ema_bullish and not above_vwap:
            action = 'strong_sell'

        # EMA cross exit: EMA8 crossed below EMA25 (momentum lost)
        elif not ema_bullish and above_vwap:
            action = 'sell_ema_cross'

        # VWAP exit: price dropped below VWAP while EMA still bullish (early warning)
        elif ema_bullish and not above_vwap:
            action = 'sell_vwap_break'

        if action:
            signals.append(Signal(
                ticker=ticker,
                action=action,
                price=price,
                ema_short=ema_s,
                ema_long=ema_l,
                ema_trend=ema_t,
                vwap=vwap,
                rsi=rsi,
            ))

    return signals
