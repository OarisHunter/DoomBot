# bot.py
import asyncio
import os
import discord
import glob
import random
import youtube_dl

from discord.ext import commands
from dotenv import load_dotenv
from configparser import ConfigParser


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

config_object = ConfigParser()
config_object.read("config.ini")

bot_settings = config_object["BOT_SETTINGS"]

libraryPath = bot_settings["libraryPath"]
recent_songs_cap = int(bot_settings["recent_songs_cap"])

songs = []
current_song = 0
recent_songs = []


@bot.event
async def on_ready():
    try:
        # Is ready debug message
        print(f"DoomBot Ready:")

        # Grab current guild and print info
        for guild in bot.guilds:
            print(f"\t{bot.user.name} has connected to {guild.owner.name}'s |{guild.name}|")

        # Populate Library on Start
        refresh_lib()
        print(f'------- {len(songs)} Songs Loaded -------')

        await change_message(0)  # Set presence as Watching

    except discord.DiscordException:
        print(f'on_ready event failed')


# ------------------- Commands ---------------------- #


@bot.command(name='play', help="connects bot to voice and infinitely plays shuffled song library")
async def play_(ctx):
    if ctx.author.voice is not None:
        try:
            vc = await ctx.author.voice.channel.connect()
            print(f"Play: Voice Client Connected to {ctx.guild.name}")
        except:
            vc = ctx.guild.voice_client
            print(f"Play: Voice Client Fetched from {ctx.guild.name}")
    else:
        print(f"Play: Message Author not Connected to Voice in {ctx.guild.name}")
        await ctx.message.delete()
        return await ctx.channel.send("Not in a Voice Channel", delete_after=10)

    # Display message in chat and delete command
    await ctx.message.delete()
    await ctx.channel.send("**Rip and Tear**, until it is **Done**", delete_after=20)

    # Start Music Loop
    await play_music_(ctx, vc)


@bot.command(name='skip', help="skips current song")
async def skip_music_(ctx):
    vc = ctx.guild.voice_client         # Get current voice client
    if vc is None:
        print(f"Skip: Bot not connected to {ctx.guild.name}, running 'play' command")
        return await ctx.invoke(bot.get_command('play'))    # Execute play command if not connected to voice

    # Generate new song index
    global current_song
    current_song = gen_rand_song_index()

    # Change Song Source
    vc.source = discord.FFmpegPCMAudio(songs[current_song])

    # Display song name
    print(f"Skip: Skipping Song in {ctx.guild.name}")
    await ctx.invoke(bot.get_command('np'))


@bot.command(name='disconnect', help="disconnect bot from voice channel")
async def disconnect_(ctx):
    vc = ctx.guild.voice_client

    # Check if voice client is connected
    if vc.is_connected():
        print(f"\tDisconnect: Disconnecting from {ctx.guild.name}")
        await vc.disconnect()
        vc = None

    await ctx.message.delete(delay=5)
    await change_message(0)  # Set presence as Watching


@bot.command(name='refresh', help="Refreshes song list from library")
async def refresh_lib_(ctx):
    refresh_lib()

    print(f"Library Refresh: {len(songs)} Songs Loaded.")
    await ctx.channel.send(f"**Library Refresh:** {len(songs)} Songs Loaded.", delete_after=5)
    await ctx.message.delete(delay=5)


@bot.command(name='playsong', help="Plays a specific song")
async def play_song_(ctx, name: str):
    # Try to get current
    vc = ctx.guild.voice_client
    if vc is None:
        print(f"PlaySong: Bot not connected in {ctx.guild.name}")
        await ctx.channel.send(f'Not in a Voice Channel', delete_after=5)
        return await ctx.message.delete(delay=5)

    flag = 0
    for song_index in range(len(songs)):
        if songs[song_index].find(name) != -1:
            global current_song
            current_song = song_index
            flag = 1
            break

    if vc.is_connected() and flag == 1:
        # Change Song Source
        print("PlaySong: Found Song")
        vc.source = discord.FFmpegPCMAudio(songs[current_song])
        await ctx.invoke(bot.get_command('np'))
    else:
        print("PlaySong: Couldn't find Song")
        await ctx.channel.send(f'Song Title not Found', delete_after=5)
        return await ctx.message.delete(delay=5)


