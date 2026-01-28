
import os

import pymongo
from dotenv import load_dotenv
from pymongo import MongoClient  # Database connector

load_dotenv('.env.local')


def store_rows(json_data, collection):
    connection_string = os.environ['MONGODB_CONNECTION_STRING']
    client = pymongo.MongoClient(connection_string)

    db = client[os.environ.get('MONGODB_DATABASE', 'next-amazona')]
    collection = db[collection]

    # mongodb_host = os.environ.get('MONGO_HOST', 'localhost')
    # mongodb_port = int(os.environ.get('MONGO_PORT', '27017'))
    # # Configure the connection to the database
    # client = MongoClient(mongodb_host, mongodb_port)
    # # db = client.next-amazona  # Select the database
    # db = client["next-amazona"]
    # collection = db.webull_scan  # Select the collection

    # Insert the JSON data into the MongoDB collection
    result = collection.insert_many(json_data)

def store_row(json_data):
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
    result = collection.insert_one(json_data)