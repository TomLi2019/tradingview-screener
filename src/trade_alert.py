import json
import os
import time

import discord
import pandas as pd
import pytest
import schedule
from discord.ext import commands
from discord_webhook import send_message_to_alert_webhook
from dotenv import load_dotenv
from mdb import store_rows
from pymongo import MongoClient
from sms import Sms
from twilio.rest import Client
from util import get_current_time, is_current_time_between
from Webull import Webull

load_dotenv('.env.local')

from tradingview_screener import Column
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

def check_action(ema1, ema2):
    rating = 0.02
    if ema1.crosses_below(ema2) & (abs(ema1-ema2)/ema1 > rating) :
        return 'short/sell'
    elif ema1 < ema2 & (abs(ema1-ema2)/ema1 > rating) :
        return 'cover/buy'
    else:
        return ''

def check_postmarket_break(stockbreaks, tf):
    for stockbreak in stockbreaks:
        breaklist = stockbreak.split('|')
        stock = breaklist[0]
        action = breaklist[1]
        price = float(breaklist[2])
        q = ''
        if action == 'short/sell/break':
            q = Query().select('name', 'close|'+tf, 'premarket_high','premarket_low', 'premarket_volume', 'pre_change|'+tf, 'premarket_change', 'premarket_change_abs', 'postmarket_high', 'postmarket_low', 'postmarket_volume', 'postmarket_change', 'postmarket_change_abs', '24h_close_prev|'+tf, 'volume','volume|'+tf, 'VWAP', 'VWAP|'+tf, 'RSI|'+tf, 'EMA8|'+tf, 'EMA25|'+tf, 'EMA200|'+tf, 'EMA8', 'EMA25','EMA200',  'high', 'low', 'market_cap_basic', 'total_shares_outstanding_fundamental', 'net_debt',  '52 Week High', '52 Week Low').where(Column('postmarket_high') > price)
        else:
            q = Query().select('name', 'close|'+tf, 'premarket_high','premarket_low', 'premarket_volume', 'pre_change|'+tf, 'premarket_change', 'premarket_change_abs', 'postmarket_high', 'postmarket_low', 'postmarket_volume', 'postmarket_change', 'postmarket_change_abs', '24h_close_prev|'+tf, 'volume','volume|'+tf, 'VWAP', 'VWAP|'+tf, 'RSI|'+tf, 'EMA8|'+tf, 'EMA25|'+tf, 'EMA200|'+tf, 'EMA8', 'EMA25','EMA200',  'high', 'low', 'market_cap_basic', 'total_shares_outstanding_fundamental', 'net_debt',  '52 Week High', '52 Week Low').where(Column('postmarket_high') > price)
        n_rows, df = q.set_tickers(stock).get_scanner_data()
        if not df.empty:
            df['time'] = [get_current_time()]
            df['action'] = action
            df['break'] = breaklist[2]
            df['desc'] = stockbreak
            quote = json.dumps(df.to_dict('records')[:10], indent=5)
            print(quote)
            # send_sms(("short --- " + quote)
            send_message_to_alert_webhook(quote)
            store_rows(df.to_dict('records')[:10], 'trade_alert')

def check_premarket_break(stockbreaks, tf):
    for stockbreak in stockbreaks:
        breaklist = stockbreak.split('|')
        stock = breaklist[0]
        action = breaklist[1]
        price = float(breaklist[2])
        q = ''
        if action == 'short/sell/break':
            q = Query().select('name', 'close|'+tf, 'premarket_high','premarket_low', 'premarket_volume', 'pre_change|'+tf, 'premarket_change', 'premarket_change_abs', 'postmarket_high', 'postmarket_low', 'postmarket_volume', 'postmarket_change', 'postmarket_change_abs', '24h_close_prev|'+tf, 'volume','volume|'+tf, 'VWAP', 'VWAP|'+tf, 'RSI|'+tf, 'EMA8|'+tf, 'EMA25|'+tf, 'EMA200|'+tf, 'EMA8', 'EMA25','EMA200',  'high', 'low', 'market_cap_basic', 'total_shares_outstanding_fundamental', 'net_debt',  '52 Week High', '52 Week Low').where(Column('premarket_high') > price)
        else:
            q = Query().select('name', 'close|1d', 'close|'+tf, 'premarket_high','premarket_low', 'premarket_volume', 'pre_change|'+tf, 'premarket_change', 'premarket_change_abs', 'postmarket_high', 'postmarket_low', 'postmarket_volume', 'postmarket_change', 'postmarket_change_abs', '24h_close_prev|'+tf, 'volume','volume|'+tf, 'VWAP', 'VWAP|'+tf, 'RSI|'+tf, 'EMA8|'+tf, 'EMA25|'+tf, 'EMA200|'+tf, 'EMA8', 'EMA25','EMA200',  'high', 'low', 'market_cap_basic', 'total_shares_outstanding_fundamental', 'net_debt',  '52 Week High', '52 Week Low').where(Column('premarket_high') > price)
        n_rows, df = q.set_tickers(stock).get_scanner_data()
        if not df.empty:
            df['time'] = [get_current_time()]
            df['action'] = action
            df['break'] = breaklist[2]
            df['desc'] = stockbreak
            quote = json.dumps(df.to_dict('records')[:10], indent=5)
            print(quote)
            # send_sms(("short --- " + quote)
            send_message_to_alert_webhook(quote)
            store_rows(df.to_dict('records')[:10], 'trade_alert')

