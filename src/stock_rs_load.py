import json
import os
import time
from datetime import datetime

import discord
import pandas as pd
import pymongo
import pytest
from Benzinga import Benzinga
from discord.ext import commands
from discord_webhook import send_message_to_webull_webhook
from dotenv import load_dotenv
from pymongo import MongoClient  # Database connector
from util import get_current_time, is_current_time_between

load_dotenv('.env.local')


def json_format(js: str):
    return json.dumps(js, indent=4)


def store_mdb(json_data):
    connection_string = os.environ['MONGODB_CONNECTION_STRING']
    client = pymongo.MongoClient(connection_string)

    db = client[os.environ.get('MONGODB_DATABASE', 'next-amazona')]
    collection = db['items']

    result = collection.insert_many(json_data)


def store_rows_to_mongodb(parsed, db_name=os.environ.get('MONGODB_DATABASE', 'next-amazona'), collection_name='rsplit', uri=os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')):
    # Connect to MongoDB
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]

    # Clear existing records (optional)
    collection.delete_many({})


    # Insert into MongoDB
    if parsed:
        result = collection.insert_many(parsed)
        print(f"✅ Inserted {len(result.inserted_ids)} documents into {db_name}.{collection_name}")
    else:
        print("⚠️ No valid records to insert.")

    client.close()


def insert_unique_stocks(records, db_name=os.environ.get('MONGODB_DATABASE', 'next-amazona'), collection_name='items', uri=os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')):
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]

    inserted_count = 0

    for record in records:
        stock = record.get("stock")
        if not stock:
            continue  # skip if missing stock symbol

        # Check if stock already exists
        if collection.find_one({"stock": stock}):
            print(f"⏩ Skipped existing stock: {stock}")
        else:
            collection.insert_one(record)
            print(f"✅ Inserted: {stock}")
            inserted_count += 1

    client.close()
    print(f"\nTotal new records inserted: {inserted_count}")

def transform_to_custom(record):
    return {
        "stock": record.get("Ticker", "").strip(),
        "rsratio": record.get("Split Ratio", "").strip(),
        "rsdate": record.get("Ex-Date", "").strip(),
        "exchange": record.get("Exchange", "").strip(),
        "befprice": "",           # placeholder
        "aftprice": "",           # placeholder
        "break": "",            # custom fixed value
        "boutstanding": "",       # placeholder
        "aoutstanding": "2M",     # custom value
        "desc": ""  # custom value
    }

def is_rs_split(ratio_str):
    try:
        before, after = map(float, ratio_str.strip().split(":"))
        return after > before
    except Exception as e:
        print(f"⚠️ Invalid ratio format: {ratio_str} ({e})")
        return False

def load():
    print("-------benzinga--------")
    benzinga = Benzinga()
    quote = benzinga.quote()
    current_time = get_current_time()
    print("benzinga_rs_quote="+quote)
 # Step 1: Convert \\n to actual newlines
    quote = bytes(quote, "utf-8").decode("unicode_escape")

    # Step 2: Split lines
    lines = quote.strip().split("\n")

    # Step 3: Headers
    headers = lines[:9]
    headers = [h.strip().strip('"') for h in headers]

    data = lines[9:]

    # Step 4: Group into rows of 9
    rows = [data[i:i + 9] for i in range(0, len(data), 9)]

    # Print headers
    print("Headers:")
    print(" | ".join(headers))

    print("\nRows:")
    # Print each row
    for row in rows:
        if len(row) == 9:
            print(" | ".join(row))
        else:
            print(f"[!] Skipped incomplete row: {row}")

    # Group rows into chunks of 9 fields each
   # rows is already grouped into lists of 9 elements
    parsed = []
    for record in rows:
        if len(record) == 9:
            entry = dict(zip(headers, record))
            parsed.append(entry)

    print("Headers:", headers)
    print("Keys of first entry:", parsed[0].keys())

    # Now print
    newParsed=[]
    for row in parsed:
        if row.get("Exchange") in {"NASDAQ", "AMEX", "NYSE"} and is_rs_split(row.get("Split Ratio")):
            newParsed.append(transform_to_custom(row))
        # print(row["Ex-Date"], row["Ticker"], row["Split Ratio"])

    filtered_transformed = [
        transform_to_custom(r)
        for r in parsed
        if r.get("Exchange") in {"NASDAQ", "AMEX", "NYSE"}
    ]

    # print(newParsed)
    # store_rows_to_mongodb(newParsed)
    insert_unique_stocks(newParsed)

    benzinga.closebrowser()



load()

