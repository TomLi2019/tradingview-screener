import json
import os
import time

import discord
import pandas as pd
import pytest
import schedule
from discord.ext import commands
from discord_webhook import send_message_to_webull_webhook
from dotenv import load_dotenv
from sms import Sms
from twilio.rest import Client
from Webull import Webull

load_dotenv('.env.local')

from tradingview_screener import Column, Scanner
from tradingview_screener.query import Query


@pytest.mark.parametrize(
    ['markets', 'expected_url'],
    [
        (['crypto'], 'https://scanner.tradingview.com/crypto/scan'),
        (['forex'], 'https://scanner.tradingview.com/forex/scan'),
        (['america'], 'https://scanner.tradingview.com/america/scan'),
        (['israel'], 'https://scanner.tradingview.com/israel/scan'),
        (['america', 'israel'], 'https://scanner.tradingview.com/global/scan'),
        (['crypto', 'israel'], 'https://scanner.tradingview.com/global/scan'),
    ],
)
def test_set_markets(markets: list[str], expected_url: str):
    q = Query().set_markets(*markets)

    assert q.url == expected_url
    assert q.query['markets'] == markets

def json_format(js: str):
    return json.dumps(js, indent=4)

def send_sms(msg):
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']

    # Create a Twilio client
    client = Client(account_sid, auth_token)

    twilio_number = os.environ['TWILIO_PHONE_NUMBER']

    recipient_number = os.environ['RECIPIENT_PHONE_NUMBER']

    # Message to be sent
    if msg.strip() == '':
        msg = 'Hello from Twilio!'

    # Send SMS
    message = client.messages.create(
        body=msg,
        from_=twilio_number,
        to=recipient_number
    )

    print(f"SMS sent with SID: {message.sid}")

# n_rows, df = Scanner.premarket_gainers.get_scanner_data()
# print(df.to_dict('records')[:10])

# n_rows, df = Scanner.premarket_gappers.get_scanner_data()
# print(df.to_dict('records')[:10])

# n_rows, df = Query().select('close', 'volume', 'EMA8', 'EMA20', 'type').where(Column('EMA8') < Column('EMA20')).get_scanner_data()
# print(df.to_dict('records')[:10])
# print("-------postmarket_gainers--------")
# n_rows, df = Scanner.postmarket_gainers.get_scanner_data()
# print(json_format(df.to_dict('records')[:10]))


# print("-------postmarket_most_active--------")
# n_rows, df = Scanner.postmarket_most_active.get_scanner_data()
# print(json_format(df.to_dict('records')[:10]))

# #-------------------------------------

# print("-------premarket_gainers--------")
# n_rows, df = Scanner.premarket_gainers.get_scanner_data()
# print(json_format(df.to_dict('records')[:10]))

# print("-------premarket_gappers--------")
# n_rows, df = Scanner.premarket_gappers.get_scanner_data()
# print(json_format(df.to_dict('records')[:10]))

# print("-------premarket_most_active--------")
# n_rows, df = Scanner.premarket_most_active.get_scanner_data()
# print(json_format(df.to_dict('records')[:10]))


# #-------------------------------------
# print("----------------------monitoring-------------------")
# q = Query().select('name', 'market', 'close', 'volume', 'VWAP', 'MACD.macd', 'EMA8', 'EMA25', 'EMA200',  'market_cap_basic', 'premarket_change', 'premarket_change_abs', 'premarket_volume', 'postmarket_change', 'postmarket_change_abs', 'postmarket_volume', 'high', 'low', '52 Week High', '52 Week Low')
# n_rows, df = q.set_tickers('NASDAQ:MULN', 'NASDAQ:SNTG', 'NASDAQ:ADTX', 'NASDAQ:SXTC', 'NASDAQ:FLJ', 'NASDAQ:NVFY', 'NASDAQ:CING', 'NASDAQ:POL', 'NASDAQ:CCCC', 'NYSE:CGA').get_scanner_data()
# print(json.dumps(df.to_dict('records')[:10], indent=4))

# q = Query().select('name', 'market', 'close', 'volume', 'VWAP', 'MACD.macd', 'EMA8', 'EMA25', 'EMA200',  'market_cap_basic', 'premarket_change', 'premarket_change_abs', 'premarket_volume', 'postmarket_change', 'postmarket_change_abs', 'postmarket_volume', 'high', 'low', '52 Week High', '52 Week Low')
# n_rows, df = q.set_tickers('NASDAQ:FWBI', 'NASDAQ:SASI', 'AMEX:POL', 'NASDAQ:DRCT', 'NASDAQ:LBPH', 'NASDAQ:VYGR', 'NASDAQ:SOS', 'NASDAQ:JFBR', 'AMEX:TZA','NYSE:AI','NASDAQ:DGHI', 'NASDAQ:DISH', 'NYSE:PNST', 'NASDAQ:SGN', 'NASDAQ:WULF', 'NASDAQ:ATXG', 'NASDAQ:NGM', 'NASDAQ:SDIG', 'NASDAQ:BTCM', 'NASDAQ:ARBK', 'NASDAQ:ANY').get_scanner_data()
# print(json.dumps(df.to_dict('records')[:10], indent=4))