def check_break(stockbreaks, tf):
    for stockbreak in stockbreaks:
        breaklist = stockbreak.split('|')
        stock = breaklist[0]
        action = breaklist[1]
        price = float(breaklist[2])
        q = ''
        if action == 'short/sell/break':
            q = Query().select('name', 'close|'+tf, 'premarket_high','premarket_low', 'premarket_volume', 'pre_change|'+tf, 'premarket_change', 'premarket_change_abs', 'postmarket_high', 'postmarket_low', 'postmarket_volume', 'postmarket_change', 'postmarket_change_abs', '24h_close_prev|'+tf, 'volume','volume|'+tf, 'VWAP', 'VWAP|'+tf, 'RSI|'+tf, 'EMA8|'+tf, 'EMA25|'+tf, 'EMA200|'+tf, 'EMA8', 'EMA25', 'EMA200',  'high', 'low', 'market_cap_basic', 'total_shares_outstanding_fundamental', 'net_debt',  '52 Week High', '52 Week Low').where(Column('close|'+tf) > price)
        else:
            q = Query().select('name', 'close|'+tf, 'premarket_high','premarket_low', 'premarket_volume', 'pre_change|'+tf, 'premarket_change', 'premarket_change_abs', 'postmarket_high', 'postmarket_low', 'postmarket_volume', 'postmarket_change', 'postmarket_change_abs', '24h_close_prev|'+tf, 'volume','volume|'+tf, 'VWAP', 'VWAP|'+tf, 'RSI|'+tf, 'EMA8|'+tf, 'EMA25|'+tf, 'EMA200|'+tf, 'EMA8', 'EMA25', 'EMA200',  'high', 'low', 'market_cap_basic', 'total_shares_outstanding_fundamental', 'net_debt',  '52 Week High', '52 Week Low').where(Column('close|'+tf) > price)
        n_rows, df = q.set_tickers(stock).get_scanner_data()
        if not df.empty:
            df['time'] = [get_current_time()]
            df['action'] = action
            df['break'] = breaklist[2]
            df['desc'] = stockbreak
            quote = json.dumps(df.to_dict('records')[:10], indent=5)
            print(quote)
            # send_sms(("short --- " + quote)
            send_message_to_alert_webhook(quote)
            store_rows(df.to_dict('records')[:10], 'trade_alert')

