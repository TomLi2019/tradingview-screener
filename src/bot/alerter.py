import json
import os

import requests

from bot.config import DISCORD_ALERTS_ENABLED, SMS_ALERTS_ENABLED, WHATSAPP_ALERTS_ENABLED
from bot.strategy import Signal

DISCORD_ALERT_WEBHOOK_URL = os.environ.get('DISCORD_ALERT_WEBHOOK_URL', '')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
RECIPIENT_PHONE_NUMBER = os.environ.get('RECIPIENT_PHONE_NUMBER', '')
WHATSAPP_RECIPIENT_NUMBER = os.environ.get('WHATSAPP_RECIPIENT_NUMBER', '')
CALLMEBOT_PHONE = os.environ.get('CALLMEBOT_PHONE', '')
CALLMEBOT_APIKEY = os.environ.get('CALLMEBOT_APIKEY', '')


def _format_signal(signal: Signal) -> str:
    action_emoji = {
        'buy': 'BUY',
        'strong_buy': 'STRONG BUY',
        'sell_ema_cross': 'EXIT (EMA Cross)',
        'sell_vwap_break': 'EXIT (VWAP Break)',
        'strong_sell': 'EXIT (EMA + VWAP)',
    }
    label = action_emoji.get(signal.action, signal.action.upper())
    lines = [
        f"[{label}] {signal.ticker} @ ${signal.price:.2f}",
        f"  EMA{signal.ema_short}/{signal.ema_long}: {signal.ema_short:.2f}/{signal.ema_long:.2f}",
        f"  EMA{200}: {signal.ema_trend:.2f}",
    ]
    if signal.vwap is not None:
        lines.append(f"  VWAP: {signal.vwap:.2f}")
    if signal.rsi is not None:
        lines.append(f"  RSI: {signal.rsi:.1f}")
    lines.append(f"  Time: {signal.timestamp}")
    return "\n".join(lines)


def send_discord_alert(signal: Signal):
    if not DISCORD_ALERT_WEBHOOK_URL:
        print("[alerter] Discord webhook URL not configured, skipping")
        return
    message = _format_signal(signal)
    payload = json.dumps({'content': message})
    response = requests.post(
        DISCORD_ALERT_WEBHOOK_URL,
        data=payload,
        headers={'Content-Type': 'application/json'},
    )
    if response.status_code == 204:
        print(f"[alerter] Discord alert sent: {signal.ticker} {signal.action}")
    else:
        print(f"[alerter] Discord alert failed ({response.status_code}): {signal.ticker}")


def send_sms_alert(signal: Signal):
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, RECIPIENT_PHONE_NUMBER]):
        print("[alerter] Twilio not configured, skipping SMS")
        return
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = _format_signal(signal)
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=RECIPIENT_PHONE_NUMBER,
        )
        print(f"[alerter] SMS sent: {signal.ticker} {signal.action}")
    except Exception as e:
        print(f"[alerter] SMS failed: {e}")


def _send_whatsapp_callmebot(text: str):
    """Send WhatsApp message via CallMeBot (free, no Twilio needed)."""
    if not all([CALLMEBOT_PHONE, CALLMEBOT_APIKEY]):
        print("[alerter] CallMeBot not configured, skipping WhatsApp")
        return False
    try:
        import urllib.parse
        encoded = urllib.parse.quote_plus(text)
        url = f"https://api.callmebot.com/whatsapp.php?phone={CALLMEBOT_PHONE}&text={encoded}&apikey={CALLMEBOT_APIKEY}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            print("[alerter] WhatsApp sent via CallMeBot")
            return True
        else:
            print(f"[alerter] WhatsApp CallMeBot failed ({resp.status_code}): {resp.text[:100]}")
            return False
    except Exception as e:
        print(f"[alerter] WhatsApp CallMeBot error: {e}")
        return False


def send_whatsapp_alert(signal: Signal):
    message = _format_signal(signal)
    if CALLMEBOT_PHONE and CALLMEBOT_APIKEY:
        _send_whatsapp_callmebot(message)
    elif all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, WHATSAPP_RECIPIENT_NUMBER]):
        try:
            from twilio.rest import Client
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=message,
                from_=f'whatsapp:{TWILIO_PHONE_NUMBER}',
                to=f'whatsapp:{WHATSAPP_RECIPIENT_NUMBER}',
            )
            print(f"[alerter] WhatsApp sent via Twilio: {signal.ticker} {signal.action}")
        except Exception as e:
            print(f"[alerter] WhatsApp Twilio failed: {e}")
    else:
        print("[alerter] WhatsApp not configured (set CALLMEBOT_PHONE+APIKEY or Twilio+WHATSAPP_RECIPIENT_NUMBER)")


