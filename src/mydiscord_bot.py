import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv('.env.local')

bot_token = os.environ['DISCORD_BOT_TOKEN']


# Define intents
intents = discord.Intents.default()
intents.messages = True  # Enable message content intent

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command(name='hello',msg)
async def hello(ctx):
    await ctx.send(msg)

# Start the bot
bot.run(bot_token)
