import os

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv('.env.local')


class Sms():

  def send_sms(msg):
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']

    # Create a Twilio client
    client = Client(account_sid, auth_token)

    twilio_number = os.environ.get('TWILIO_PHONE_NUMBER', 'your_twilio_number')

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

