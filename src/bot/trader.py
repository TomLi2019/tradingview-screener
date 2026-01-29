import math
from typing import List

from bot.broker import Broker
from bot.config import POSITION_SIZE
from bot.strategy import Signal


def execute_signals(signals: List[Signal], broker: Broker):
    if not signals:
        return

    for signal in signals:
        ticker = signal.ticker
        price = signal.price

        if price <= 0:
            continue

        is_buy = signal.action in ('buy', 'strong_buy')
        is_sell = signal.action in ('sell_ema_cross', 'sell_vwap_break', 'strong_sell')

        qty = math.floor(POSITION_SIZE / price)
        if qty <= 0:
            continue

        if is_buy:
            # Cover short position first if we have one
            if broker.has_short_position(ticker):
                positions = broker.get_positions() if not hasattr(broker, 'short_positions') else {}
                short_pos = getattr(broker, 'short_positions', {}).get(ticker)
                if short_pos:
                    print(f"[trader] Signal: {signal.action.upper()} {ticker} @ ${price:.2f} -> covering {short_pos.qty} short shares")
                    broker.cover(ticker, short_pos.qty, price)

            # Open long if not already holding
            if not broker.has_position(ticker):
                print(f"[trader] Signal: {signal.action.upper()} {ticker} @ ${price:.2f} -> buying {qty} shares")
                broker.buy(ticker, qty, price)
            else:
                print(f"[trader] Already holding {ticker} long, skipping buy")

        elif is_sell:
            # Sell long position if holding
            if broker.has_position(ticker):
                positions = broker.get_positions()
                pos = positions.get(ticker)
                if pos:
                    reason = {
                        'sell_ema_cross': 'EMA8 crossed below EMA25',
                        'sell_vwap_break': 'Price dropped below VWAP',
                        'strong_sell': 'EMA bearish + below VWAP',
                    }.get(signal.action, signal.action)
                    print(f"[trader] EXIT LONG {ticker} @ ${price:.2f} ({reason}) -> selling {pos.qty} shares")
                    broker.sell(ticker, pos.qty, price)

            # Open short position
            if not broker.has_short_position(ticker):
                print(f"[trader] Signal: {signal.action.upper()} {ticker} @ ${price:.2f} -> shorting {qty} shares")
                broker.short(ticker, qty, price)
            else:
                print(f"[trader] Already short {ticker}, skipping")