@bot.command(name='np', help="Displays current song name")
async def now_playing_(ctx):
    if ctx.message.guild.voice_client:
        song_split = songs[current_song].split('\\')
        song = song_split[len(song_split) - 1]

        print(f'NowPlaying: {song[:len(song)-4]} in {ctx.guild.name}')
        await ctx.channel.send(f'**Now Playing**\n\n`{song[:len(song)-4]}`', delete_after=5)
        await ctx.message.delete(delay=5)
    else:
        print(f'NowPlaying: Not in a Voice Channel in {ctx.guild.name}')
        await ctx.channel.send(f'Not in a Voice Channel', delete_after=5)
        await ctx.message.delete(delay=5)


@bot.command(name='upload', help="Saves attached mp3 file to song library and refreshes")
async def upload_(ctx):
    # Check if author is the owner
    if ctx.author == ctx.guild.owner:

        for attachment in ctx.message.attachments:
            print(f'Downloading File: {attachment.filename} to {libraryPath}')
            await attachment.save(fp=libraryPath + "\\" + attachment.filename)

        await ctx.invoke(bot.get_command('refresh'))

    else:
        await ctx.channel.send(f'Only Server Owner can upload songs to song library', delete_after=5)
        await ctx.message.delete(delay=5)


@bot.command(name='download', help="Downloads a song from youtube and adds it to the library, refresh required")
async def download_(ctx, name: str, url: str):
    ytdlopts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': libraryPath + f'\{name}.mp3'
    }

    # Check if author is the owner
    if ctx.author == ctx.guild.owner:

        with youtube_dl.YoutubeDL(ytdlopts) as ydtl:
            ydtl.cache.remove()
            info_dict = ydtl.extract_info(url, download=False)
            ydtl.prepare_filename(info_dict)
            ydtl.download([url])

        await ctx.channel.send(f'{name} added to library', delete_after=5)

        await ctx.invoke(bot.get_command('refresh'))
    else:
        await ctx.channel.send(f'Only Server Owner can download songs to song library', delete_after=5)
        await ctx.message.delete(delay=5)


# ------------------------- Functions -------------------- #


async def play_music_(ctx, vc):  # vc = voice_client
    global current_song  # Get current song index
    # Infinite Music Loop
    while vc.is_connected():
        # Generate new song
        current_song = gen_rand_song_index()

        # Play song at random index of song list
        try:
            if vc.is_connected() and not vc.is_playing():
                # Create FFmpeg audio stream, attach to voice client
                vc.play(discord.FFmpegPCMAudio(songs[current_song]))
        except discord.errors.ClientException:
            print(f"ClientException: Failed to Play Song {songs[current_song]} in {ctx.guild.name}")
            break

        if not vc.is_playing():
            print(f"Failed to Play Song {songs[current_song]} in {ctx.guild.name}")
            break

        await change_message(1)  # Set presence as Playing

        await ctx.invoke(bot.get_command('np'))
        # Prevent next song from playing till previous one ends
        while vc.is_playing():
            await asyncio.sleep(1)


def refresh_lib():
    global songs
    songs = glob.glob(libraryPath + r"\*.mp3")


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


def gen_rand_song_index():

    global recent_songs

    recent_songs.append(current_song)
    if len(recent_songs) >= recent_songs_cap:
        recent_songs.pop(0)

    randNum = random.randrange(0, len(songs))
    # while randNum == current_song:                # Protects against last played song
    while randNum in recent_songs:                  # Protects against last 'x' played song
        randNum = random.randrange(0, len(songs))
    return randNum


bot.run(TOKEN)