def check_trend(stocks, tf):
    for stock in stocks:
        q = Query().select('name', 'close|'+tf, 'premarket_high','premarket_low', 'premarket_volume', 'pre_change|'+tf, 'premarket_change', 'premarket_change_abs', 'postmarket_high', 'postmarket_low', 'postmarket_volume', 'postmarket_change', 'postmarket_change_abs', '24h_close_prev|'+tf, 'volume','volume|'+tf, 'VWAP', 'VWAP|'+tf, 'RSI|'+tf, 'EMA8|'+tf, 'EMA25|'+tf, 'EMA8', 'EMA25', 'EMA200|'+tf, 'EMA200',  'high', 'low', 'market_cap_basic', 'total_shares_outstanding_fundamental', 'net_debt',  '52 Week High', '52 Week Low').where(Column('EMA8|'+tf) < Column('EMA25|'+tf), Column('close|'+tf) < Column('VWAP|'+tf))
        n_rows, df = q.set_tickers(stock).get_scanner_data()
        if not df.empty:
            df['time'] = [get_current_time()]
            df['action'] = 'short/sell'
            quote = json.dumps(df.to_dict('records')[:10], indent=4)
            print(quote)
            # send_sms(("short --- " + quote)
            # send_message_to_alert_webhook(quote)
            # store_rows(df.to_dict('records')[:10], 'trade_alert')
        q = Query().select('name', 'close|'+tf, 'premarket_high','premarket_low', 'premarket_volume', 'pre_change|'+tf, 'premarket_change', 'premarket_change_abs', 'postmarket_high', 'postmarket_low', 'postmarket_volume', 'postmarket_change', 'postmarket_change_abs', '24h_close_prev|'+tf, 'volume','volume|'+tf, 'VWAP', 'VWAP|'+tf, 'RSI|'+tf, 'EMA8|'+tf, 'EMA25|'+tf, 'EMA200|'+tf, 'EMA8', 'EMA25', 'EMA200',  'high', 'low', 'market_cap_basic', 'total_shares_outstanding_fundamental', 'net_debt',  '52 Week High', '52 Week Low').where(Column('EMA8|'+tf) > Column('EMA25|'+tf), Column('close|'+tf) > Column('VWAP|'+tf))
        n_rows, df = q.set_tickers(stock).get_scanner_data()
        if not df.empty:
            df['time'] = [get_current_time()]
            df['action'] = 'cover/buy'
            quote = json.dumps(df.to_dict('records')[:10], indent=4)
            print(quote)
            # send_sms(("short --- " + quote)
            # send_message_to_alert_webhook(quote)
            # store_rows(df.to_dict('records')[:10], 'trade_alert')

def read_custom_formatted_records(
    uri=os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/'),
    db_name=os.environ.get('MONGODB_DATABASE', 'next-amazona'),
    collection_name="items",
    field1="exchange",
    field2="stock",
    field3="break",
    middle_fields=["rsdate", "rsratio", "aoutstanding", "desc"]
):
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]

    query = {
        field3: {"$exists": True, "$ne": ""}
    }

    records = list(collection.find(query))
    result = []
    for doc in records:
        first_part = f"{doc.get(field1, '')}:{doc.get(field2, '')}"
        middle_part = "-".join(str(doc.get(f, '')) for f in middle_fields)
        formatted = f"{first_part}|buy|{doc.get(field3, '')}|{middle_part}"
        result.append(formatted)

    client.close()
    return result


def alert():
    stocks = ['NASDAQ:MCU','NASDAQ:AERT','NASDAQ:AERT','NASDAQ:AERT','NASDAQ:AERT','NASDAQ:AERT','NASDAQ:AUVI','NASDAQ:MDAI','NASDAQ:TGAN','NASDAQ:ROMA','NASDAQ:SWVL','NASDAQ:BNZA','NASDAQ:SPEC','NASDAQ:MLEC','NASDAQ:ZKH','NASDAQ:CCCC','NASDAQ:LAES','NASDAQ:ICCT','NASDAQ:TCTM','NASDAQ:MCAF','NASDAQ:SNTG','NASDAQ:NKTX','NASDAQ:PRAX','NASDAQ:ELEV','NASDAQ:QSG', 'NASDAQ:ADXN', 'NASDAQ:ACON', 'NASDAQ:CLRB', 'NASDAQ:SPEC', 'NASDAQ:VINC', 'NASDAQ:CYCC', 'NASDAQ:LBPH', 'AMEX:POL', 'AMEX:TZA']
    stockbreaks = ['NASDAQ:BSLK|buy|3']
    check_break(stockbreaks, '5')
    # print(read_custom_formatted_records())
    # check_trend(stocks, '5')
    # check_trend(stocks, '30')
    # check_break(read_custom_formatted_records(), '5')
    # check_premarket_break(read_custom_formatted_records(), '5')
    if is_current_time_between(4, 9):
        check_premarket_break(read_custom_formatted_records(), '5')
    elif is_current_time_between(16, 20):
        check_postmarket_break(read_custom_formatted_records(), '5')
    else:
        check_break(read_custom_formatted_records(), '5')

# #Schedule the function to run every 5 minutes
# schedule.every(5).minutes.do(alert)

# # Run the scheduler continuously
# while True:
#     schedule.run_pending()
#     time.sleep(300)  # Sleep for 5 mins


alert()