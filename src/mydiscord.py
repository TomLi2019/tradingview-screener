import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv('.env.local')

bot_token = os.environ['DISCORD_BOT_TOKEN']

intents = discord.Intents.default()
intents.messages = True  # Enable message events

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


async def send_discord_message(message_content):
    # Replace 'YOUR_CHANNEL_ID' with the ID of the channel where you want to send the message
    channel_id = os.environ['DISCORD_CHANNEL_ID']

    # Get the channel using fjdthe channel ID
    channel = bot.get_channel(int(channel_id))

    if channel:
        # Send the message to the specified channel
        await channel.send(message_content)
        print(f"Message sent: '{message_content}'")
    else:
        print("Channel not found.")



# Start the bot
bot.run(bot_token)