# q = Query().select('name', 'market', 'close', 'volume', 'VWAP', 'MACD.macd', 'EMA8', 'EMA25', 'EMA200',  'market_cap_basic', 'premarket_change', 'premarket_change_abs', 'premarket_volume', 'postmarket_change', 'postmarket_change_abs', 'postmarket_volume', 'high', 'low', '52 Week High', '52 Week Low')
# n_rows, df = q.set_tickers('NASDAQ:FWBI').get_scanner_data()
# print(json.dumps(df.to_dict('records')[:10], indent=4))

# print("-------Webull--------")
# webull = Webull()
# webull.quote()

# # webull.closebrowser()



# q = Query().select('name', 'close', 'premarket_high','premarket_low', 'premarket_volume', 'pre_change|5', 'premarket_change', 'premarket_change_abs', 'postmarket_high', 'postmarket_low', 'postmarket_volume', 'postmarket_change', 'postmarket_change_abs', 'close|5', '24h_close_prev|5', 'volume','volume|5', 'VWAP', 'VWAP|5', 'RSI|5', 'EMA8|5', 'EMA25|5', 'EMA200|5', 'EMA8', 'EMA25', 'EMA200',  'high', 'low', 'market_cap_basic', 'total_shares_outstanding_fundamental', 'net_debt',  '52 Week High', '52 Week Low')
# n_rows, df = q.set_tickers('NASDAQ:HWH','NASDAQ:ACON','NASDAQ:CLRB', 'NASDAQ:SPEC', 'NASDAQ:VINC', 'NASDAQ:CYCC', 'NASDAQ:SWVL', 'NASDAQ:CLRB').get_scanner_data()
# stock = json.dumps(df.to_dict('records')[:10], indent=4)
# print(stock)

q = Query().select('name', 'close', 'premarket_high','premarket_low', 'premarket_volume', 'pre_change|5', 'premarket_change', 'premarket_change_abs', 'postmarket_high', 'postmarket_low', 'postmarket_volume', 'postmarket_change', 'postmarket_change_abs', 'close|5', '24h_close_prev|5', 'volume','volume|5', 'VWAP', 'VWAP|5', 'RSI|5', 'EMA8|5', 'EMA25|5', 'EMA200|5', 'EMA8', 'EMA25', 'EMA200',  'high', 'low', 'market_cap_basic', 'total_shares_outstanding_fundamental', 'net_debt',  '52 Week High', '52 Week Low')
n_rows, df = q.set_tickers('NASDAQ:NEXI').get_scanner_data()
stock = json.dumps(df.to_dict('records')[:10], indent=4)
print(stock)

# q = Query().select('name', 'close', 'volume', 'VWAP', 'MACD.macd', 'EMA8|5', 'EMA25|5', 'EMA200',  'high', 'low').where(Column('EMA8|5') < Column('EMA25|5'))
# n_rows, df = q.set_tickers('NASDAQ:DOGZ').get_scanner_data()
# quote = json.dumps(df.to_dict('records')[:10], indent=4)
# print('quote='+quote)
# if quote.strip() == '':
#     print("short --- " + quote)
#     send_sms("short --- " + quote)

def alert():
    q = Query().select('name', 'close', 'volume','volume|5', 'VWAP', 'VWAP|5', 'RSI|5', 'EMA8|5', 'EMA25|5', 'EMA200|5', 'EMA200',  'high', 'low').where(Column('EMA8|5') < Column('EMA25|5'))
    n_rows, df = q.set_tickers('NASDAQ:RUM').get_scanner_data()
    quote = json.dumps(df.to_dict('records')[:10], indent=4)
    print('quote='+quote)
    if quote.strip():
        print("short --- " + quote)
        # send_sms(("short --- " + quote)
        # send_message_to_webull_webhook("short --- " + quote)

# #Schedule the function to run every 5 minutes
# schedule.every(1).minutes.do(alert)

# # Run the scheduler continuously
# while True:
#     schedule.run_pending()
#     time.sleep(60)  # Sleep for 1 mins
# alert()