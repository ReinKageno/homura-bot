
import os
import asyncio
import discord
import time
import re
import yt_dlp
from bson.objectid import ObjectId
from discord.ext import commands
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs 
from pyauxy import hprint
from services.homura import database

load_dotenv()
git_avatar = os.getenv('GIT_AVA')

QUEUE_YDL = yt_dlp.YoutubeDL({
    'format': 'bestaudio',
    'extract_flat': True,
    'quiet': True,
    'noplaylist': True,
    'js_runtimes': {
        'deno': {
            'path':'../tools/deno/deno'
        }
    }
})

PLAY_YDL = yt_dlp.YoutubeDL({
    'format': 'bestaudio',
    'quiet': True,
    'noplaylist': True,
    'js_runtimes': {
        'deno': {
            'path':'../tools/deno/deno'
        }
    }
})

player_locks = {}

URL_RE = re.compile(r"^https?://", re.IGNORECASE)

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}

def get_lock(guild_id):
    if guild_id not in player_locks:
        player_locks[guild_id] = asyncio.Lock()

    return player_locks[guild_id]

async def music_player(ctx:commands.Context, search):
        guild_id = ctx.guild.id
        voice_channel = ctx.author.voice.channel
        
        if not ctx.author.voice:
            await ctx.send(f'Please use when you inside a voice channel.')
            return
        
        music_db = database.musicQueue_db[str(guild_id)]
        empty_queue = True

        if ctx.voice_client is None:
            music_db.delete_many({})

            vc = await voice_channel.connect()
        else:
            vc = ctx.voice_client

            if vc is None or not vc.is_connected():
                vc = await voice_channel.connect()

        # Queue checker, currently not used
        if music_db.count_documents({}) != 0:
            empty_queue = False

        # Gatekeeper
        if is_url(search):
            query = clean_youtube_url(search)
        else:
            hprint(f"Searching for {search}'s audio", id=guild_id)
            query = f'ytsearch:{search}'

        # Youtube finder
        info = await asyncio.to_thread(
            QUEUE_YDL.extract_info,
            query,
            download=False
        )

        if 'entries' in info:
            info = next(iter(info['entries']), None)

        if info is None:
            await ctx.send('No results found.')
            return

        # URL filtering
        try:
            url =  info['original_url']
        except Exception:
            try:
                url = info['webpage_url']
            except Exception:
                url = info['url']

        music_db.insert_one({
            'title': info["title"],
            'artist': info["channel"],
            'webpage_url': url,
            'requester': ctx.author.id,
            'created_at': int(time.time())
        })

        # Media player
        if not vc.is_playing() or vc.is_paused():
            await play_next(ctx)
        if not empty_queue:
            await ctx.send(f'Queue: {info["title"]} by {info["channel"]} successfully added.')

async def play_next(ctx:commands.Context):

    # Lock the media player and wait until end

    guild_id = ctx.guild.id
    lock = get_lock(guild_id)
    hprint('Attempting to play the audio', id=guild_id)

    async with lock:
        channel = ctx.voice_client

        if channel is None:
            return

        if not channel.is_connected():
            return

        if channel.is_playing() or channel.is_paused():
            return
        
        hprint('Preparing the audio', id=guild_id)
        music_db = database.musicQueue_db[str(guild_id)]
        loop = asyncio.get_running_loop()

        if ctx.voice_client is None:
            await ctx.send("I'm not in a voice channel. Can't play the audio.")
            return
        else:
            channel = ctx.voice_client

        song = music_db.find_one({}, sort=[('created_at', 1)])

        if not song:
            await ctx.send('Music stopped, queue is empty.')
            hprint('No audio found', id=guild_id)
            return

        hprint(f'Attempting to streaming {song['webpage_url']}', id=guild_id)

        info = await asyncio.to_thread(
            PLAY_YDL.extract_info,
            song['webpage_url'],
            download=False
        )

        stream_url = info['url']

        source = discord.FFmpegPCMAudio(
            stream_url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-ar 48000 -ac 2 -af "aresample=async=1"'
        )

        def after(error):
            if error:
                print(error)

            music_db.delete_one({"_id": song["_id"]})

            asyncio.run_coroutine_threadsafe(
                play_next(ctx),
                loop
            )

        await ctx.send(f'Playing {song['title']} by {song['artist']}')
        channel.play(source, after=after)

