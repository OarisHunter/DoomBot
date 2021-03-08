# bot_v2.py
# Version 2 of DoomBot, Intended to implement youtube link streaming

import discord
import os
import random
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)


@bot.event
async def on_ready():
    try:
        # Is ready debug message
        print(f"DoomBot Ready:")

        # Grab current guild and print info
        for guild in bot.guilds:
              print(f"\t{bot.user.name} has connected to {guild.owner.name}'s |{guild.name}|")

        await change_message(0)  # Set presence as Watching

    except discord.DiscordException:
        print(f'on_ready event failed')


async def change_message(i):
    type_idle = discord.ActivityType.watching
    type_active = discord.ActivityType.playing

    activity_idle_list = ["the Carnage"]
    activity_active_list = ["your Rib Cage"]
    if i == 0:
        randNum = random.randrange(0, len(activity_idle_list))
        await bot.change_presence(activity=discord.Activity(type=type_idle, name=activity_idle_list[randNum]))
    elif i == 1:
        randNum = random.randrange(0, len(activity_active_list))
        await bot.change_presence(activity=discord.Activity(type=type_active, name=activity_active_list[randNum]))
    else:
        # Default to "Watching the Carnage" if invalid input
        await bot.change_presence(activity=discord.Activity(type=type_idle, name=activity_idle_list[0]))

bot.run(TOKEN)