def send_alert(signal: Signal):
    if DISCORD_ALERTS_ENABLED:
        send_discord_alert(signal)
    if SMS_ALERTS_ENABLED:
        send_sms_alert(signal)
    if WHATSAPP_ALERTS_ENABLED:
        send_whatsapp_alert(signal)


def send_portfolio_summary(broker, prices: dict):
    """Send portfolio summary to Discord every interval."""
    if not hasattr(broker, 'positions'):
        return

    from bot.config import STARTING_CAPITAL
    total = broker.get_portfolio_value(prices)
    pnl = total - STARTING_CAPITAL
    pnl_pct = (pnl / STARTING_CAPITAL) * 100
    pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"

    lines = [
        "📊 **PORTFOLIO SUMMARY**",
        f"Cash: ${broker.cash:,.2f}",
    ]

    if broker.positions:
        lines.append("**Long Positions:**")
        for ticker, pos in broker.positions.items():
            cur = prices.get(ticker, pos.avg_price)
            upnl = pos.unrealized_pnl(cur)
            upnl_s = f"+${upnl:,.2f}" if upnl >= 0 else f"-${abs(upnl):,.2f}"
            entry_time = pos.entry_time[11:19] if hasattr(pos, 'entry_time') else ''
            lines.append(f"  [{entry_time}] {ticker}: {pos.qty} @ ${pos.avg_price:.2f} → ${cur:.2f} ({upnl_s})")

    if broker.short_positions:
        lines.append("**Short Positions:**")
        for ticker, pos in broker.short_positions.items():
            cur = prices.get(ticker, pos.avg_price)
            upnl = (pos.avg_price - cur) * pos.qty
            upnl_s = f"+${upnl:,.2f}" if upnl >= 0 else f"-${abs(upnl):,.2f}"
            entry_time = pos.entry_time[11:19] if hasattr(pos, 'entry_time') else ''
            lines.append(f"  [{entry_time}] {ticker}: {pos.qty} @ ${pos.avg_price:.2f} → ${cur:.2f} ({upnl_s})")

    # List all trades from today
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    today_trades = [t for t in broker.trade_log if t['time'].startswith(today)]
    closed_trades = [t for t in today_trades if t['action'] in ('SELL', 'COVER')]
    if closed_trades:
        lines.append(f"**Closed Trades ({len(closed_trades)}):**")
        for t in closed_trades:
            action = t['action']
            ticker = t['ticker']
            qty = t['qty']
            price = t['price']
            entry = t.get('entry_price', price)
            pnl = t.get('pnl', 0)
            pnl_s = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
            time_str = t.get('time', '')[11:19]
            if action == 'SELL':
                lines.append(f"  [{time_str}] {ticker} {qty}sh | buy ${entry:.2f} → sell ${price:.2f} | P&L: {pnl_s}")
            elif action == 'COVER':
                lines.append(f"  [{time_str}] {ticker} {qty}sh | short ${entry:.2f} → cover ${price:.2f} | P&L: {pnl_s}")

    lines.append(f"**Total: ${total:,.2f} ({pnl_str}, {pnl_pct:+.1f}%)**")
    lines.append(f"Closed: {len(closed_trades)} today | Open trades: {len(today_trades) - len(closed_trades)}")

    message = "\n".join(lines)
    print(f"[alerter] Portfolio summary:\n{message}")

    if DISCORD_ALERTS_ENABLED and DISCORD_ALERT_WEBHOOK_URL:
        payload = json.dumps({'content': message})
        resp = requests.post(
            DISCORD_ALERT_WEBHOOK_URL,
            data=payload,
            headers={'Content-Type': 'application/json'},
        )
        if resp.status_code == 204:
            print("[alerter] Portfolio summary sent to Discord")
        else:
            print(f"[alerter] Portfolio summary Discord send failed ({resp.status_code})")

    if WHATSAPP_ALERTS_ENABLED:
        _send_whatsapp_callmebot(message)