async def clear_queue(ctx:commands.Context, skip=1, clear=False):
    music_db = database.musicQueue_db[str(ctx.guild.id)]

    if isinstance(skip, str):
        skip = int(skip)

    # Clear the whole queue
    if clear and ctx.voice_client:
        await clear_whole_queue(ctx)
        return

    if skip > 1:
        rm_queue = list(
            music_db.find({}, sort=[("created_at", 1)], limit=skip)
        )

        music_db.delete_many({
            "_id": {
                "$in": [doc["_id"] for doc in rm_queue]
            }
        })

    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send(f'Skipping {skip} song.')

async def remove_queue(ctx:commands.Context, query):
    music_db = database.musicQueue_db[str(ctx.guild.id)]

    isnum = bool(re.fullmatch(r'\d+', query))

    if isnum:
        query = int(query)

        if query == 0:
            await ctx.send(
                'Queue is not changed, nothing to remove.\n'+
                'Try `!skipm` if you want to skip current audio.'
            )
            return

        db_cursor = music_db.find(
            {},
            sort=[('created_at', 1)],
            skip=query,
            limit=1,
        )

        db_doc = next(db_cursor, None)

        if db_doc is None:
            await ctx.send("That queue position doesn't exit.")
            return

        music_db.delete_one({'_id': db_doc['_id']})
        await ctx.send(f"Queue: [{query}] {db_doc['title']} has been removed.")
        return
    
    arg = " ".join(query)

    if  arg.startswith(("http://", "https://")):
        music_db.delete_one({'webpage_url': arg})
    else:
        song = music_db.find_one({
            'title': {
                '$regex': query,
                '$options': 'i'
            }
        })

    if song:
        music_db.delete_one({'_id': song['_id']})
        await ctx.send(f"Queue: {song['title']} successfully removed.")
    else:
        await ctx.send(f"I can't find {query} in queue. Remove something doesn't exist is not possible.")
        return

async def clear_whole_queue(ctx:commands.Context):
    audio_db = database.musicQueue_db[str(ctx.guild.id)]

    entity = audio_db.find_one({}, sort=[('created_at', 1)])

    audio_db.delete_many({'_id': {'$ne': ObjectId(entity['_id'])}})
    await ctx.send('The queue successfully cleared.')

async def show_queue(bot, ctx:commands.Context):
    music_db = database.musicQueue_db[str(ctx.guild.id)]
    text = []

    music_list = list(
        music_db.find(
            {},
            {
                'title': 1,
                'artist': 1,
                'requester': 1,
                '_id': 0
            }
        ).sort('created_at', 1)
    )

    if not music_list:
        await ctx.send('The queue is empty, try `!playm` to start.\n')
        return

    text.extend([
        '**Now Playing** \n──────────\n',
        f'**{music_list[0]['title']} by {music_list[0]['artist']}**\n',
        f'-# -requested by {await bot.fetch_user(music_list[0]['requester'])}\n'
    ])

    music_list.pop(0)
    if music_list:
        text.append('\n **Queue**\n──────\n')

    i = 0

    for music in music_list:
        i += 1
        text.extend([
            f'**[{i}] {music['title']} by {music['artist']}**\n',
            f'-# -requested by {await bot.fetch_user(music['requester'])}\n\n'
        ])

    msg = "".join(text)

    embed = discord.Embed(
        title='Homura - Media Player',
        description=msg,
        color=0x4b37e6,
    )

    embed.set_footer(
        text='by KanadeRein',
        icon_url=f"https://avatars.githubusercontent.com/u/{git_avatar}"
    )

    await ctx.send(embed=embed)

async def music_stop(ctx:commands.Context):
    music_db = database.musicQueue_db[str(ctx.guild.id)]

    music_db.delete_many({})

    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send('Disconnected.')
    else:
        await ctx.send("I'm not in a voice channel.")

def is_url(text: str)-> bool:
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def clean_youtube_url(url: str):
    parsed = urlparse(url)

    if parsed.netloc.lower() in YOUTUBE_HOSTS:
        query = parse_qs(parsed.query)

        if 'v' in query:
            return f"https://www.youtube.com/watch?v={query['v'][0]}"

    return url