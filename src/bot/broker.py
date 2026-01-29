from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from bot.config import STARTING_CAPITAL


@dataclass
class Position:
    ticker: str
    qty: int
    avg_price: float
    entry_time: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

    def unrealized_pnl(self, current_price: float) -> float:
        return (current_price - self.avg_price) * self.qty

    def market_value(self, current_price: float) -> float:
        return current_price * self.qty


class Broker(ABC):
    @abstractmethod
    def buy(self, ticker: str, qty: int, price: float) -> bool:
        pass

    @abstractmethod
    def sell(self, ticker: str, qty: int, price: float) -> bool:
        pass

    @abstractmethod
    def get_positions(self) -> Dict[str, Position]:
        pass

    @abstractmethod
    def get_cash(self) -> float:
        pass

    @abstractmethod
    def get_portfolio_value(self, prices: Dict[str, float]) -> float:
        pass

    @abstractmethod
    def has_position(self, ticker: str) -> bool:
        pass

    @abstractmethod
    def short(self, ticker: str, qty: int, price: float) -> bool:
        pass

    @abstractmethod
    def cover(self, ticker: str, qty: int, price: float) -> bool:
        pass

    @abstractmethod
    def has_short_position(self, ticker: str) -> bool:
        pass


class PaperBroker(Broker):
    def __init__(self, starting_capital: float = None):
        self.cash = starting_capital or STARTING_CAPITAL
        self.positions: Dict[str, Position] = {}
        self.short_positions: Dict[str, Position] = {}
        self.trade_log: List[dict] = []
        print(f"[paper] Paper broker initialized with ${self.cash:,.2f}")

    def buy(self, ticker: str, qty: int, price: float) -> bool:
        cost = qty * price
        if cost > self.cash:
            print(f"[paper] Insufficient cash for {ticker}: need ${cost:,.2f}, have ${self.cash:,.2f}")
            return False

        self.cash -= cost

        if ticker in self.positions:
            pos = self.positions[ticker]
            total_qty = pos.qty + qty
            pos.avg_price = ((pos.avg_price * pos.qty) + (price * qty)) / total_qty
            pos.qty = total_qty
        else:
            self.positions[ticker] = Position(ticker=ticker, qty=qty, avg_price=price)

        trade = {
            'action': 'BUY',
            'ticker': ticker,
            'qty': qty,
            'price': price,
            'cost': cost,
            'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        }
        self.trade_log.append(trade)
        print(f"[paper] BUY {qty} {ticker} @ ${price:.2f} (cost: ${cost:,.2f}, cash: ${self.cash:,.2f})")
        return True

    def sell(self, ticker: str, qty: int, price: float) -> bool:
        if ticker not in self.positions:
            print(f"[paper] No position to sell for {ticker}")
            return False

        pos = self.positions[ticker]
        sell_qty = min(qty, pos.qty)
        entry_price = pos.avg_price
        proceeds = sell_qty * price
        pnl = (price - entry_price) * sell_qty

        self.cash += proceeds
        pos.qty -= sell_qty

        if pos.qty == 0:
            del self.positions[ticker]

        trade = {
            'action': 'SELL',
            'ticker': ticker,
            'qty': sell_qty,
            'entry_price': entry_price,
            'price': price,
            'proceeds': proceeds,
            'pnl': pnl,
            'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        }
        self.trade_log.append(trade)
        pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
        print(f"[paper] SELL {sell_qty} {ticker} @ ${price:.2f} (P&L: {pnl_str}, cash: ${self.cash:,.2f})")
        return True

    def get_positions(self) -> Dict[str, Position]:
        return self.positions

    def get_cash(self) -> float:
        return self.cash

    def has_position(self, ticker: str) -> bool:
        return ticker in self.positions and self.positions[ticker].qty > 0

    def short(self, ticker: str, qty: int, price: float) -> bool:
        # Short selling: we receive cash upfront, owe shares
        proceeds = qty * price
        self.cash += proceeds

        if ticker in self.short_positions:
            pos = self.short_positions[ticker]
            total_qty = pos.qty + qty
            pos.avg_price = ((pos.avg_price * pos.qty) + (price * qty)) / total_qty
            pos.qty = total_qty
        else:
            self.short_positions[ticker] = Position(ticker=ticker, qty=qty, avg_price=price)

        trade = {
            'action': 'SHORT',
            'ticker': ticker,
            'qty': qty,
            'price': price,
            'proceeds': proceeds,
            'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        }
        self.trade_log.append(trade)
        print(f"[paper] SHORT {qty} {ticker} @ ${price:.2f} (proceeds: ${proceeds:,.2f}, cash: ${self.cash:,.2f})")
        return True

    def cover(self, ticker: str, qty: int, price: float) -> bool:
        if ticker not in self.short_positions:
            print(f"[paper] No short position to cover for {ticker}")
            return False

        pos = self.short_positions[ticker]
        cover_qty = min(qty, pos.qty)
        entry_price = pos.avg_price
        cost = cover_qty * price
        # P&L on short: profit when price goes down
        pnl = (entry_price - price) * cover_qty

        self.cash -= cost
        pos.qty -= cover_qty

        if pos.qty == 0:
            del self.short_positions[ticker]

        trade = {
            'action': 'COVER',
            'ticker': ticker,
            'qty': cover_qty,
            'entry_price': entry_price,
            'price': price,
            'cost': cost,
            'pnl': pnl,
            'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        }
        self.trade_log.append(trade)
        pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
        print(f"[paper] COVER {cover_qty} {ticker} @ ${price:.2f} (P&L: {pnl_str}, cash: ${self.cash:,.2f})")
        return True

    def has_short_position(self, ticker: str) -> bool:
        return ticker in self.short_positions and self.short_positions[ticker].qty > 0

    def get_portfolio_value(self, prices: Dict[str, float]) -> float:
        long_value = sum(
            pos.market_value(prices.get(pos.ticker, pos.avg_price))
            for pos in self.positions.values()
        )
        # Short liability: we owe shares at current price
        short_liability = sum(
            pos.qty * prices.get(pos.ticker, pos.avg_price)
            for pos in self.short_positions.values()
        )
        # Short collateral already in cash, subtract current liability
        return self.cash + long_value - short_liability

    def print_summary(self, prices: Dict[str, float] = None):
        prices = prices or {}
        total = self.get_portfolio_value(prices)
        pnl = total - STARTING_CAPITAL
        pnl_pct = (pnl / STARTING_CAPITAL) * 100

        print(f"\n{'='*50}")
        print(f"  PAPER PORTFOLIO SUMMARY")
        print(f"{'='*50}")
        print(f"  Cash:       ${self.cash:,.2f}")

        if self.positions:
            print(f"  Long Positions:")
            for ticker, pos in self.positions.items():
                cur_price = prices.get(ticker, pos.avg_price)
                upnl = pos.unrealized_pnl(cur_price)
                upnl_str = f"+${upnl:,.2f}" if upnl >= 0 else f"-${abs(upnl):,.2f}"
                print(f"    {ticker}: {pos.qty} shares @ ${pos.avg_price:.2f} (now ${cur_price:.2f}, P&L: {upnl_str})")

        if self.short_positions:
            print(f"  Short Positions:")
            for ticker, pos in self.short_positions.items():
                cur_price = prices.get(ticker, pos.avg_price)
                # Short P&L is inverted: profit when price drops
                upnl = (pos.avg_price - cur_price) * pos.qty
                upnl_str = f"+${upnl:,.2f}" if upnl >= 0 else f"-${abs(upnl):,.2f}"
                print(f"    {ticker}: {pos.qty} shares @ ${pos.avg_price:.2f} (now ${cur_price:.2f}, P&L: {upnl_str})")

        pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
        print(f"  Total:      ${total:,.2f} ({pnl_str}, {pnl_pct:+.1f}%)")
        print(f"  Trades:     {len(self.trade_log)}")
        print(f"{'='*50}\n")


class TradeZeroBroker(Broker):
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.tz = None
        self._login()

    def _login(self):
        try:
            from tradezero_api import TradeZero
            self.tz = TradeZero(self.username, self.password)
            self.tz.login()
            print(f"[tradezero] Logged in as {self.username}")
        except Exception as e:
            print(f"[tradezero] Login failed: {e}")
            raise

    def _symbol(self, ticker: str) -> str:
        # Convert "NASDAQ:AAPL" to "AAPL"
        return ticker.split(':')[-1] if ':' in ticker else ticker

    def buy(self, ticker: str, qty: int, price: float) -> bool:
        try:
            from tradezero_api import Order
            symbol = self._symbol(ticker)
            self.tz.market_order(Order.BUY, symbol, qty)
            print(f"[tradezero] BUY {qty} {symbol} @ ~${price:.2f}")
            return True
        except Exception as e:
            print(f"[tradezero] BUY failed for {ticker}: {e}")
            return False

    def sell(self, ticker: str, qty: int, price: float) -> bool:
        try:
            from tradezero_api import Order
            symbol = self._symbol(ticker)
            self.tz.market_order(Order.SELL, symbol, qty)
            print(f"[tradezero] SELL {qty} {symbol} @ ~${price:.2f}")
            return True
        except Exception as e:
            print(f"[tradezero] SELL failed for {ticker}: {e}")
            return False

    def short(self, ticker: str, qty: int, price: float) -> bool:
        try:
            from tradezero_api import Order
            symbol = self._symbol(ticker)
            self.tz.market_order(Order.SHORT, symbol, qty)
            print(f"[tradezero] SHORT {qty} {symbol} @ ~${price:.2f}")
            return True
        except Exception as e:
            print(f"[tradezero] SHORT failed for {ticker}: {e}")
            return False

    def cover(self, ticker: str, qty: int, price: float) -> bool:
        try:
            from tradezero_api import Order
            symbol = self._symbol(ticker)
            self.tz.market_order(Order.BUY, symbol, qty)
            print(f"[tradezero] COVER {qty} {symbol} @ ~${price:.2f}")
            return True
        except Exception as e:
            print(f"[tradezero] COVER failed for {ticker}: {e}")
            return False

    def has_short_position(self, ticker: str) -> bool:
        # TradeZero doesn't expose short position check easily
        return False

    def get_positions(self) -> Dict[str, Position]:
        return {}

    def get_cash(self) -> float:
        return 0.0

    def has_position(self, ticker: str) -> bool:
        try:
            symbol = self._symbol(ticker)
            return self.tz.Portfolio.invested(symbol)
        except Exception:
            return False

    def get_portfolio_value(self, prices: Dict[str, float]) -> float:
        return 0.0

    def close(self):
        if self.tz:
            self.tz.exit()
            print("[tradezero] Session closed")
