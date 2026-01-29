import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import schedule

from bot.config import SCAN_INTERVAL_MINUTES, TIMEFRAME, BROKER_MODE, TRADEZERO_USERNAME, TRADEZERO_PASSWORD
from bot.scanner import scan_stocks
from bot.webull_scanner import scan_extended_hours
from bot.watchlist import fetch_gainers
from bot.strategy import ema_crossover
from bot.alerter import send_alert, send_portfolio_summary
from bot.storage import save_signal, was_recently_alerted
from bot.broker import PaperBroker, TradeZeroBroker
from bot.trader import execute_signals

from tradingview_screener.util import is_current_time_between

# Global broker instance
broker = None


def init_broker():
    global broker
    if BROKER_MODE == 'tradezero':
        print("[bot] Broker: TradeZero Canada (LIVE)")
        broker = TradeZeroBroker(TRADEZERO_USERNAME, TRADEZERO_PASSWORD)
    else:
        print("[bot] Broker: Paper Trading (simulated)")
        broker = PaperBroker()


def run_scan():
    WATCHLIST = fetch_gainers()
    if not WATCHLIST:
        print("[bot] No tickers in watchlist")
        return

    print(f"[bot] Scanning {len(WATCHLIST)} tickers: {WATCHLIST}")

    # Pick scanner based on market hours (ET)
    if is_current_time_between(4, 9):
        print("[bot] Pre-market scan (Webull candles)")
        df = scan_extended_hours(WATCHLIST, TIMEFRAME)
    elif is_current_time_between(16, 20):
        print("[bot] Post-market scan (Webull candles)")
        df = scan_extended_hours(WATCHLIST, TIMEFRAME)
    else:
        print("[bot] Regular scan")
        df = scan_stocks(WATCHLIST, TIMEFRAME)

    if df is None or df.empty:
        print("[bot] No data returned")
        return

    signals = ema_crossover(df, TIMEFRAME)
    print(f"[bot] Found {len(signals)} signal(s)")

    # Alert + deduplicate
    for signal in signals:
        if was_recently_alerted(signal.ticker, signal.action):
            print(f"[bot] Skipping (cooldown): {signal.ticker} {signal.action}")
            continue
        send_alert(signal)
        save_signal(signal)

    # Execute trades via broker
    execute_signals(signals, broker)

    # Print portfolio summary with current prices
    if hasattr(broker, 'print_summary'):
        prices = {}
        for signal in signals:
            prices[signal.ticker] = signal.price
        # Also include prices for existing positions from the scan data
        if df is not None and not df.empty:
            close_col = f'close|{TIMEFRAME}'
            for _, row in df.iterrows():
                ticker = row.get('ticker', '')
                price = row.get(close_col, row.get('close', 0))
                if ticker and price:
                    prices[ticker] = price
        broker.print_summary(prices)
        send_portfolio_summary(broker, prices)


def main():
    print(f"[bot] Starting EMA Crossover Bot")
    print(f"[bot] Mode: {BROKER_MODE}")
    print(f"[bot] Watchlist: dynamic (Webull top gainers, vol > 100K)")
    print(f"[bot] Interval: every {SCAN_INTERVAL_MINUTES} minutes")
    print(f"[bot] Timeframe: {TIMEFRAME}")

    init_broker()

    # Run once immediately
    run_scan()

    # Schedule recurring scans
    schedule.every(SCAN_INTERVAL_MINUTES).minutes.do(run_scan)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == '__main__':
    main()
