import json
import os

import requests
from dotenv import load_dotenv

load_dotenv('.env.local')

webull_webhook_url = os.environ['DISCORD_WEBULL_WEBHOOK_URL']
alert_webhook_url = os.environ['DISCORD_ALERT_WEBHOOK_URL']

def send_message_to_webull_webhook(message_content):
    # Create a payload with the message content
    payload = {
        'content': message_content
    }

    # Convert the payload to JSON
    json_payload = json.dumps(payload)

    # Send a POST request to the webhook URL
    response = requests.post(webull_webhook_url, data=json_payload, headers={'Content-Type': 'application/json'})

    # Check the response status
    if response.status_code == 204:
        print(f"Message sent successfully: '{message_content}'")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")

def send_message_to_alert_webhook(message_content):
    # Create a payload with the message content
    payload = {
        'content': message_content
    }

    # Convert the payload to JSON
    json_payload = json.dumps(payload)

    # Send a POST request to the webhook URL
    response = requests.post(alert_webhook_url, data=json_payload, headers={'Content-Type': 'application/json'})

    # Check the response status
    if response.status_code == 204:
        print(f"Message sent successfully: '{message_content}'")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")

# Example: Send a message to the webhook
# send_message_to_webhook("Hello, Discord!")

