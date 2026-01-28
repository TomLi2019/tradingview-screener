import json
import os
import time
from datetime import datetime

import discord
import pandas as pd
import pymongo
import pytest
import schedule
from discord.ext import commands
from discord_webhook import send_message_to_webull_webhook
from dotenv import load_dotenv
from pymongo import MongoClient  # Database connector
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


def store_mdb(json_data):
    connection_string = os.environ['MONGODB_CONNECTION_STRING']
    client = pymongo.MongoClient(connection_string)

    db = client[os.environ.get('MONGODB_DATABASE', 'next-amazona')]
    collection = db['webull_scan']

    # mongodb_host = os.environ.get('MONGO_HOST', 'localhost')
    # mongodb_port = int(os.environ.get('MONGO_PORT', '27017'))
    # # Configure the connection to the database
    # client = MongoClient(mongodb_host, mongodb_port)
    # # db = client.next-amazona  # Select the database
    # db = client["next-amazona"]
    # collection = db.webull_scan  # Select the collection

    # Insert the JSON data into the MongoDB collection
    result = collection.insert_many(json_data)

def scan():
    print("-------Webull--------")
    webull = Webull()
    quote = webull.quote()
    current_time = get_current_time()
    if quote.strip():
        # Split the input string into lines
        lines_org = quote.split('\\n')
        lines = [item for item in lines_org if not (item.isalpha() and len(item) == 1 and 'A' <= item.upper() <= 'Z')]
        print(lines)
        # Create a list to store the data entries
        data_entries = []

        # Iterate over lines in groups of 4 to create data entries
        for i in range(0, len(lines), 5):
                rank = lines[i].replace('"', '')
                name = lines[i + 1].replace('"', '')
                symbol = lines[i + 2].replace('"', '')
                percentage_change = lines[i + 3].replace('"', '')
                value = lines[i + 4].replace('"', '')

                # Create a dictionary for each entry
                entry = {
                        "time": current_time,
                        "rank": rank,
                        "name": name,
                        "symbol": symbol,
                        "percentage_change": percentage_change,
                        "close": value
                }

                # Append the entry to the list
                data_entries.append(entry)
                last_group = lines[-(len(lines) % 5):]

        # Convert the list of dictionaries to a JSON string
        json_string = json.dumps(data_entries, indent=2)

        # Print the JSON string
        print(json_string)
        print('json_string='+json_string)
        store_mdb(data_entries)
        send_message_to_webull_webhook("Webull Scan - " +  current_time + "\n" + json_string)
    webull.closebrowser()

    # q = Query().select('name', 'close', 'volume','volume|5', 'VWAP', 'VWAP|5', 'RSI|5', 'EMA8|5', 'EMA25|5', 'EMA200|5', 'EMA200',  'high', 'low').where(Column('EMA8|5') < Column('EMA25|5'))
    # n_rows, df = q.set_tickers('NASDAQ:DOGZ').get_scanner_data()
    # quote = json.dumps(df.to_dict('records')[:10], indent=4)
    # print('quote='+quote)
    # if quote.strip():
    #     print("short --- " + quote)
    #     # send_sms(("short --- " + quote)


#Schedule the function to run every 10 minutes
# schedule.every(10).minutes.do(scan)

# # Run the scheduler continuously
# while True:
#     # Check if the current time is between 4am and 8pm
#     if is_current_time_between(4, 20):
#         schedule.run_pending()
#         time.sleep(600)  # Sleep for 10 mins

# Check if the current time is between 4am and 8pm
# if is_current_time_between(4, 20):
#     scan()

scan()